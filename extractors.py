#!/usr/bin/env python3
"""
extractors.py — scrapers for companies whose careers pages aren't on a
board covered by internship_watch.py.

Four strategies, in descending order of how long they'll keep working:

  1. jsonld_jobs(url)        - schema.org/JobPosting markup. Standardized.
  2. hydration_jobs(url, ..) - __NEXT_DATA__ etc. Stable-ish, site-specific shape.
  3. css_jobs(url, cfg)      - CSS selectors. Breaks on redesign.
  4. page_fingerprint(url)   - just hash it and alert on change. Never breaks.

Plus extra ATS fetchers not in the main script. Confidence noted per fetcher —
verify with discover.py before trusting one.
"""

import hashlib
import json
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from selectolax.parser import HTMLParser

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
TIMEOUT = 25


def _get(url, **kw):
    r = requests.get(url, headers=UA, timeout=TIMEOUT, **kw)
    r.raise_for_status()
    return r


# ------------------------------------------------------------ 1. JSON-LD


def _flatten_ld(data):
    if isinstance(data, list):
        for d in data:
            yield from _flatten_ld(d)
    elif isinstance(data, dict):
        if "@graph" in data:
            yield from _flatten_ld(data["@graph"])
        else:
            yield data


def _ld_location(posting):
    loc = posting.get("jobLocation")
    if isinstance(loc, list):
        loc = loc[0] if loc else {}
    if not isinstance(loc, dict):
        return ""
    addr = loc.get("address")
    if isinstance(addr, list):
        addr = addr[0] if addr else {}
    if not isinstance(addr, dict):
        return str(addr or "")
    parts = [addr.get("addressLocality"), addr.get("addressRegion")]
    out = ", ".join(p for p in parts if p)
    if not out and posting.get("jobLocationType") == "TELECOMMUTE":
        return "Remote"
    return out


def parse_jsonld(html, url, company):
    """Pull JobPosting objects out of raw HTML. Returns job dicts."""
    out = []
    blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.S | re.I,
    )
    for b in blocks:
        try:
            data = json.loads(b.strip())
        except json.JSONDecodeError:
            continue
        for obj in _flatten_ld(data):
            if not isinstance(obj, dict):
                continue
            if "JobPosting" not in str(obj.get("@type", "")):
                continue
            ident = obj.get("identifier")
            if isinstance(ident, dict):
                ident = ident.get("value")
            job_url = obj.get("url") or url
            key = ident or job_url or obj.get("title")
            out.append({
                "id": f"ld:{company}:{hashlib.sha1(str(key).encode()).hexdigest()[:16]}",
                "title": obj.get("title", "") or "",
                "location": _ld_location(obj),
                "url": job_url,
                "company": company,
                "source": "json-ld",
                "posted": obj.get("datePosted", ""),
            })
    return out


def jsonld_jobs(url, company):
    return parse_jsonld(_get(url).text, url, company)


def jsonld_crawl(list_url, company, link_pattern, limit=60, delay=0.7):
    """
    Listings pages often carry no JSON-LD while each detail page does.
    Collect links matching link_pattern, then parse each one.
    """
    html = _get(list_url).text
    tree = HTMLParser(html)
    seen, links = set(), []
    for a in tree.css("a"):
        href = a.attributes.get("href")
        if not href:
            continue
        full = urljoin(list_url, href)
        if re.search(link_pattern, full) and full not in seen:
            seen.add(full)
            links.append(full)
    jobs = []
    for link in links[:limit]:
        try:
            jobs += parse_jsonld(_get(link).text, link, company)
        except requests.RequestException:
            pass
        time.sleep(delay)
    return jobs


# -------------------------------------------------- 2. hydration payloads

HYDRATION = {
    "next": r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    "nuxt": r"window\.__NUXT__\s*=\s*(\{.*?\})\s*;?\s*</script>",
    "initial_state": r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;?\s*</script>",
}


def hydration_payload(url, kind="next"):
    """Return the parsed JSON blob. Then explore it to find the jobs array."""
    m = re.search(HYDRATION[kind], _get(url).text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def find_arrays(obj, min_len=3, path="$", results=None, depth=0):
    """
    Walk a nested payload and report every list-of-dicts, with its key names.
    Run this once interactively to find where the jobs live, then hardcode the path.
    """
    if results is None:
        results = []
    if depth > 12:
        return results
    if isinstance(obj, dict):
        for k, v in obj.items():
            find_arrays(v, min_len, f"{path}.{k}", results, depth + 1)
    elif isinstance(obj, list) and len(obj) >= min_len and isinstance(obj[0], dict):
        results.append((path, len(obj), sorted(obj[0].keys())[:12]))
        find_arrays(obj[0], min_len, f"{path}[0]", results, depth + 1)
    return results


def dig(obj, path):
    """dig(payload, 'props.pageProps.jobs') -> the list"""
    cur = obj
    for part in path.replace("$.", "").split("."):
        if not part:
            continue
        if part.endswith("]"):
            key, idx = part[:-1].split("[")
            cur = cur[key][int(idx)]
        else:
            cur = cur[part]
    return cur


# ------------------------------------------------------- 3. CSS selectors


def css_jobs(url, cfg, company):
    """
    cfg = {
      "row":      "div.job-listing",        # repeating container
      "title":    "h3.job-title",           # relative to row
      "location": "span.job-location",      # optional
      "link":     "a",                      # optional; falls back to row itself
    }
    """
    html = _get(url).text
    tree = HTMLParser(html)
    jobs = []
    for row in tree.css(cfg["row"]):
        t_node = row.css_first(cfg["title"]) if cfg.get("title") else row
        title = t_node.text(strip=True) if t_node else ""
        if not title:
            continue
        loc = ""
        if cfg.get("location"):
            l_node = row.css_first(cfg["location"])
            loc = l_node.text(strip=True) if l_node else ""
        href = ""
        a = row.css_first(cfg.get("link", "a"))
        if a is None and row.tag == "a":
            a = row
        if a is not None:
            href = urljoin(url, a.attributes.get("href", "") or "")
        jobs.append({
            "id": f"css:{company}:{hashlib.sha1((title + loc).encode()).hexdigest()[:16]}",
            "title": title,
            "location": loc,
            "url": href or url,
            "company": company,
            "source": "css",
        })
    return jobs


# --------------------------------------------- 4. change detection fallback


def page_fingerprint(url, selector=None, strip_patterns=None):
    """
    For pages not worth parsing. Hash the relevant region; alert when it moves.
    strip_patterns removes volatile junk (timestamps, CSRF tokens, view counters)
    that would otherwise make every check look like a change.
    """
    html = _get(url).text
    if selector:
        node = HTMLParser(html).css_first(selector)
        text = node.text(separator=" ", strip=True) if node else ""
    else:
        text = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
    for pat in (strip_patterns or []):
        text = re.sub(pat, "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(text.encode()).hexdigest(), text


# ------------------------------------------------- extra ATS API fetchers
# Confidence noted — run discover.py against the real careers page first.


def fetch_workable(slug, company):
    """confidence: medium. apply.workable.com widget API."""
    url = f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true"
    data = _get(url).json()
    for j in data.get("jobs", []):
        loc = ", ".join(x for x in (j.get("city"), j.get("state") or j.get("country")) if x)
        yield {
            "id": f"wk:{slug}:{j.get('shortcode')}",
            "title": j.get("title", ""),
            "location": loc,
            "url": j.get("url") or j.get("application_url", ""),
            "company": company,
            "source": "workable",
        }


def fetch_bamboohr(slug, company):
    """confidence: medium. Common at smaller agencies."""
    url = f"https://{slug}.bamboohr.com/careers/list"
    data = _get(url).json()
    for j in data.get("result", []):
        loc = j.get("location") or {}
        parts = [loc.get("city"), loc.get("state")] if isinstance(loc, dict) else []
        yield {
            "id": f"bh:{slug}:{j.get('id')}",
            "title": (j.get("jobOpeningName") or "").strip(),
            "location": ", ".join(p for p in parts if p),
            "url": f"https://{slug}.bamboohr.com/careers/{j.get('id')}",
            "company": company,
            "source": "bamboohr",
        }


def fetch_recruitee(slug, company):
    """confidence: medium."""
    url = f"https://{slug}.recruitee.com/api/offers/"
    for j in _get(url).json().get("offers", []):
        yield {
            "id": f"rc:{slug}:{j.get('id')}",
            "title": j.get("title", ""),
            "location": j.get("location", "") or "",
            "url": j.get("careers_url") or j.get("careers_apply_url", ""),
            "company": company,
            "source": "recruitee",
        }


def fetch_eightfold(slug, company, domain=None, num=100):
    """
    confidence: medium-low. Used by several large enterprises.
    The ?domain= param is usually the company's main domain — check the
    Network tab on their careers page for the exact value.
    """
    domain = domain or f"{slug}.com"
    url = (f"https://{slug}.eightfold.ai/api/apply/v2/jobs"
           f"?domain={domain}&start=0&num={num}&sort_by=relevance")
    for j in _get(url).json().get("positions", []):
        locs = j.get("locations") or [j.get("location", "")]
        yield {
            "id": f"ef:{slug}:{j.get('id')}",
            "title": j.get("name", ""),
            "location": "; ".join(str(x) for x in locs if x),
            "url": j.get("canonicalPositionUrl", ""),
            "company": company,
            "source": "eightfold",
        }


EXTRA_FETCHERS = {
    "workable": fetch_workable,
    "bamboohr": fetch_bamboohr,
    "recruitee": fetch_recruitee,
    "eightfold": fetch_eightfold,
}


# ------------------------------------------------------- government feeds


def fetch_nyc_jobs(company="City of New York", keyword="intern", limit=1000):
    """
    NYC publishes every open city-agency posting as an Open Data (Socrata)
    dataset. Public, no key needed for modest volume. Covers all agencies:
    OTI, DDC, HRA, DOE, EDC, Health+Hospitals, Comptroller, etc.

    Dataset: "NYC Jobs" on data.cityofnewyork.us
    """
    url = "https://data.cityofnewyork.us/resource/kpav-sd4t.json"
    params = {
        "$limit": limit,
        "$where": (f"upper(business_title) like upper('%{keyword}%') OR "
                   f"upper(civil_service_title) like upper('%{keyword}%')"),
    }
    r = requests.get(url, params=params, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    for j in r.json():
        jid = j.get("job_id")
        yield {
            "id": f"nyc:{jid}",
            "title": j.get("business_title") or j.get("civil_service_title", ""),
            "location": j.get("work_location", "") or "New York, NY",
            "url": f"https://cityjobs.nyc.gov/job/?id={jid}",
            "company": j.get("agency", company),
            "source": "nyc-open-data",
            "salary": f"{j.get('salary_range_from','')}-{j.get('salary_range_to','')}",
        }


def fetch_state_ny(company="New York State", keyword="intern"):
    """
    NY State jobs aren't on a clean API. statejobs.ny.gov is server-rendered,
    so CSS selectors work — but the markup changes, so verify with discover.py
    before relying on it. Returns [] rather than raising if the shape moved.
    """
    try:
        html = _get(f"https://statejobs.ny.gov/public/vacancySearch.cfm?keyword={keyword}").text
    except requests.RequestException:
        return []
    tree = HTMLParser(html)
    rows = tree.css("tr")
    out = []
    for row in rows:
        cells = row.css("td")
        if len(cells) < 2:
            continue
        title = cells[0].text(strip=True)
        if keyword.lower() not in title.lower():
            continue
        a = row.css_first("a")
        out.append({
            "id": f"nys:{hashlib.sha1(title.encode()).hexdigest()[:16]}",
            "title": title,
            "location": cells[1].text(strip=True) if len(cells) > 1 else "New York",
            "url": urljoin("https://statejobs.ny.gov/", a.attributes.get("href", "")) if a else "",
            "company": company,
            "source": "nys",
        })
    return out
