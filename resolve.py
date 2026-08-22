#!/usr/bin/env python3
"""
resolve.py — turn company NAMES into verified ATS slugs, then write config.json.

I can't know these slugs ahead of time (companies migrate boards, and slugs
aren't derivable from the name). So this probes the actual APIs and keeps only
what responds.

    python resolve.py --category fintech_core      # start small
    python resolve.py --all                        # everything (slow, ~1hr)
    python resolve.py --report                     # show cache, no network
    python resolve.py --write-config               # emit config.json from cache

Results cache to resolved.json, so re-runs are cheap and resumable.
"""

import argparse
import itertools
import json
import re
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).parent
TARGETS = HERE / "targets.json"
CACHE = HERE / "resolved.json"
OUT_CONFIG = HERE / "config.json"

UA = {"User-Agent": "internship-watch/1.0 (personal job search tool)"}
TIMEOUT = 12
DELAY = 0.6          # between probes; be polite, this is a lot of requests
MAX_CANDIDATES = 8   # slug guesses to try per company

STOPWORDS = {
    "inc", "corp", "corporation", "llc", "ltd", "limited", "company", "co",
    "group", "holdings", "the", "usa", "us", "plc", "pbc",
}


# ------------------------------------------------------------ slug candidates


def _words(text):
    text = re.sub(r"[.'’,/]", "", text.lower())
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return [w for w in text.split() if w]


def candidates(name, hint=None):
    """Generate plausible slugs, best guess first."""
    out = []
    if hint:
        out.append(hint)

    # "&" is ambiguous: J&J -> johnsonandjohnson OR johnsonjohnson OR jnj.
    # Generate both expansions.
    variants = [
        name.replace("&", " and ").replace("+", " and "),
        name.replace("&", " ").replace("+", " "),
    ]

    for variant in variants:
        words = _words(variant)
        if not words:
            continue
        meaningful = [w for w in words if w not in STOPWORDS] or words

        out.append("".join(meaningful))
        out.append("-".join(meaningful))

        if len(meaningful) > 1:
            out.append("".join(meaningful[:-1]))   # drop trailing generic
            out.append(meaningful[0])              # first word alone

        # Acronyms from BOTH the full and the filtered word list, so
        # "Boston Consulting Group" -> bcg and "Johnson Johnson" -> jj
        for wl in (words, meaningful):
            if len(wl) >= 2:
                acr = "".join(w[0] for w in wl)
                if 2 <= len(acr) <= 5:
                    out.append(acr)

    # "and" inside a joined slug is often just dropped: sandpglobal -> spglobal
    for c in list(out):
        stripped = c.replace("and", "")
        if len(stripped) >= 2 and stripped != c:
            out.append(stripped)

    seen, uniq = set(), []
    for c in out:
        c = re.sub(r"-{2,}", "-", c).strip("-")
        if not c or len(c) < 2 or c in seen:
            continue
        if c in STOPWORDS:
            continue
        seen.add(c)
        uniq.append(c)

    # Keep the hint first; otherwise try long/specific forms before short
    # acronyms, which are cheap to generate but usually wrong.
    def rank(c):
        if hint and c == hint:
            return (0, 0, 0)
        if len(c) <= 2:
            return (3, 0, len(c))
        if len(c) <= 4 and "-" not in c:
            return (2, 0, -len(c))
        # joined forms are more common than hyphenated on most boards
        return (1, 1 if "-" in c else 0, -len(c))

    uniq.sort(key=rank)
    return uniq[:MAX_CANDIDATES]


# ------------------------------------------------------------------- probes
# Each returns (n_jobs, sample_titles) on success, or None.


def _titles(items, key, n=3):
    out = []
    for it in items[:n]:
        t = it.get(key) if isinstance(it, dict) else None
        if t:
            out.append(str(t)[:60])
    return out


def probe_greenhouse(slug):
    r = requests.get(
        f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false",
        headers=UA, timeout=TIMEOUT)
    if r.status_code != 200:
        return None
    jobs = r.json().get("jobs")
    if jobs is None:
        return None
    return len(jobs), _titles(jobs, "title")


def probe_lever(slug):
    r = requests.get(f"https://api.lever.co/v0/postings/{slug}?mode=json",
                     headers=UA, timeout=TIMEOUT)
    if r.status_code != 200:
        return None
    data = r.json()
    if not isinstance(data, list):
        return None
    return len(data), _titles(data, "text")


def probe_ashby(slug):
    r = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                     headers=UA, timeout=TIMEOUT)
    if r.status_code != 200:
        return None
    jobs = r.json().get("jobs")
    if jobs is None:
        return None
    return len(jobs), _titles(jobs, "title")


def probe_smartrecruiters(slug):
    r = requests.get(
        f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=10",
        headers=UA, timeout=TIMEOUT)
    if r.status_code != 200:
        return None
    data = r.json()
    if "content" not in data:
        return None
    return data.get("totalFound", 0), _titles(data["content"], "name")


def probe_workable(slug):
    r = requests.get(
        f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true",
        headers=UA, timeout=TIMEOUT)
    if r.status_code != 200:
        return None
    jobs = r.json().get("jobs")
    if jobs is None:
        return None
    return len(jobs), _titles(jobs, "title")


def probe_bamboohr(slug):
    r = requests.get(f"https://{slug}.bamboohr.com/careers/list",
                     headers=UA, timeout=TIMEOUT)
    if r.status_code != 200:
        return None
    res = r.json().get("result")
    if res is None:
        return None
    return len(res), _titles(res, "jobOpeningName")


def probe_recruitee(slug):
    r = requests.get(f"https://{slug}.recruitee.com/api/offers/",
                     headers=UA, timeout=TIMEOUT)
    if r.status_code != 200:
        return None
    offers = r.json().get("offers")
    if offers is None:
        return None
    return len(offers), _titles(offers, "title")


PROBES = [
    ("greenhouse", probe_greenhouse),
    ("lever", probe_lever),
    ("ashby", probe_ashby),
    ("smartrecruiters", probe_smartrecruiters),
    ("workable", probe_workable),
    ("bamboohr", probe_bamboohr),
    ("recruitee", probe_recruitee),
]


def resolve_one(name, hint=None, verbose=True):
    """Try every (candidate, board) pair. Return first solid hit."""
    for slug in candidates(name, hint):
        for board, fn in PROBES:
            try:
                hit = fn(slug)
            except requests.RequestException:
                hit = None
            except (ValueError, KeyError):
                hit = None
            time.sleep(DELAY)
            if hit and hit[0] > 0:
                n, samples = hit
                if verbose:
                    print(f"    ✓ {board}/{slug} — {n} open")
                    for s in samples:
                        print(f"        {s}")
                return {"board": board, "slug": slug, "open_jobs": n,
                        "samples": samples, "confidence": "verified"}
    return None


# ------------------------------------------------------------------- main


def parse_workday_url(url):
    """
    Fortune 500 companies are overwhelmingly on Workday, and Workday configs
    can't be guessed — tenant, cluster number, and site name all vary. But they
    ARE all visible in the careers URL. Paste it, get a config entry.

    https://acme.wd5.myworkdayjobs.com/en-US/External/job/...
              ^tenant ^wd            ^site
    """
    m = re.search(r"https?://([\w-]+)\.wd(\d+)\.myworkdayjobs\.com/(?:([\w-]{2,5})/)?([\w-]+)", url)
    if not m:
        return None
    tenant, wd, maybe_locale, site = m.groups()
    # the segment after the host is either a locale (en-US) or the site name
    if maybe_locale and not re.fullmatch(r"[a-z]{2}(-[A-Za-z]{2,4})?", maybe_locale):
        site = maybe_locale
    return {"board": "workday", "tenant": tenant, "wd": int(wd),
            "site": site, "search": "intern", "confidence": "parsed-from-url"}


def verify_workday(cfg):
    """Confirm a parsed Workday config actually returns postings."""
    tenant, wd, site = cfg["tenant"], cfg["wd"], cfg["site"]
    url = f"https://{tenant}.wd{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    try:
        r = requests.post(url, json={"appliedFacets": {}, "limit": 20, "offset": 0,
                                     "searchText": cfg.get("search", "intern")},
                          headers={**UA, "Accept": "application/json"}, timeout=TIMEOUT)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        data = r.json()
        return data.get("total", 0), [p.get("title", "")[:60]
                                      for p in data.get("jobPostings", [])[:3]]
    except (requests.RequestException, ValueError) as e:
        return None, f"{type(e).__name__}"


def load_cache():
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def save_cache(c):
    CACHE.write_text(json.dumps(c, indent=1, sort_keys=True))


def write_config(cache):
    """Merge resolved companies into the config.json internship_watch.py reads."""
    existing = json.loads(OUT_CONFIG.read_text()) if OUT_CONFIG.exists() else {}
    companies = []
    for name, rec in sorted(cache.items()):
        board = rec.get("board")
        if not board:
            continue
        if board == "workday":
            companies.append({"board": "workday", "name": name,
                              "tenant": rec["tenant"], "wd": rec["wd"],
                              "site": rec["site"], "search": rec.get("search", "intern")})
        elif board == "eightfold":
            companies.append({"board": "eightfold", "name": name,
                              "slug": rec["slug"], "domain": rec.get("domain")})
        else:
            companies.append({"board": board, "slug": rec["slug"], "name": name})
    companies.append({
        "board": "usajobs", "keyword": "intern", "name": "US Federal",
        "locations": ["New York, New York", "Newark, New Jersey",
                      "Jersey City, New Jersey"],
    })
    existing["companies"] = companies
    OUT_CONFIG.write_text(json.dumps(existing, indent=2))
    print(f"\nwrote {OUT_CONFIG} with {len(companies)} entries")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", action="append", help="resolve one category (repeatable)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--priority", type=int, help="only categories at or above this priority (1=highest)")
    ap.add_argument("--report", action="store_true", help="summarize cache, no network")
    ap.add_argument("--write-config", action="store_true")
    ap.add_argument("--retry-failed", action="store_true", help="re-probe previous misses")
    ap.add_argument("--workday", nargs=2, metavar=("NAME", "URL"),
                    help='add a Workday company: --workday "Merck" "https://merck.wd5.myworkdayjobs.com/en-US/SearchJobs"')
    ap.add_argument("--force", action="store_true",
                    help="probe slugs even for categories flagged expect_workday")
    args = ap.parse_args()

    targets = json.loads(TARGETS.read_text())
    cache = load_cache()

    if args.workday:
        name, url = args.workday
        cfg = parse_workday_url(url)
        if not cfg:
            sys.exit("couldn't parse that as a myworkdayjobs.com URL")
        print(f"parsed: tenant={cfg['tenant']} wd={cfg['wd']} site={cfg['site']}")
        n, samples = verify_workday(cfg)
        if n is None:
            print(f"  ✗ verification failed ({samples}) — site name is probably wrong.")
            print("    Open the careers page, check the path segment after the locale.")
            return
        print(f"  ✓ {n} postings match 'intern'")
        for t in samples:
            print(f"      {t}")
        cache[name] = cfg
        save_cache(cache)
        print(f"\nsaved to cache as '{name}'")
        return

    if args.report or args.write_config:
        hits = {k: v for k, v in cache.items() if v.get("board")}
        misses = [k for k, v in cache.items() if not v.get("board")]
        print(f"resolved: {len(hits)}   unresolved: {len(misses)}")
        by_board = {}
        for v in hits.values():
            by_board[v["board"]] = by_board.get(v["board"], 0) + 1
        for b, n in sorted(by_board.items(), key=lambda x: -x[1]):
            print(f"  {b:<18} {n}")
        if misses:
            print(f"\nunresolved ({len(misses)}) — check careers page with discover.py:")
            for m in sorted(misses):
                print(f"  {m}")
        if args.write_config:
            write_config(cache)
        return

    cats = targets["categories"]
    if args.all:
        chosen = list(cats)
    elif args.category:
        chosen = args.category
    elif args.priority:
        chosen = [k for k, v in cats.items() if v.get("priority", 3) <= args.priority]
    else:
        print("pick one: --category NAME | --priority N | --all\n")
        w = max(len(k) for k in cats)
        for k, v in cats.items():
            print(f"  {k:<{w}}  p{v.get('priority',3)}  {len(v['companies']):>3}  {v['label']}")
        return

    for cat in chosen:
        if cat not in cats:
            print(f"! unknown category '{cat}'")
            continue
        block = cats[cat]
        print(f"\n{'='*66}\n{block['label']}  ({len(block['companies'])} companies)")
        if block.get("note"):
            print(f"  {block['note']}")
        print("=" * 66)

        if block.get("expect_workday") and not args.force:
            print("  These are almost all on Workday, which can't be resolved by")
            print("  guessing slugs. For each one, open their careers page and run:")
            print('    python resolve.py --workday "Name" "<myworkdayjobs URL>"')
            print("  (--force to probe anyway)")
            for c in block["companies"]:
                loc = f"  — {c['note']}" if c.get("note") else ""
                print(f"    · {c['name']}{loc}")
            continue

        for c in block["companies"]:
            name = c["name"]
            if name in cache and not (args.retry_failed and not cache[name].get("board")):
                rec = cache[name]
                mark = f"{rec['board']}/{rec['slug']}" if rec.get("board") else "unresolved"
                print(f"  · {name:<34} (cached: {mark})")
                continue
            print(f"  ? {name}")
            rec = resolve_one(name, c.get("hint"))
            if rec is None:
                print("    ✗ no ATS found — likely custom site; run discover.py on their careers page")
                rec = {"board": None, "note": c.get("note", "")}
            if c.get("note"):
                rec["note"] = c["note"]
            cache[name] = rec
            save_cache(cache)

    save_cache(cache)
    print(f"\ncache: {CACHE}")
    print("next: python resolve.py --report      (see what landed)")
    print("      python resolve.py --write-config")


if __name__ == "__main__":
    main()
