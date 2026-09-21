#!/usr/bin/env python3
"""Inject pre-baked scan data into Vite's static build for GitHub Pages."""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from internship_watch import (
    load_json, compile_filters, compile_discovery_filters, classify_match, CONFIG_PATH,
    BOARD_FETCHERS, fetch_workday, fetch_usajobs,
)

HERE = Path(__file__).parent
DIST_DIR = HERE / "dist"
INDEX = DIST_DIR / "index.html"
EARLY_CAREER_SOURCES = HERE / "early_career_sources.json"

LEVEL_RULES = [
    ("intern",     re.compile(r"\bintern(?:ship)?\b|\bco-?op\b|\bextern(?:ship)?\b|\btrainee\b|\bpracticum\b", re.I)),
    ("fellow",     re.compile(r"\bfellow(?:ship)?\b", re.I)),
    ("apprentice", re.compile(r"\bapprentice(?:ship)?\b", re.I)),
    ("entry",      re.compile(r"\b(?:associate|junior|jr\.?|entry[\s-]level|new[\s-]grad|analyst\s*I\b)", re.I)),
    ("manager+",   re.compile(r"\b(?:manager|director|vp\b|vice\s*president|head\s+of|chief|president)\b", re.I)),
    ("senior+",    re.compile(r"\b(?:senior|sr\.?|lead|staff|principal)\b", re.I)),
]

HOURLY_RE = re.compile(r"(?:per|/|an?)\s*(?:hour|hr)\b", re.I)
SALARY_RE = re.compile(r"(?:per|/|an?)\s*(?:year|yr|annum|annually)\b", re.I)
AMOUNT_RE = re.compile(r"\$\s*([\d,]+)")


def classify(job):
    title = job.get("title") or ""
    level = "mid"
    for lbl, pat in LEVEL_RULES:
        if pat.search(title):
            level = lbl
            break
    job["level"] = level

    pay = job.get("pay") or ""
    if not pay:
        job["pay_type"] = ""
    elif HOURLY_RE.search(pay):
        job["pay_type"] = "hourly"
    elif SALARY_RE.search(pay):
        job["pay_type"] = "salary"
    else:
        amounts = AMOUNT_RE.findall(pay)
        if amounts:
            val = int(amounts[0].replace(",", ""))
            job["pay_type"] = "salary" if val > 1000 else "hourly"
        else:
            job["pay_type"] = ""


SCAN_CACHE = HERE / "_scan_results.json"


def run_scan():
    cached = load_json(SCAN_CACHE, None)
    if cached:
        jobs = cached["jobs"]
        for j in jobs:
            j["is_new"] = False
            classify(j)
        print(f"Loaded {len(jobs)} jobs from cached scan results")
        return jobs, cached.get("errors", []), cached["companies_scanned"]

    cfg = load_json(CONFIG_PATH, None)
    if cfg is None:
        sys.exit("missing config.json")

    title_inc, title_exc, loc_inc, loc_exc = compile_filters(cfg)
    description_inc, adjacent_inc, early_career_inc = compile_discovery_filters(cfg)
    all_jobs = []
    errors = []

    for i, entry in enumerate(cfg["companies"]):
        board = entry["board"]
        company = entry.get("name", entry.get("slug", board))
        print(f"  [{i+1}/{len(cfg['companies'])}] {company} ({board})")

        try:
            if board in BOARD_FETCHERS:
                jobs = list(BOARD_FETCHERS[board](entry["slug"], company))
            elif board == "workday":
                jobs = list(fetch_workday(entry, company))
            elif board == "usajobs":
                jobs = list(fetch_usajobs(entry))
            else:
                continue
        except Exception as e:
            errors.append({"company": company, "error": f"{type(e).__name__}: {e}"})
            print(f"    ERROR: {e}")
            continue

        hits = []
        for job in jobs:
            lane = classify_match(job, title_inc, title_exc, loc_inc, loc_exc, description_inc, adjacent_inc, early_career_inc, cfg.get("allow_all_remote", False))
            if lane:
                job["match_lane"] = lane
                hits.append(job)
        for h in hits:
            h["is_new"] = False
            classify(h)
        all_jobs.extend(hits)
        print(f"    {len(jobs)} open, {len(hits)} match")
        time.sleep(0.4)

    print(f"\n{len(all_jobs)} total matches, {len(errors)} errors")
    return all_jobs, errors, len(cfg["companies"])


def build():
    print("Scanning job boards...")
    jobs, errors, company_count = run_scan()
    now = datetime.now(timezone.utc).isoformat()

    static_data = json.dumps({
        "jobs": jobs,
        "errors": errors,
        "companies_scanned": company_count,
        "updated_at": now,
    }, default=str, separators=(",", ":"))

    cfg = load_json(CONFIG_PATH, None)
    config_json = json.dumps(cfg, separators=(",", ":"))
    early_career = load_json(EARLY_CAREER_SOURCES, {"sources": []})
    early_career_json = json.dumps(early_career.get("sources", []), separators=(",", ":"))

    if not INDEX.exists():
        sys.exit("missing dist/index.html; run `npm run build` before `python build_static.py`")

    # Escape '<' so data from job descriptions cannot terminate the script tag.
    def safe_for_script(value):
        return value.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    static_inject = (
        '<script id="static-data">\n'
        f"window.STATIC_DATA={safe_for_script(static_data)};\n"
        f"window.STATIC_CONFIG={safe_for_script(config_json)};\n"
        f"window.EARLY_CAREER_SOURCES={safe_for_script(early_career_json)};\n"
        "</script>"
    )
    html = INDEX.read_text()
    html = re.sub(r'<script id="static-data">.*?</script>\s*', "", html, flags=re.DOTALL)
    if "</head>" not in html:
        sys.exit("Vite output is missing a closing </head> tag")
    html = html.replace("</head>", f"{static_inject}</head>", 1)

    INDEX.write_text(html)
    # GitHub Pages serves this fallback for direct visits to client-side routes.
    (DIST_DIR / "404.html").write_text(html)
    print(f"\nInjected {len(jobs)} jobs into dist/index.html")


if __name__ == "__main__":
    build()
