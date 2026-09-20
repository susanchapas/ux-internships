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
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
load_dotenv()
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode, urljoin

import html as htmlmod

import requests
from extractors import fetch_bamboohr, fetch_recruitee, fetch_eightfold, page_fingerprint

HERE = Path(__file__).parent
CONFIG_PATH = HERE / "config.json"
STATE_PATH = HERE / "seen.json"
HIDDEN_PATH = HERE / "hidden.json"

UA = {"User-Agent": "internship-watch/1.0 (personal job search tool)"}
TIMEOUT = 20
DEFAULT_BATCH_SIZE = 1
BETWEEN_BATCH_DELAY = 1.0
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "http://127.0.0.1:8080/")

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
            "description": j.get("content", "") or "",
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
            "description": text_blob,
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
            "description": desc,
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
            "description": " ".join(str(j.get(k, "")) for k in ("jobAd", "jobAdText", "description")),
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
    # Workday only supports one free-text query per request. Query the common
    # early-career names so a board that calls its roles "placements" or
    # "fellowships" is not invisible to an internship-only search.
    queries = cfg.get("search_terms") or [
        cfg.get("search", "intern"), "co-op", "fellowship", "apprentice",
        "trainee", "placement", "extern", "residency", "student",
    ]
    emitted = set()
    for query in dict.fromkeys(q for q in queries if q):
        offset = 0
        while True:
            body = {
                "appliedFacets": {},
                "limit": 20,
                "offset": offset,
                "searchText": query,
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
                if path in emitted:
                    continue
                emitted.add(path)
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
                    "description": " ".join(str(j.get(k, "")) for k in ("bulletFields", "externalDescription", "jobDescription")),
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


def fetch_workable(slug, company):
    url = f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true"
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    for j in r.json().get("jobs", []):
        loc = ", ".join(x for x in (j.get("city"), j.get("state") or j.get("country")) if x)
        yield {
            "id": f"wk:{slug}:{j.get('shortcode')}",
            "title": j.get("title", ""),
            "location": loc,
            "url": j.get("url") or j.get("application_url", ""),
            "company": company,
            "source": "workable",
            "pay": "",
        }


def fetch_jsonld(url, company):
    """Fetch JobPosting objects embedded on a public careers page.

    This is a conservative fallback for employers whose ATS has no supported
    public API.  A page with no JobPosting schema simply yields no jobs.
    """
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        r.text, re.S | re.I,
    )

    def walk(value):
        if isinstance(value, list):
            for item in value:
                yield from walk(item)
        elif isinstance(value, dict):
            if "@graph" in value:
                yield from walk(value["@graph"])
            else:
                yield value

    for block in blocks:
        try:
            data = json.loads(htmlmod.unescape(block.strip()))
        except (json.JSONDecodeError, TypeError):
            continue
        for job in walk(data):
            if "JobPosting" not in str(job.get("@type", "")):
                continue
            locations = job.get("jobLocation") or []
            if not isinstance(locations, list):
                locations = [locations]
            location_parts = []
            for loc in locations:
                address = loc.get("address", {}) if isinstance(loc, dict) else {}
                if isinstance(address, list):
                    address = address[0] if address else {}
                if isinstance(address, dict):
                    location_parts.append(
                        ", ".join(str(address.get(key, "")) for key in
                                  ("addressLocality", "addressRegion", "addressCountry")
                                  if address.get(key))
                    )
            if job.get("jobLocationType") == "TELECOMMUTE":
                location_parts.append("Remote")
            title = job.get("title", "")
            job_url = urljoin(r.url, job.get("url") or url)
            key = hashlib.sha256(f"{job_url}|{title}|{job.get('datePosted', '')}".encode()).hexdigest()[:16]
            salary = job.get("baseSalary") or ""
            if isinstance(salary, dict):
                salary = json.dumps(salary, sort_keys=True)
            yield {
                "id": f"ld:{key}",
                "title": title,
                "location": "; ".join(part for part in location_parts if part),
                "url": job_url,
                "company": company,
                "source": "jsonld",
                "pay": str(salary),
                "description": job.get("description", "") or "",
                "posted_at": job.get("datePosted", ""),
            }


def fetch_hydration_jobs(url, company):
    """Best-effort fallback for Next.js career pages without JSON-LD.

    It only accepts objects that look like a job (a title plus a URL/id), so
    generic page cards are not turned into postings.
    """
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    m = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', r.text, re.S | re.I)
    if not m:
        return
    try:
        payload = json.loads(htmlmod.unescape(m.group(1)).strip())
    except (json.JSONDecodeError, TypeError):
        return

    def walk(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)

    seen = set()
    for item in walk(payload):
        title = item.get("title") or item.get("name") or item.get("text")
        path = item.get("absolute_url") or item.get("absoluteUrl") or item.get("jobUrl") or item.get("url") or item.get("externalPath")
        identifier = item.get("id") or item.get("jobId") or path
        if not isinstance(title, str) or not title.strip() or not identifier or not path:
            continue
        job_url = urljoin(r.url, str(path))
        key = f"hydr:{hashlib.sha256(str(identifier).encode()).hexdigest()[:16]}"
        if key in seen:
            continue
        seen.add(key)
        location = item.get("location") or item.get("locationsText") or ""
        description = item.get("description") or item.get("descriptionHtml") or ""
        yield {
            "id": key, "title": title.strip(), "location": str(location),
            "url": job_url, "company": company, "source": "hydration",
            "description": str(description), "pay": extract_pay(str(description)),
            "posted_at": item.get("datePosted") or item.get("postedOn") or "",
        }


def fetch_jsonld_with_fallback(url, company):
    jobs = list(fetch_jsonld(url, company))
    if jobs:
        yield from jobs
        return
    yield from fetch_hydration_jobs(url, company)


BOARD_FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "smartrecruiters": fetch_smartrecruiters,
    "workable": fetch_workable,
    "bamboohr": fetch_bamboohr,
    "recruitee": fetch_recruitee,
    "eightfold": fetch_eightfold,
    "jsonld": fetch_jsonld_with_fallback,
}


# ---------------------------------------------------------------- filtering


def compile_filters(cfg):
    title_inc = re.compile("|".join(cfg["title_include"]), re.I)
    title_exc = re.compile("|".join(cfg["title_exclude"]), re.I) if cfg.get("title_exclude") else None
    loc_inc = re.compile("|".join(cfg["location_include"]), re.I)
    loc_exc = re.compile("|".join(cfg["location_exclude"]), re.I) if cfg.get("location_exclude") else None
    return title_inc, title_exc, loc_inc, loc_exc


def compile_discovery_filters(cfg):
    """Compile additive lanes; core title matching remains unchanged."""
    description_inc = re.compile(cfg.get("description_include", "(?!)"), re.I)
    adjacent_inc = re.compile(cfg.get("adjacent_title_include", "(?!)"), re.I)
    early_career_inc = re.compile(cfg.get("early_career_include", "(?!)"), re.I)
    return description_inc, adjacent_inc, early_career_inc


_CORE_UX_RE = re.compile(
    r"\bUX\b|\bUI\b|\buser experience|\buser interface|\buser research"
    r"|\bproduct design|\binteraction design|\binteractive design"
    r"|\bexperience design|\bhuman-centered design|\binclusive design"
    r"|\baccessibility\b|\ba11y\b|\busability\b|\bHCI\b|\bUXR\b"
    r"|\bdesign research|\bdesign system|\bcontent design|\bUX writing"
    r"|\bdesign engineer|\bdesign engineering|\bcreative developer|\bcreative development"
    r"|\bUX engineer|\bUX developer|\bUI engineer|\bUI developer",
    re.I,
)

_DOMAIN_EXCLUDE_RE = re.compile(
    r"\bsales\b|\brecruiting\b|\brecruiter\b|\btalent acquisition\b|\bclinical\b"
    r"|\bhuman resources\b|\bhr\b|\blegal\b|\bcompliance\b|\baudit\b|\baccounting\b"
    r"|\bsupply chain\b|\bdata science\b|\bdata scientist\b|\bmachine learning\b|\bdata analyst\b"
    r"|\bequity research\b|\bcredit research\b",
    re.I,
)

_REMOTE_RE = re.compile(
    r"\bremote\b|\bhybrid\b|\bvirtual\b|\btelecommute\b|\btelecommuting\b|\bwork from home\b|\bwfh\b|\banywhere\b|\bdistributed\b",
    re.I,
)
_US_RE = re.compile(r"\bUS\b|\bU\.S\b|\bUSA\b|\bunited states\b", re.I)
_REMOTE_WORDS_RE = re.compile(
    r"\bremote\b|\bhybrid\b|\bvirtual\b|\btelecommute\b|\btelecommuting\b"
    r"|\bwork from home\b|\bwfh\b|\banywhere\b|\bdistributed\b",
    re.I,
)
_LOCATION_TEXT_RE = re.compile(r"[A-Za-z]")
_OUT_OF_AREA_STATE_RE = re.compile(
    r",\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NM|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b"
    r"|,\s*(?:alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new mexico|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|wisconsin|wyoming|district of columbia)\b",
    re.I,
)


def matches(job, title_inc, title_exc, loc_inc, loc_exc=None):
    title = job.get("title", "") or ""
    loc = job.get("location", "") or ""
    if not title_inc.search(title):
        return False
    if title_exc and title_exc.search(title):
        # Option 1: Core UX Immunity
        # If the title explicitly contains a core UX/Product Design discipline,
        # internal business domain keywords (sales, recruiting, HR, legal, etc.)
        # do not disqualify the posting.
        if _CORE_UX_RE.search(title):
            stripped = _DOMAIN_EXCLUDE_RE.sub(" ", title)
            if title_exc.search(stripped):
                return False
        else:
            return False
    return location_is_eligible(loc, loc_inc, loc_exc)


def location_is_eligible(location, loc_inc, loc_exc=None):
    """Whether a posting is commutable or an eligible remote role.

    Remote is deliberately evaluated before the local-location allowlist.
    Unqualified "Remote" is allowed, but a remote role naming a place must
    explicitly be US-scoped or offer one of the allowed local areas.
    """
    # A missing location cannot establish that the role is commutable or US
    # remote, so keep it out rather than treating it as an unrestricted match.
    if not location:
        return False
    if _REMOTE_RE.search(location):
        if _US_RE.search(location):
            return True
        # "Remote — San Francisco" and "Remote — Canada" both name a place
        # outside the allowed set.  A bare "Remote" remains eligible.
        if loc_exc and loc_exc.search(location):
            return False
        if loc_inc.search(location):
            return True
        place_text = _REMOTE_WORDS_RE.sub(" ", location)
        if _LOCATION_TEXT_RE.search(place_text):
            return False
        return True
    # Check exclusions first: a location such as "Brooklyn, Canada" must not
    # pass merely because it includes an allowed city name.
    return (
        not (loc_exc and loc_exc.search(location))
        and not _OUT_OF_AREA_STATE_RE.search(location)
        and bool(loc_inc.search(location))
    )


def classify_match(job, title_inc, title_exc, loc_inc, loc_exc, description_inc, adjacent_inc, early_career_inc, allow_all_remote=False):
    """Return a discovery lane or None, without narrowing legacy title hits."""
    title = job.get("title", "") or ""
    description = job.get("description", "") or ""
    location = job.get("location", "") or ""

    # Preserve every existing title match exactly as before.
    core = matches(job, title_inc, title_exc, loc_inc, loc_exc)
    if not core and allow_all_remote and _REMOTE_RE.search(location) and location_is_eligible(location, loc_inc, loc_exc):
        core = bool(title_inc.search(title)) and not (title_exc and title_exc.search(title))
    if core:
        return "core-title"

    # A generic internship title can still be highly relevant when its body
    # names the discipline. Adjacent titles are deliberately labeled, not
    # blended into the core UX results.
    early_career = bool(early_career_inc.search(f"{title} {description}"))
    location_ok = location_is_eligible(location, loc_inc, loc_exc)
    if early_career and location_ok and description_inc.search(description):
        return "description-match"
    if early_career and location_ok and adjacent_inc.search(title):
        return "adjacent-role"
    return None


# ---------------------------------------------------------------- notify


def notify(new_jobs):
    lines = []
    for j in new_jobs:
        pay = f"\n💰 {j['pay']}" if j.get("pay") else ""
        status = "UPDATED " if j.get("is_update") else "NEW "
        lane = f" [{j['match_lane']}]" if j.get("match_lane") and j.get("match_lane") != "core-title" else ""
        lines.append(f"{status}{j['company']} — {j['title']}{lane}\n{j['location']}{pay}\n{j['url']}")
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
        discord_re = re.compile(
            r"\bintern\b|\bapprentice\b|\bfellow(?:ship)?\b|\bstudent\b"
            r"|\bco-?op\b|\bcooperative education\b|\bsummer\s+(?:analyst|associate|scholar|intern)\b"
            r"|\bearly[- ](?:career|talent)\b|\bemerging talent\b|\bnew[- ]grad\b"
            r"|\bundergraduate\b|\bundergrad\b|\bgraduate\b|\bpostgrad\b"
            r"|\btrainee\b|\bextern\b|\bresiden(?:cy)?\b|\bpracticum\b|\bpathways\b",
            re.I,
        )
        discord_jobs = [j for j in new_jobs if discord_re.search(j.get("title", ""))]
        if not discord_jobs:
            print("  -> no early-career postings for Discord")
        else:
            by_company = {}
            for j in discord_jobs:
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
                f"🔔 **{len(discord_jobs)}** new posting{'s' if len(discord_jobs) != 1 else ''} "
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


def notify_source_health(alerts):
    """Send scan failures and suspicious empty boards through active channels."""
    if not alerts:
        return
    body = "\n".join(f"• {a['company']}: {a['reason']}" for a in alerts)
    ntfy_topic = os.environ.get("NTFY_TOPIC")
    if ntfy_topic:
        requests.post(
            f"https://ntfy.sh/{ntfy_topic}", data=body.encode("utf-8"),
            headers={"Title": "Internship scan source alert", "Tags": "warning"}, timeout=TIMEOUT,
        )
    discord = os.environ.get("DISCORD_WEBHOOK")
    if discord:
        requests.post(discord, json={"content": f"⚠️ **Internship scan source alert**\n{body}"}, timeout=TIMEOUT)


# --------------------------------------------------------- app reminders


def _should_remind(app):
    interval = app.get("reminder_interval", "daily")
    if interval == "off":
        return False
    if interval == "daily":
        return True
    created = app.get("created_at", "")[:10]
    if not created:
        return True
    try:
        from datetime import datetime, timezone
        created_date = datetime.strptime(created, "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        days_since = (today - created_date).days
    except ValueError:
        return True
    if interval == "every_3_days":
        return days_since % 3 == 0
    if interval == "weekly":
        return days_since % 7 == 0
    return True


def _deadline_label(deadline_str):
    if not deadline_str:
        return ""
    try:
        from datetime import datetime, timezone
        dl = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        diff = (dl - today).days
    except ValueError:
        return ""
    if diff < 0:
        return f"🔴 {-diff}d overdue"
    if diff == 0:
        return "🔴 Due today"
    if diff <= 3:
        return f"⚠️ {diff}d left"
    return f"📅 {dl.strftime('%b %d')}"


def remind_saved_applications():
    discord = os.environ.get("DISCORD_WEBHOOK")
    if not discord:
        print("  ! no DISCORD_WEBHOOK set; skipping reminders")
        return

    from db import list_saved_applications
    saved = [a for a in list_saved_applications() if _should_remind(a)]
    if not saved:
        print("  -> no saved applications to remind about")
        return

    saved.sort(key=lambda a: (a.get("deadline") or "9999", a.get("created_at", "")))

    desc_lines = []
    for app in saved:
        parts = [f"**{app['company']}** — {app['title']}"]
        if app.get("url"):
            modal_url = f"{DASHBOARD_URL}#app={app['id']}"
            parts[0] = f"[{app['company']} — {app['title']}]({modal_url})"
        if app.get("location"):
            parts.append(f"📍 {app['location']}")
        dl_label = _deadline_label(app.get("deadline", ""))
        if dl_label:
            parts.append(dl_label)
        else:
            saved_date = app.get("created_at", "")[:10]
            if saved_date:
                parts.append(f"saved {saved_date}")
        desc_lines.append(" · ".join(parts))

    embed = {
        "title": f"📋 {len(saved)} saved application{'s' if len(saved) != 1 else ''} — not yet applied",
        "description": "\n".join(desc_lines),
        "color": 0xFEE75C,
    }
    payload = {
        "content": "⏰ **Application reminder** — you saved these but haven't applied yet!",
        "embeds": [embed],
    }
    requests.post(discord, json=payload, timeout=TIMEOUT)
    print(f"  -> reminded about {len(saved)} saved applications on Discord")


# ---------------------------------------------------------------- main


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def fetch_company(entry):
    """Fetch one source, returning an error instead of stopping the scan.

    This function deliberately performs a single company's requests in order.
    The caller runs different companies concurrently in bounded batches, so
    pagination and the Workday search-term sequence remain gentle per source.
    """
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
            return company, None, f"unknown board '{board}'"
    except Exception as e:
        return company, None, f"{type(e).__name__}: {e}"
    return company, jobs, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", action="store_true", help="mark all current postings as seen")
    ap.add_argument("--remind", action="store_true", help="send Discord reminders for saved applications")
    ap.add_argument(
        "--batch-size", type=int, default=None,
        help=f"number of company sources to fetch concurrently (default: {DEFAULT_BATCH_SIZE})",
    )
    args = ap.parse_args()

    if args.remind:
        from db import init_db
        init_db()
        remind_saved_applications()
        return

    cfg = load_json(CONFIG_PATH, None)
    if cfg is None:
        sys.exit(f"missing {CONFIG_PATH}")
    batch_size = args.batch_size if args.batch_size is not None else cfg.get("scan_batch_size", DEFAULT_BATCH_SIZE)
    if batch_size < 1:
        ap.error("--batch-size must be at least 1")
    state = load_json(STATE_PATH, {"ids": []})
    seen = set(state["ids"])
    prior_fingerprints = state.get("fingerprints", {})
    prior_sources = state.get("sources", {})
    prior_page_fingerprints = state.get("page_fingerprints", {})

    title_inc, title_exc, loc_inc, loc_exc = compile_filters(cfg)
    description_inc, adjacent_inc, early_career_inc = compile_discovery_filters(cfg)
    found, errors, disabled = [], [], []
    source_status = {}
    page_fingerprints = {}
    page_alerts = []

    # Non-ATS career pages cannot reliably yield structured jobs. Monitor a
    # normalized page fingerprint so a meaningful change prompts a manual look.
    for watch in cfg.get("page_watches", []):
        try:
            fingerprint, _ = page_fingerprint(watch["url"], watch.get("selector"), watch.get("strip_patterns"))
            page_fingerprints[watch["url"]] = fingerprint
            if prior_page_fingerprints.get(watch["url"]) not in (None, fingerprint):
                page_alerts.append({"company": watch["name"], "reason": "manual careers page changed"})
        except Exception as e:
            errors.append({"company": watch["name"], "error": f"page watch {type(e).__name__}: {e}"})

    enabled_entries = []
    for entry in cfg["companies"]:
        company = entry.get("name", entry.get("slug", entry["board"]))
        if not entry.get("enabled", True):
            disabled.append({"company": company, "reason": entry.get("disabled_reason", "disabled in config")})
            continue
        enabled_entries.append(entry)

    print(f"scanning {len(enabled_entries)} sources in batches of {batch_size}")
    for start in range(0, len(enabled_entries), batch_size):
        batch = enabled_entries[start:start + batch_size]
        # executor.map preserves config order, keeping console output stable.
        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            results = executor.map(fetch_company, batch)
            for company, jobs, error in results:
                if error:
                    errors.append({"company": company, "error": error})
                    source_status[company] = {"count": None, "error": error}
                    continue

                source_status[company] = {"count": len(jobs), "error": ""}
                hits = []
                for job in jobs:
                    lane = classify_match(
                        job, title_inc, title_exc, loc_inc, loc_exc,
                        description_inc, adjacent_inc, early_career_inc,
                        cfg.get("allow_all_remote", False),
                    )
                    if lane:
                        job["match_lane"] = lane
                        hits.append(job)
                print(f"{company:<28} {len(jobs):>4} open  {len(hits):>3} match")
                found.extend(hits)
        if start + batch_size < len(enabled_entries):
            time.sleep(BETWEEN_BATCH_DELAY)

    if errors:
        print("\nerrors:")
        for e in errors:
            print(f"  - {e['company']}: {e['error']}")

    if disabled:
        print(f"\nskipped {len(disabled)} disabled source{'s' if len(disabled) != 1 else ''}:")
        for entry in disabled:
            print(f"  - {entry['company']}: {entry['reason']}")

    hidden = set(load_json(HIDDEN_PATH, []))
    fingerprints = {
        j["id"]: hashlib.sha256(json.dumps(
            {k: j.get(k, "") for k in ("title", "location", "url", "pay", "description")},
            sort_keys=True,
        ).encode()).hexdigest()
        for j in found
    }
    new = []
    for job in found:
        if job["id"] in hidden:
            continue
        is_update = job["id"] in seen and prior_fingerprints.get(job["id"]) not in (None, fingerprints[job["id"]])
        if job["id"] not in seen or is_update:
            job["is_update"] = is_update
            new.append(job)
    health_alerts = []
    for company, status in source_status.items():
        previous = prior_sources.get(company, {})
        if status["error"] and status["error"] != previous.get("error"):
            health_alerts.append({"company": company, "reason": status["error"]})
        elif status["count"] == 0 and previous.get("count", 0) > 0:
            health_alerts.append({"company": company, "reason": "board returned zero postings"})
    health_alerts.extend(page_alerts)
    print(f"\n{len(found)} matches, {len(new)} new or updated")
    if health_alerts:
        print(f"{len(health_alerts)} source health alert{'s' if len(health_alerts) != 1 else ''}")

    if args.seed:
        STATE_PATH.write_text(json.dumps({"ids": sorted({j["id"] for j in found} | seen), "fingerprints": fingerprints, "sources": source_status, "page_fingerprints": page_fingerprints}, indent=1))
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
    notify_source_health(health_alerts)
    STATE_PATH.write_text(json.dumps({
        "updated": datetime.now(timezone.utc).isoformat(), "ids": sorted(seen),
        "fingerprints": fingerprints, "sources": source_status, "page_fingerprints": page_fingerprints,
    }, indent=1))

    (HERE / "_scan_results.json").write_text(json.dumps({
        "jobs": found, "errors": errors, "disabled": disabled, "health_alerts": health_alerts,
        "companies_scanned": len(cfg["companies"]) - len(disabled),
    }, default=str))


if __name__ == "__main__":
    main()
