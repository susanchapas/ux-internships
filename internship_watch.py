#!/usr/bin/env python3
"""
internship_watch.py — poll ATS job APIs, notify on new matching postings.

Usage:
    python internship_watch.py                 # normal run
    python internship_watch.py --dry-run       # print matches, don't notify or save state
    python internship_watch.py --seed          # mark everything currently open as "seen"

State lives in seen.json. Config lives in config.json.
"""

import argparse
import json
import os

from dotenv import load_dotenv
load_dotenv()
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode

import html as htmlmod

import requests

HERE = Path(__file__).parent
CONFIG_PATH = HERE / "config.json"
STATE_PATH = HERE / "seen.json"
HIDDEN_PATH = HERE / "hidden.json"

UA = {"User-Agent": "internship-watch/1.0 (personal job search tool)"}
TIMEOUT = 20
DASHBOARD_URL = "https://susanchapas.github.io/ux-internships/"

PAY_RE = re.compile(
    r"\$\s*[\d,]+(?:\.\d{2})?"
    r"(?:\s*(?:[-–—/]|to)\s*\$?\s*[\d,]+(?:\.\d{2})?)?"
    r"(?:\s*(?:per|/|an?)\s*(?:hour|hr|yr|year|month|week|annum|annually))?"
    r"(?:\s*(?:USD|CAD))?"
    r"(?:\s*(?:per|/|an?)\s*(?:hour|hr|yr|year|month|week|annum|annually))?",
    re.I,
)


def extract_pay(text):
    if not text:
        return ""
    text = htmlmod.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    matches = PAY_RE.findall(text)
    return "; ".join(dict.fromkeys(matches)) if matches else ""


# ---------------------------------------------------------------- fetchers
# Each fetcher yields dicts: {id, title, location, url, company, source, pay}


def fetch_greenhouse(slug, company):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    for j in r.json().get("jobs", []):
        yield {
            "id": f"gh:{slug}:{j['id']}",
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
            "company": company,
            "source": "greenhouse",
            "pay": extract_pay(j.get("content", "")),
            "posted_at": j.get("updated_at", ""),
        }


def fetch_lever(slug, company):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    for j in r.json():
        cats = j.get("categories") or {}
        text_blob = " ".join(filter(None, [
            j.get("descriptionPlain", ""),
            j.get("additionalPlain", ""),
            j.get("openingPlain", ""),
        ]))
        for section in j.get("lists", []):
            text_blob += " " + (section.get("content", "") if isinstance(section.get("content"), str) else "")
        yield {
            "id": f"lv:{slug}:{j['id']}",
            "title": j.get("text", ""),
            "location": cats.get("location", "") or "",
            "url": j.get("hostedUrl", ""),
            "company": company,
            "source": "lever",
            "pay": extract_pay(text_blob),
            "posted_at": (datetime.fromtimestamp(j["createdAt"] / 1000, tz=timezone.utc).isoformat()
                          if j.get("createdAt") else ""),
            "commitment": cats.get("commitment", ""),
        }


def fetch_ashby(slug, company):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    for j in r.json().get("jobs", []):
        desc = j.get("descriptionHtml", "") or j.get("description", "") or ""
        comp = j.get("compensationTierSummary", "") or ""
        yield {
            "id": f"ab:{slug}:{j.get('id')}",
            "title": j.get("title", ""),
            "location": j.get("location", "") or "",
            "url": j.get("jobUrl", ""),
            "company": company,
            "source": "ashby",
            "pay": comp or extract_pay(desc),
            "posted_at": j.get("publishedAt", ""),
            "employment_type": j.get("employmentType", ""),
        }


def fetch_smartrecruiters(slug, company):
    offset, page = 0, 100
    while True:
        url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit={page}&offset={offset}"
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        items = data.get("content", [])
        for j in items:
            loc = j.get("location") or {}
            city = loc.get("city", "")
            region = loc.get("region", "")
            comp = j.get("compensation") or {}
            pay = ""
            if comp:
                parts = []
                if comp.get("min"):
                    parts.append(f"${comp['min']:,.0f}")
                if comp.get("max"):
                    parts.append(f"${comp['max']:,.0f}")
                pay = " - ".join(parts)
            yield {
                "id": f"sr:{slug}:{j.get('id')}",
                "title": j.get("name", ""),
                "location": ", ".join(x for x in (city, region) if x),
                "url": f"https://jobs.smartrecruiters.com/{slug}/{j.get('id')}",
                "company": company,
                "source": "smartrecruiters",
                "pay": pay,
                "posted_at": j.get("releasedDate", ""),
            }
        offset += page
        if offset >= data.get("totalFound", 0) or not items:
            break
        time.sleep(0.3)


def fetch_workday(cfg, company):
    """
    Workday needs three pieces you read off the careers-page URL:
      https://<tenant>.wd<N>.myworkdayjobs.com/en-US/<site>/...
    config entry: {"tenant": "acme", "wd": 5, "site": "External", "search": "intern"}
    """
    tenant, wd, site = cfg["tenant"], cfg.get("wd", 5), cfg["site"]
    base = f"https://{tenant}.wd{wd}.myworkdayjobs.com"
    endpoint = f"{base}/wday/cxs/{tenant}/{site}/jobs"
    offset = 0
    while True:
        body = {
            "appliedFacets": {},
            "limit": 20,
            "offset": offset,
            "searchText": cfg.get("search", "intern"),
        }
        r = requests.post(
            endpoint,
            json=body,
            headers={**UA, "Accept": "application/json", "Content-Type": "application/json"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        posts = data.get("jobPostings", [])
        for j in posts:
            path = j.get("externalPath", "")
            pay = ""
            sal = j.get("compensationAmount") or j.get("salaryAmount") or ""
            if sal:
                pay = str(sal)
            yield {
                "id": f"wd:{tenant}:{path}",
                "title": j.get("title", ""),
                "location": j.get("locationsText", "") or "",
                "url": f"{base}/en-US/{site}{path}",
                "company": company,
                "source": "workday",
                "pay": pay,
                "posted_at": j.get("postedOn", ""),
            }
        offset += 20
        if offset >= data.get("total", 0) or not posts:
            break
        time.sleep(0.4)


def fetch_usajobs(cfg, company="US Federal Government"):
    """Needs a free API key: https://developer.usajobs.gov/APIRequest"""
    key = os.environ.get("USAJOBS_API_KEY")
    email = os.environ.get("USAJOBS_EMAIL")
    if not (key and email):
        print("  ! skipping USAJOBS (set USAJOBS_API_KEY and USAJOBS_EMAIL)")
        return
    headers = {**UA, "Authorization-Key": key, "User-Agent": email, "Host": "data.usajobs.gov"}
    for loc in cfg.get("locations", ["New York, New York", "Newark, New Jersey"]):
        params = {
            "Keyword": cfg.get("keyword", "intern"),
            "LocationName": loc,
            "ResultsPerPage": 100,
        }
        url = "https://data.usajobs.gov/api/search?" + urlencode(params)
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        items = r.json().get("SearchResult", {}).get("SearchResultItems", [])
        for it in items:
            d = it.get("MatchedObjectDescriptor", {})
            locs = d.get("PositionLocation") or [{}]
            sal = d.get("PositionRemuneration", [{}])
            pay = ""
            if sal and isinstance(sal, list) and sal[0]:
                s = sal[0]
                mn, mx = s.get("MinimumRange", ""), s.get("MaximumRange", "")
                desc = s.get("Description", "")
                if mn:
                    pay = f"${float(mn):,.0f}"
                    if mx and mx != mn:
                        pay += f" - ${float(mx):,.0f}"
                    if desc:
                        pay += f" {desc}"
            yield {
                "id": f"usa:{d.get('PositionID')}",
                "title": d.get("PositionTitle", ""),
                "location": locs[0].get("LocationName", ""),
                "url": d.get("PositionURI", ""),
                "company": d.get("OrganizationName", company),
                "source": "usajobs",
                "pay": pay,
                "posted_at": d.get("PublicationStartDate", ""),
            }
        time.sleep(0.5)


BOARD_FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "smartrecruiters": fetch_smartrecruiters,
}


# ---------------------------------------------------------------- filtering


def compile_filters(cfg):
    title_inc = re.compile("|".join(cfg["title_include"]), re.I)
    title_exc = re.compile("|".join(cfg["title_exclude"]), re.I) if cfg.get("title_exclude") else None
    loc_inc = re.compile("|".join(cfg["location_include"]), re.I)
    return title_inc, title_exc, loc_inc


def matches(job, title_inc, title_exc, loc_inc):
    title = job.get("title", "") or ""
    loc = job.get("location", "") or ""
    if not title_inc.search(title):
        return False
    if title_exc and title_exc.search(title):
        return False
    # Remote-friendly: allow if location is blank or says remote, plus geo matches
    if not loc:
        return True
    return bool(loc_inc.search(loc))


# ---------------------------------------------------------------- notify


def notify(new_jobs):
    lines = []
    for j in new_jobs:
        pay = f"\n💰 {j['pay']}" if j.get("pay") else ""
        lines.append(f"{j['company']} — {j['title']}\n{j['location']}{pay}\n{j['url']}")
    body = "\n\n".join(lines)
    subject = f"{len(new_jobs)} new UX posting{'s' if len(new_jobs) != 1 else ''}"

    ntfy_topic = os.environ.get("NTFY_TOPIC")
    if ntfy_topic:
        requests.post(
            f"https://ntfy.sh/{ntfy_topic}",
            data=body.encode("utf-8"),
            headers={"Title": subject, "Tags": "briefcase"},
            timeout=TIMEOUT,
        )
        print(f"  -> pushed to ntfy.sh/{ntfy_topic}")

    discord = os.environ.get("DISCORD_WEBHOOK")
    if discord:
        by_company = {}
        for j in new_jobs:
            by_company.setdefault(j["company"], []).append(j)
        embeds = []
        for company, postings in by_company.items():
            desc_lines = []
            for j in postings:
                modal_url = f"{DASHBOARD_URL}#job={quote(j['id'], safe='')}"
                parts = [f"[{j['title']}]({modal_url})"]
                if j.get("location"):
                    parts.append(f"📍 {j['location']}")
                if j.get("pay"):
                    parts.append(f"💰 {j['pay']}")
                desc_lines.append(" · ".join(parts))
            embeds.append({
                "title": f"{company} ({len(postings)})",
                "description": "\n".join(desc_lines),
                "color": 0x5865F2,
            })
        summary = (
            f"🔔 **{len(new_jobs)}** new posting{'s' if len(new_jobs) != 1 else ''} "
            f"across **{len(by_company)}** compan{'ies' if len(by_company) != 1 else 'y'}"
        )
        for i in range(0, len(embeds), 10):
            batch = embeds[i:i + 10]
            payload = {"embeds": batch}
            if i == 0:
                payload["content"] = summary
            requests.post(discord, json=payload, timeout=TIMEOUT)
            time.sleep(0.5)
        print("  -> posted to Discord")

    if not (ntfy_topic or discord):
        print("  ! no notification channel configured; printing instead\n")
        print(body)


# ---------------------------------------------------------------- main


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", action="store_true", help="mark all current postings as seen")
    args = ap.parse_args()

    cfg = load_json(CONFIG_PATH, None)
    if cfg is None:
        sys.exit(f"missing {CONFIG_PATH}")
    seen = set(load_json(STATE_PATH, {"ids": []})["ids"])

    title_inc, title_exc, loc_inc = compile_filters(cfg)
    found, errors = [], []

    for entry in cfg["companies"]:
        board = entry["board"]
        company = entry.get("name", entry.get("slug", board))
        try:
            if board in BOARD_FETCHERS:
                jobs = list(BOARD_FETCHERS[board](entry["slug"], company))
            elif board == "workday":
                jobs = list(fetch_workday(entry, company))
            elif board == "usajobs":
                jobs = list(fetch_usajobs(entry))
            else:
                errors.append(f"{company}: unknown board '{board}'")
                continue
        except Exception as e:
            errors.append(f"{company} ({board}): {type(e).__name__} {e}")
            continue

        hits = [j for j in jobs if matches(j, title_inc, title_exc, loc_inc)]
        print(f"{company:<28} {len(jobs):>4} open  {len(hits):>3} match")
        found.extend(hits)
        time.sleep(0.4)

    if errors:
        print("\nerrors:")
        for e in errors:
            print("  -", e)

    hidden = set(load_json(HIDDEN_PATH, []))
    new = [j for j in found if j["id"] not in seen and j["id"] not in hidden]
    print(f"\n{len(found)} matches, {len(new)} new")

    if args.seed:
        STATE_PATH.write_text(json.dumps({"ids": sorted({j["id"] for j in found} | seen)}, indent=1))
        print("seeded state; nothing sent")
        return

    if args.dry_run:
        for j in new:
            pay = f" | {j['pay']}" if j.get("pay") else ""
            print(f"  {j['company']} | {j['title']} | {j['location']}{pay}\n    {j['url']}")
        return

    if new:
        notify(new)
        seen |= {j["id"] for j in new}
        STATE_PATH.write_text(
            json.dumps({"updated": datetime.now(timezone.utc).isoformat(), "ids": sorted(seen)}, indent=1)
        )


if __name__ == "__main__":
    main()
