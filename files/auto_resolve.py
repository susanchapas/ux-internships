#!/usr/bin/env python3
"""
auto_resolve.py — find and VERIFY the ATS endpoint for every unresolved company.

Strategy per company:
  1. SNIFF   fetch the careers page(s), regex for ATS fingerprints in the HTML
             (Workday, Greenhouse, Lever, Ashby, SmartRecruiters, Workable,
              Recruitee, Eightfold, iCIMS, Taleo, Oracle, Phenom, Jobvite...)
  2. GUESS   if sniffing found nothing, probe likely slugs against each ATS's
             public JSON API (company name normalized a few different ways)
  3. BRUTE   for Workday only: probe tenant x wd-host x site-name combinations
             (--deep). Workday tenants are unguessable by hand but trivial to
             brute force because the CXS endpoint is public.
  4. VERIFY  every candidate is confirmed by hitting the real jobs API and
             counting postings. Nothing is written unless it returns jobs.

Outputs (in --out dir):
  resolved.json      machine-readable, keyed by company
  resolved.md        human-readable table
  unresolved.md      what still needs a human, with the careers URL to check
  commands.sh        ready-to-run `python resolve.py --workday ...` lines

Usage:
  pip install requests
  python auto_resolve.py                 # normal pass
  python auto_resolve.py --deep          # + Workday brute force (slower)
  python auto_resolve.py --only "Pfizer,Merck"
  python auto_resolve.py --priority 1
  python auto_resolve.py --resume        # skip companies already in resolved.json
"""

import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run:  pip install requests")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/json,*/*"}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

PRINT_LOCK = threading.Lock()


def log(*a):
    with PRINT_LOCK:
        print(*a, flush=True)


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------

def get(url, timeout=20, **kw):
    try:
        return SESSION.get(url, timeout=timeout, allow_redirects=True, **kw)
    except Exception:
        return None


def post_json(url, payload, timeout=20):
    try:
        return SESSION.post(
            url, json=payload, timeout=timeout,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
    except Exception:
        return None


# --------------------------------------------------------------------------
# ATS fingerprints found in careers-page HTML
# --------------------------------------------------------------------------

PATTERNS = [
    # Workday: tenant.wdN.myworkdayjobs.com[/en-US]/SiteName
    ("workday", re.compile(
        r"https?://([a-z0-9][a-z0-9\-]*)\.(wd\d+)\.(myworkdayjobs|myworkdaysite)\.com"
        r"(?:/wday/cxs/[^/]+)?(?:/[a-z]{2}-[A-Z]{2})?/([A-Za-z0-9_\-]+)", re.I)),
    ("greenhouse", re.compile(
        r"(?:job-)?boards(?:-api)?\.greenhouse\.io/(?:embed/job_board\?for=)?([a-z0-9_\-]+)", re.I)),
    ("greenhouse", re.compile(r"greenhouse\.io/embed/job_board/js\?for=([a-z0-9_\-]+)", re.I)),
    ("lever", re.compile(r"jobs\.(?:eu\.)?lever\.co/([a-z0-9\-\.]+)", re.I)),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/([a-z0-9\-\.]+)", re.I)),
    ("smartrecruiters", re.compile(
        r"(?:careers|jobs|api)\.smartrecruiters\.com/(?:v1/companies/)?([A-Za-z0-9_\-]+)", re.I)),
    ("workable", re.compile(r"apply\.workable\.com/([a-z0-9\-]+)", re.I)),
    ("recruitee", re.compile(r"([a-z0-9\-]+)\.recruitee\.com", re.I)),
    ("eightfold", re.compile(r"([a-z0-9\-]+)\.eightfold\.ai", re.I)),
    ("rippling", re.compile(r"([a-z0-9\-]+)\.rippling-ats\.com", re.I)),
    ("jobvite", re.compile(r"jobs\.jobvite\.com/([a-z0-9\-]+)", re.I)),
    ("bamboohr", re.compile(r"([a-z0-9\-]+)\.bamboohr\.com/(?:careers|jobs)", re.I)),
    ("paylocity", re.compile(r"recruiting\.paylocity\.com/recruiting/jobs/All/([a-z0-9\-]+)", re.I)),
    ("teamtailor", re.compile(r"([a-z0-9\-]+)\.teamtailor\.com", re.I)),
    # scrape-only platforms: capture the host so change-detection can be pointed at it
    ("icims", re.compile(r"(https?://[a-z0-9\-]+\.icims\.com/jobs[^\"'\s]*)", re.I)),
    ("taleo", re.compile(r"(https?://[a-z0-9\-\.]*taleo\.net/[^\"'\s]*)", re.I)),
    ("oracle", re.compile(r"(https?://[a-z0-9\-\.]+\.oraclecloud\.com/hcmUI/CandidateExperience[^\"'\s]*)", re.I)),
    ("phenom", re.compile(r"(https?://[a-z0-9\-\.]+/(?:widgets|search-results)\?[^\"'\s]*)", re.I)),
]

# tokens that show up inside Workday/GH URLs but are never a real slug/site
JUNK = {"www", "en", "en-us", "static", "cdn", "assets", "img", "images", "app",
        "api", "js", "css", "login", "signin", "home", "index", "null", "undefined",
        "embed", "job_board", "jobs", "job", "boards", "v1", "search", "widget"}


def sniff(html):
    """Return list of (ats, capture...) tuples found in a blob of HTML."""
    hits = []
    for ats, rx in PATTERNS:
        for m in rx.finditer(html):
            groups = tuple(g for g in m.groups() if g)
            if not groups:
                continue
            if groups[0].lower() in JUNK:
                continue
            hits.append((ats, groups))
    # de-dupe, preserve order
    seen, out = set(), []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


# --------------------------------------------------------------------------
# Careers-page discovery
# --------------------------------------------------------------------------

CAREER_PATHS = [
    "/careers", "/careers/", "/jobs", "/company/careers", "/about/careers",
    "/en/careers", "/us/en/careers", "/careers/jobs", "/careers/search",
    "/about-us/careers", "/join-us", "/work-with-us", "/company/jobs",
    "/careers/open-positions", "/about/jobs",
]

CAREER_LINK_RX = re.compile(
    r'href=["\']([^"\']*(?:career|job|join-us|work-with-us|opportunit)[^"\']*)["\']', re.I)


def collect_html(domain, max_pages=8):
    """Fetch homepage + likely careers pages, follow careers links one hop."""
    blobs = []
    tried = set()

    def fetch(url):
        if url in tried or len(tried) > max_pages:
            return None
        tried.add(url)
        r = get(url)
        if r is not None and r.status_code < 400 and r.text:
            blobs.append((r.url, r.text))
            return r
        return None

    root = f"https://{domain}"
    home = fetch(root)

    # follow careers-ish links off the homepage
    if home is not None and home.text:
        links = CAREER_LINK_RX.findall(home.text)[:40]
        cands = []
        for href in links:
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = root + href
            elif not href.startswith("http"):
                continue
            if "career" in href.lower() or "/jobs" in href.lower() or "join-us" in href.lower():
                cands.append(href.split("#")[0])
        for u in list(dict.fromkeys(cands))[:4]:
            fetch(u)

    for p in CAREER_PATHS:
        if len(tried) > max_pages:
            break
        fetch(root + p)

    return blobs


# --------------------------------------------------------------------------
# Verification — every ATS below has a public JSON endpoint
# --------------------------------------------------------------------------

def v_greenhouse(slug):
    r = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false")
    if r is None or r.status_code != 200:
        return None
    try:
        n = len(r.json().get("jobs", []))
    except Exception:
        return None
    return {"ats": "greenhouse", "slug": slug, "count": n,
            "api": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
            "human": f"https://job-boards.greenhouse.io/{slug}"} if n else None


def v_lever(slug):
    r = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if r is None or r.status_code != 200:
        return None
    try:
        data = r.json()
    except Exception:
        return None
    if not isinstance(data, list) or not data:
        return None
    return {"ats": "lever", "slug": slug, "count": len(data),
            "api": f"https://api.lever.co/v0/postings/{slug}?mode=json",
            "human": f"https://jobs.lever.co/{slug}"}


def v_ashby(slug):
    r = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    if r is None or r.status_code != 200:
        return None
    try:
        n = len(r.json().get("jobs", []))
    except Exception:
        return None
    return {"ats": "ashby", "slug": slug, "count": n,
            "api": f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
            "human": f"https://jobs.ashbyhq.com/{slug}"} if n else None


def v_smartrecruiters(slug):
    r = get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=10")
    if r is None or r.status_code != 200:
        return None
    try:
        j = r.json()
        n = j.get("totalFound", len(j.get("content", [])))
    except Exception:
        return None
    return {"ats": "smartrecruiters", "slug": slug, "count": n,
            "api": f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
            "human": f"https://careers.smartrecruiters.com/{slug}"} if n else None


def v_workable(slug):
    r = get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")
    if r is None or r.status_code != 200:
        return None
    try:
        n = len(r.json().get("jobs", []))
    except Exception:
        return None
    return {"ats": "workable", "slug": slug, "count": n,
            "api": f"https://apply.workable.com/api/v1/widget/accounts/{slug}",
            "human": f"https://apply.workable.com/{slug}/"} if n else None


def v_recruitee(slug):
    r = get(f"https://{slug}.recruitee.com/api/offers/")
    if r is None or r.status_code != 200:
        return None
    try:
        n = len(r.json().get("offers", []))
    except Exception:
        return None
    return {"ats": "recruitee", "slug": slug, "count": n,
            "api": f"https://{slug}.recruitee.com/api/offers/",
            "human": f"https://{slug}.recruitee.com/"} if n else None


def v_eightfold(slug, domain=None):
    dom = domain or f"{slug}.com"
    url = (f"https://{slug}.eightfold.ai/api/apply/v2/jobs"
           f"?domain={dom}&start=0&num=10&exclude_pid=&sort_by=relevance")
    r = get(url)
    if r is None or r.status_code != 200:
        return None
    try:
        n = r.json().get("count", 0)
    except Exception:
        return None
    return {"ats": "eightfold", "slug": slug, "count": n, "api": url,
            "human": f"https://{slug}.eightfold.ai/careers"} if n else None


def v_workday(tenant, host, site, base="myworkdayjobs"):
    """host is like 'wd5'. Confirms via the public CXS jobs endpoint."""
    url = f"https://{tenant}.{host}.{base}.com/wday/cxs/{tenant}/{site}/jobs"
    r = post_json(url, {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""})
    if r is None or r.status_code != 200:
        return None
    try:
        j = r.json()
    except Exception:
        return None
    n = j.get("total")
    if not isinstance(n, int) or n <= 0:
        return None
    return {"ats": "workday", "tenant": tenant, "host": host, "site": site,
            "count": n, "api": url,
            "human": f"https://{tenant}.{host}.{base}.com/en-US/{site}",
            "resolve_url": f"https://{tenant}.{host}.{base}.com/en-US/{site}"}


VERIFIERS = {
    "greenhouse": v_greenhouse,
    "lever": v_lever,
    "ashby": v_ashby,
    "smartrecruiters": v_smartrecruiters,
    "workable": v_workable,
    "recruitee": v_recruitee,
}

SCRAPE_ONLY = {"icims", "taleo", "oracle", "phenom", "jobvite", "bamboohr",
               "paylocity", "teamtailor", "rippling"}

# Companies that run their own recruiting stack. These will never match an ATS
# fingerprint, so we point change-detection straight at the right search page.
# (URLs verified as of Aug 2026 — the script re-checks each one returns 200.)
CUSTOM_CAREERS = {
    "Amazon": "https://www.amazon.jobs/en/search?base_query=design+intern",
    "Apple": "https://jobs.apple.com/en-us/search?team=Design-DES",
    "Google": "https://www.google.com/about/careers/applications/jobs/results/?employment_type=INTERN",
    "Meta": "https://www.metacareers.com/jobs?roles[0]=Internship",
    "Microsoft": "https://jobs.careers.microsoft.com/global/en/search?lc=United%20States",
    "IBM": "https://www.ibm.com/careers/search",
    "Uber": "https://www.uber.com/us/en/careers/list/?department=Design",
    "Netflix": "https://explore.jobs.netflix.net/careers",
    "Goldman Sachs": "https://higher.gs.com/roles",
    "Morgan Stanley": "https://www.morganstanley.com/careers/career-opportunities-search",
    "JPMorgan Chase": "https://careers.jpmorgan.com/us/en/students/programs",
    "Bank of America": "https://careers.bankofamerica.com/en-us/job-search",
    "Citi": "https://jobs.citi.com/search-jobs",
    "Bloomberg": "https://careers.bloomberg.com/job/search",
    "Oracle": "https://careers.oracle.com/jobs/#en/sites/jobsearch",
    "The Walt Disney Company": "https://jobs.disneycareers.com/search-jobs",
    "Jane Street": "https://www.janestreet.com/join-jane-street/open-roles/",
    "Deloitte": "https://apply.deloitte.com/careers",
    "EY": "https://careers.ey.com/ey/search/",
    "PwC": "https://jobs.us.pwc.com/search-jobs",
    "KPMG": "https://www.kpmguscareers.com/search-jobs",
    "McKinsey": "https://www.mckinsey.com/careers/search-jobs",
    "Bain": "https://www.bain.com/careers/find-a-role/",
    "Accenture": "https://www.accenture.com/us-en/careers/jobsearch",
    "Verizon": "https://mycareer.verizon.com/jobs/",
    "AT&T": "https://www.att.jobs/search-jobs",
    "T-Mobile": "https://careers.t-mobile.com/search-jobs",
    "Shopify": "https://www.shopify.com/careers/search",
    "Pentagram": "https://www.pentagram.com/careers",
}


# --------------------------------------------------------------------------
# Slug guessing
# --------------------------------------------------------------------------

def name_variants(name, domain):
    base = re.sub(r"[^a-z0-9\s\-]", "", name.lower())
    base = base.replace("&", "and")
    words = base.split()
    stop = {"inc", "llc", "co", "corp", "corporation", "company", "the",
            "group", "holdings", "usa", "pbc", "associates"}
    core = [w for w in words if w not in stop]
    joined = "".join(core)
    hyph = "-".join(core)
    dom = domain.split(".")[0]
    out = [joined, hyph, dom, core[0] if core else joined,
           joined + "careers", "".join(words), "-".join(words)]
    seen, res = set(), []
    for v in out:
        v = v.strip("-")
        if v and v not in seen and len(v) > 1:
            seen.add(v)
            res.append(v)
    return res


WD_HOSTS = ["wd1", "wd5", "wd3", "wd2", "wd12", "wd101", "wd103", "wd10",
            "wd102", "wd104", "wd105", "wd502", "wd505"]

WD_SITES = ["External", "External_Career_Site", "ExternalCareerSite", "Careers",
            "careers", "External_Careers", "external", "External_Site",
            "ExternalSite", "Global_Careers", "GlobalCareers", "CorporateCareers",
            "Search", "jobs", "Jobs", "PublicJobs", "External_Experienced",
            "external_experienced", "Professional_Careers", "USA_Careers"]


def workday_brute(name, domain, deep=False, workers=24):
    tenants = name_variants(name, domain)[:4]
    hosts = WD_HOSTS if deep else WD_HOSTS[:6]
    sites = WD_SITES if deep else WD_SITES[:8]
    combos = [(t, h, s) for t in tenants for h in hosts for s in sites]
    found = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(v_workday, t, h, s): (t, h, s) for t, h, s in combos}
        for f in as_completed(futs):
            try:
                r = f.result()
            except Exception:
                r = None
            if r:
                found.append(r)
                for other in futs:
                    other.cancel()
                break
    return found[0] if found else None


def guess_standard(name, domain, workers=12):
    """Probe greenhouse/lever/ashby/smartrecruiters/workable with name variants."""
    variants = name_variants(name, domain)
    jobs = []
    for ats in ("greenhouse", "lever", "ashby", "smartrecruiters", "workable"):
        for v in variants:
            jobs.append((ats, v))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(VERIFIERS[a], v): (a, v) for a, v in jobs}
        for f in as_completed(futs):
            try:
                r = f.result()
            except Exception:
                r = None
            if r:
                return r
    return None


# --------------------------------------------------------------------------
# Per-company pipeline
# --------------------------------------------------------------------------

def resolve_company(row, deep=False):
    name, domain, cat, pri, hint = row
    rec = {"name": name, "domain": domain, "category": cat, "priority": pri,
           "hint": hint, "status": "unresolved", "careers_seen": []}

    if hint == "defunct":
        rec["status"] = "skip"
        rec["note"] = "company likely defunct/acquired — verify before spending time"
        return rec
    if hint == "manual":
        rec["status"] = "manual"
        rec["note"] = "no ATS; apply direct"
        rec["human"] = CUSTOM_CAREERS.get(name, f"https://{domain}")
        return rec

    # Known in-house recruiting stacks: skip ATS discovery, hand back the
    # search page for change-detection (after confirming it still loads).
    if hint == "custom" and name in CUSTOM_CAREERS:
        url = CUSTOM_CAREERS[name]
        r = get(url)
        rec["status"] = "scrape"
        rec["ats"] = "custom"
        rec["human"] = url
        rec["note"] = ("in-house ATS, no public JSON board — point change-detection here"
                       + ("" if (r is not None and r.status_code < 400) else " (URL did not load, re-check)"))
        return rec

    if hint == "eightfold":
        r = v_eightfold(domain.split(".")[0], domain)
        if r:
            rec.update(r)
            rec["status"] = "resolved"
            rec["method"] = "hint"
            return rec

    # 1. sniff
    blobs = collect_html(domain)
    rec["careers_seen"] = [u for u, _ in blobs][:6]
    all_hits = []
    for _, html in blobs:
        all_hits += sniff(html)

    # prefer the hinted ATS if we have one
    def rank(h):
        return 0 if (hint and h[0] == hint) else 1
    all_hits.sort(key=rank)

    for ats, groups in all_hits:
        if ats == "workday":
            tenant, host, base, site = groups[0], groups[1], groups[2], groups[3]
            if site.lower() in JUNK or site.lower().startswith("wday"):
                continue
            r = v_workday(tenant.lower(), host.lower(), site, base.lower())
            if r:
                rec.update(r)
                rec["status"] = "resolved"
                rec["method"] = "sniff"
                return rec
        elif ats in VERIFIERS:
            r = VERIFIERS[ats](groups[0].lower())
            if r:
                rec.update(r)
                rec["status"] = "resolved"
                rec["method"] = "sniff"
                return rec
        elif ats == "eightfold":
            r = v_eightfold(groups[0].lower(), domain)
            if r:
                rec.update(r)
                rec["status"] = "resolved"
                rec["method"] = "sniff"
                return rec
        elif ats in SCRAPE_ONLY:
            # remember it, but keep looking for something with a real API
            rec.setdefault("scrape_candidate", {"ats": ats, "url": groups[0]})

    # 2. guess standard ATS slugs
    r = guess_standard(name, domain)
    if r:
        rec.update(r)
        rec["status"] = "resolved"
        rec["method"] = "guess"
        return rec

    # 3. workday brute force
    if hint == "workday" or deep:
        r = workday_brute(name, domain, deep=deep)
        if r:
            rec.update(r)
            rec["status"] = "resolved"
            rec["method"] = "brute"
            return rec

    # 4. fall back to scrape target
    if "scrape_candidate" in rec:
        rec["status"] = "scrape"
        rec["ats"] = rec["scrape_candidate"]["ats"]
        rec["human"] = rec["scrape_candidate"]["url"]
        rec["note"] = "no public JSON API — use change-detection on this URL"
        return rec

    rec["note"] = "check careers page by hand"
    return rec


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def write_reports(records, outdir):
    os.makedirs(outdir, exist_ok=True)

    with open(os.path.join(outdir, "resolved.json"), "w") as f:
        json.dump({r["name"]: r for r in records}, f, indent=2)

    res = [r for r in records if r["status"] == "resolved"]
    scr = [r for r in records if r["status"] == "scrape"]
    unr = [r for r in records if r["status"] in ("unresolved", "manual", "skip")]

    res.sort(key=lambda r: (r["priority"], r["name"]))
    lines = ["# Resolved", "",
             f"{len(res)} companies verified against a live jobs API.", "",
             "| Company | Pri | ATS | Endpoint | Open roles | How |",
             "|---|---|---|---|---|---|"]
    for r in res:
        ident = r.get("slug") or f"{r.get('tenant')}/{r.get('host')}/{r.get('site')}"
        lines.append(
            f"| {r['name']} | {r['priority']} | {r['ats']} | `{ident}` | "
            f"{r.get('count','?')} | {r.get('method','')} |")
    lines += ["", "## Full endpoints", ""]
    for r in res:
        lines.append(f"- **{r['name']}** — {r.get('human','')}")
    with open(os.path.join(outdir, "resolved.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

    lines = ["# Needs a human", ""]
    if scr:
        lines += ["## Scrape / change-detection only (no public API)", "",
                  "| Company | Pri | Platform | URL |", "|---|---|---|---|"]
        for r in sorted(scr, key=lambda r: (r["priority"], r["name"])):
            lines.append(f"| {r['name']} | {r['priority']} | {r.get('ats','?')} | {r.get('human','')} |")
        lines.append("")
    if unr:
        lines += ["## Unresolved", "",
                  "| Company | Pri | Domain | Pages checked | Note |", "|---|---|---|---|---|"]
        for r in sorted(unr, key=lambda r: (r["priority"], r["name"])):
            seen = " ".join(r.get("careers_seen", [])[:2]) or "-"
            lines.append(f"| {r['name']} | {r['priority']} | {r['domain']} | {seen} | {r.get('note','')} |")
    with open(os.path.join(outdir, "unresolved.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

    cmds = ["#!/usr/bin/env bash", "set -e", ""]
    for r in res:
        if r["ats"] == "workday":
            cmds.append(f'python resolve.py --workday "{r["name"]}" "{r["resolve_url"]}"')
    cmds += ["", "python resolve.py --write-config", "python internship_watch.py --dry-run"]
    with open(os.path.join(outdir, "commands.sh"), "w") as f:
        f.write("\n".join(cmds) + "\n")

    log(f"\n  resolved: {len(res)}   scrape-only: {len(scr)}   still open: {len(unr)}")
    log(f"  wrote {outdir}/resolved.json, resolved.md, unresolved.md, commands.sh")


# --------------------------------------------------------------------------

def load_seeds(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            while len(parts) < 5:
                parts.append("")
            rows.append((parts[0].strip(), parts[1].strip(), parts[2].strip(),
                         int(parts[3] or 3), parts[4].strip()))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="seeds.tsv")
    ap.add_argument("--out", default="out")
    ap.add_argument("--workers", type=int, default=6,
                    help="companies in parallel (keep low; each spawns its own probes)")
    ap.add_argument("--deep", action="store_true", help="wider Workday brute force")
    ap.add_argument("--priority", type=int, default=0, help="only this priority tier")
    ap.add_argument("--only", default="", help="comma-separated company names")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    rows = load_seeds(args.seeds)
    if args.priority:
        rows = [r for r in rows if r[3] == args.priority]
    if args.only:
        want = {s.strip().lower() for s in args.only.split(",")}
        rows = [r for r in rows if r[0].lower() in want]

    done = {}
    path = os.path.join(args.out, "resolved.json")
    if args.resume and os.path.exists(path):
        done = json.load(open(path))
        before = len(rows)
        rows = [r for r in rows if done.get(r[0], {}).get("status") != "resolved"]
        log(f"resume: skipping {before - len(rows)} already resolved")

    log(f"resolving {len(rows)} companies with {args.workers} workers"
        f"{' (deep)' if args.deep else ''}\n")

    records = list(done.values()) if args.resume else []
    names_done = {r["name"] for r in records}
    records = [r for r in records if r["name"] not in {x[0] for x in rows}]

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(resolve_company, r, args.deep): r[0] for r in rows}
        for i, f in enumerate(as_completed(futs), 1):
            name = futs[f]
            try:
                rec = f.result()
            except Exception as e:
                rec = {"name": name, "status": "unresolved", "priority": 3,
                       "domain": "", "category": "", "note": f"error: {e}"}
            records.append(rec)
            mark = {"resolved": "OK  ", "scrape": "SCR ", "manual": "MAN ",
                    "skip": "SKIP"}.get(rec["status"], "--  ")
            detail = rec.get("human", rec.get("note", ""))
            log(f"[{i:3}/{len(rows)}] {mark} {name:<32} {detail[:70]}")
            if i % 25 == 0:
                write_reports(records, args.out)

    write_reports(records, args.out)
    log(f"\ndone in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
