#!/usr/bin/env python3
"""
discover.py — point it at a careers page, it tells you how to scrape it.

    python discover.py https://www.example.com/careers

Checks, in order of how much you'd rather it be true:
  1. Is this a known ATS with a public JSON API?
  2. Does the page embed JSON-LD JobPosting markup?
  3. Does it embed a hydration payload (__NEXT_DATA__, __NUXT__, etc.)?
  4. Is there an XHR endpoint the page calls? (heuristic — confirm in DevTools)
  5. Is there a sitemap listing job URLs?
  6. Is the job content even in the initial HTML, or is it JS-rendered?
"""

import json
import re
import sys
from urllib.parse import urljoin, urlparse

import requests

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
TIMEOUT = 25

# host fragment -> (board name, how to get the slug, confidence)
ATS_SIGNATURES = [
    ("boards.greenhouse.io", "greenhouse", "path segment after the domain", "high"),
    ("job-boards.greenhouse.io", "greenhouse", "path segment after the domain", "high"),
    ("boards-api.greenhouse.io", "greenhouse", "path segment after /boards/", "high"),
    ("jobs.lever.co", "lever", "path segment after the domain", "high"),
    ("api.lever.co", "lever", "path segment after /postings/", "high"),
    ("jobs.ashbyhq.com", "ashby", "path segment after the domain", "high"),
    ("ashbyhq.com", "ashby", "path segment after the domain", "high"),
    ("smartrecruiters.com", "smartrecruiters", "path segment (case-sensitive)", "high"),
    ("myworkdayjobs.com", "workday", "subdomain = tenant; path after /en-US/ = site", "high"),
    ("workable.com", "workable", "subdomain, or path after apply.workable.com/", "medium"),
    ("bamboohr.com", "bamboohr", "subdomain", "medium"),
    ("recruitee.com", "recruitee", "subdomain", "medium"),
    ("eightfold.ai", "eightfold", "subdomain; API also needs a ?domain= param", "medium"),
    ("icims.com", "icims", "subdomain — HTML only, no clean JSON", "low"),
    ("taleo.net", "taleo", "subdomain — legacy, messy", "low"),
    ("oraclecloud.com", "oracle_orc", "host + site number from the URL", "low"),
    ("successfactors.com", "successfactors", "?company= query param", "low"),
    ("jobvite.com", "jobvite", "path segment", "low"),
    ("phenompeople.com", "phenom", "varies — inspect Network tab", "low"),
    ("teamtailor.com", "teamtailor", "subdomain", "low"),
]

HYDRATION_PATTERNS = [
    ("__NEXT_DATA__", r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>'),
    ("__NUXT__", r"window\.__NUXT__\s*=\s*(.*?);?\s*</script>"),
    ("__INITIAL_STATE__", r"window\.__INITIAL_STATE__\s*=\s*(.*?);?\s*</script>"),
    ("__APOLLO_STATE__", r"window\.__APOLLO_STATE__\s*=\s*(.*?);?\s*</script>"),
]

# things that look like an API path inside page JS
ENDPOINT_HINT = re.compile(
    r"""["'](/(?:api|wp-json|_next/data|graphql)[^"'\s]{0,120})["']""", re.I
)

JOBWORD = re.compile(r"\b(intern|internship|co-?op|engineer|designer|analyst|manager)\b", re.I)


def get(url, **kw):
    return requests.get(url, headers=UA, timeout=TIMEOUT, allow_redirects=True, **kw)


def check_ats(url, html):
    hits = []
    haystack = url + " " + html[:200000]
    for frag, board, slug_hint, conf in ATS_SIGNATURES:
        if frag in haystack:
            where = "URL" if frag in url else "embedded in page (likely an iframe or widget)"
            hits.append((board, frag, slug_hint, conf, where))
    return hits


def check_jsonld(html):
    blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.S | re.I,
    )
    postings = []
    for b in blocks:
        try:
            data = json.loads(b.strip())
        except json.JSONDecodeError:
            continue
        for obj in flatten_ld(data):
            if isinstance(obj, dict) and "JobPosting" in str(obj.get("@type", "")):
                postings.append(obj)
    return len(blocks), postings


def flatten_ld(data):
    """JSON-LD shows up as a dict, a list, or wrapped in @graph."""
    if isinstance(data, list):
        for d in data:
            yield from flatten_ld(d)
    elif isinstance(data, dict):
        if "@graph" in data:
            yield from flatten_ld(data["@graph"])
        else:
            yield data


def check_hydration(html):
    found = []
    for name, pat in HYDRATION_PATTERNS:
        m = re.search(pat, html, re.S)
        if m:
            blob = m.group(1)
            has_jobs = bool(JOBWORD.search(blob[:400000]))
            found.append((name, len(blob), has_jobs))
    return found


def check_endpoints(html):
    return sorted({m for m in ENDPOINT_HINT.findall(html)})[:12]


def check_sitemap(base):
    root = f"{urlparse(base).scheme}://{urlparse(base).netloc}"
    out = []
    for path in ("/robots.txt", "/sitemap.xml"):
        try:
            r = get(urljoin(root, path))
            if r.status_code != 200:
                continue
            if path == "/robots.txt":
                maps = re.findall(r"(?im)^sitemap:\s*(\S+)", r.text)
                out += [("robots.txt lists sitemap", m) for m in maps[:5]]
                disallow = re.findall(r"(?im)^disallow:\s*(\S*)", r.text)
                job_blocked = [d for d in disallow if re.search(r"job|career", d, re.I)]
                if job_blocked:
                    out.append(("robots.txt disallows", ", ".join(job_blocked[:5])))
            else:
                locs = re.findall(r"<loc>(.*?)</loc>", r.text)
                joblocs = [l for l in locs if re.search(r"job|career|position|opening", l, re.I)]
                if joblocs:
                    out.append((f"sitemap.xml has {len(joblocs)} job-ish URLs", joblocs[0]))
                elif locs:
                    out.append((f"sitemap.xml ({len(locs)} URLs, none job-ish)", locs[0]))
        except requests.RequestException:
            pass
    return out


def check_static(html):
    """Is job text actually in the served HTML, or is the page an empty JS shell?"""
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    words = JOBWORD.findall(text)
    return len(text.split()), len(words)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python discover.py <careers-page-url>")
    url = sys.argv[1]

    try:
        r = get(url)
    except requests.RequestException as e:
        sys.exit(f"fetch failed: {type(e).__name__}: {e}")

    html = r.text
    final = r.url
    print(f"\n{'='*68}\n{final}\nHTTP {r.status_code} · {len(html):,} bytes\n{'='*68}")

    print("\n[1] KNOWN ATS")
    ats = check_ats(final, html)
    if ats:
        for board, frag, slug_hint, conf, where in ats:
            print(f"  ✓ {board}  (confidence: {conf})")
            print(f"      matched '{frag}' in {where}")
            print(f"      slug: {slug_hint}")
    else:
        print("  – none detected")

    print("\n[2] JSON-LD JobPosting")
    n_blocks, postings = check_jsonld(html)
    if postings:
        print(f"  ✓ {len(postings)} JobPosting object(s) in {n_blocks} ld+json block(s)")
        p = postings[0]
        loc = p.get("jobLocation")
        if isinstance(loc, list):
            loc = loc[0] if loc else {}
        addr = (loc or {}).get("address", {}) if isinstance(loc, dict) else {}
        print(f"      sample: {str(p.get('title'))[:60]}")
        print(f"              {addr.get('addressLocality','?')}, {addr.get('addressRegion','?')}")
        print("      -> best case: parse this, it's a standard schema")
    elif n_blocks:
        types = set()
        for b in re.findall(r'type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I):
            try:
                for o in flatten_ld(json.loads(b.strip())):
                    types.add(str(o.get("@type")))
            except Exception:
                pass
        print(f"  – {n_blocks} ld+json block(s) but no JobPosting (types: {', '.join(sorted(types))[:80]})")
        print("      try an individual job detail page — listings pages often omit it")
    else:
        print("  – none")

    print("\n[3] HYDRATION PAYLOAD")
    hyd = check_hydration(html)
    if hyd:
        for name, size, has_jobs in hyd:
            mark = "✓" if has_jobs else "–"
            note = "contains job-ish words" if has_jobs else "no job words found"
            print(f"  {mark} {name}  ({size:,} bytes, {note})")
        print("      -> extract the <script>, json.loads it, walk for the jobs array")
    else:
        print("  – none")

    print("\n[4] API PATHS REFERENCED IN PAGE")
    eps = check_endpoints(html)
    if eps:
        for e in eps:
            print(f"    {e}")
        print("      -> heuristic only; confirm in DevTools > Network > Fetch/XHR")
    else:
        print("  – none obvious")

    print("\n[5] SITEMAP / ROBOTS")
    sm = check_sitemap(final)
    if sm:
        for label, val in sm:
            print(f"    {label}: {val[:90]}")
    else:
        print("  – nothing useful")

    print("\n[6] IS CONTENT IN THE STATIC HTML?")
    nwords, njobwords = check_static(html)
    print(f"    {nwords:,} words of visible text, {njobwords} job-related terms")
    if njobwords >= 5:
        print("    ✓ content is server-rendered — plain requests + a parser will work")
    elif nwords < 200:
        print("    ✗ near-empty shell — JS-rendered, you'll need Playwright or the API")
    else:
        print("    ? text present but few job words — check if listings are behind a click")

    print("\n" + "-" * 68)
    print("RECOMMENDATION")
    if ats and any(c == "high" for *_, c, _ in [(a[0], a[1], a[2], a[3], a[4]) for a in ats]):
        print("  Use the ATS fetcher in internship_watch.py. Done.")
    elif postings:
        print("  Use the JSON-LD extractor. Stable across redesigns.")
    elif hyd and any(h[2] for h in hyd):
        print("  Extract the hydration payload — it's the same data the API returns.")
    elif eps:
        print("  Open DevTools > Network > Fetch/XHR, reload, find the jobs call. Replay it with requests.")
    elif njobwords >= 5:
        print("  Write CSS selectors against the static HTML (see extractors.py).")
    else:
        print("  Playwright, or fall back to hash-based change detection.")
    print()


if __name__ == "__main__":
    main()
