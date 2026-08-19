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
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

HERE = Path(__file__).parent
CONFIG_PATH = HERE / "config.json"
STATE_PATH = HERE / "seen.json"

UA = {"User-Agent": "internship-watch/1.0 (personal job search tool)"}
TIMEOUT = 20


# ---------------------------------------------------------------- fetchers
# Each fetcher yields dicts: {id, title, location, url, company, source}


def fetch_greenhouse(slug, company):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false"
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
        }


def fetch_lever(slug, company):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    for j in r.json():
        cats = j.get("categories") or {}
        yield {
            "id": f"lv:{slug}:{j['id']}",
            "title": j.get("text", ""),
            "location": cats.get("location", "") or "",
            "url": j.get("hostedUrl", ""),
            "company": company,
            "source": "lever",
        }


def fetch_ashby(slug, company):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    for j in r.json().get("jobs", []):
        yield {
            "id": f"ab:{slug}:{j.get('id')}",
            "title": j.get("title", ""),
            "location": j.get("location", "") or "",
            "url": j.get("jobUrl", ""),
            "company": company,
            "source": "ashby",
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
            yield {
                "id": f"sr:{slug}:{j.get('id')}",
                "title": j.get("name", ""),
                "location": ", ".join(x for x in (city, region) if x),
                "url": f"https://jobs.smartrecruiters.com/{slug}/{j.get('id')}",
                "company": company,
                "source": "smartrecruiters",
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
            yield {
                "id": f"wd:{tenant}:{path}",
                "title": j.get("title", ""),
                "location": j.get("locationsText", "") or "",
                "url": f"{base}/en-US/{site}{path}",
                "company": company,
                "source": "workday",
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
            yield {
                "id": f"usa:{d.get('PositionID')}",
                "title": d.get("PositionTitle", ""),
                "location": locs[0].get("LocationName", ""),
                "url": d.get("PositionURI", ""),
                "company": d.get("OrganizationName", company),
                "source": "usajobs",
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


def notify(new_jobs, cfg):
    lines = []
    for j in new_jobs:
        lines.append(f"{j['company']} — {j['title']}\n{j['location']}\n{j['url']}")
    body = "\n\n".join(lines)
    subject = f"{len(new_jobs)} new internship posting{'s' if len(new_jobs) != 1 else ''}"

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
        # Discord caps at 2000 chars; chunk it.
        chunks, cur = [], f"**{subject}**\n\n"
        for block in lines:
            if len(cur) + len(block) > 1800:
                chunks.append(cur)
                cur = ""
            cur += block + "\n\n"
        chunks.append(cur)
        for c in chunks:
            requests.post(discord, json={"content": c}, timeout=TIMEOUT)
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

    new = [j for j in found if j["id"] not in seen]
    print(f"\n{len(found)} matches, {len(new)} new")

    if args.seed:
        STATE_PATH.write_text(json.dumps({"ids": sorted({j["id"] for j in found} | seen)}, indent=1))
        print("seeded state; nothing sent")
        return

    if args.dry_run:
        for j in new:
            print(f"  {j['company']} | {j['title']} | {j['location']}\n    {j['url']}")
        return

    if new:
        notify(new, cfg)
        seen |= {j["id"] for j in new}
        STATE_PATH.write_text(
            json.dumps({"updated": datetime.now(timezone.utc).isoformat(), "ids": sorted(seen)}, indent=1)
        )


if __name__ == "__main__":
    main()
