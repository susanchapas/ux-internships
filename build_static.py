#!/usr/bin/env python3
"""Build a static dashboard.html with pre-baked scan data for GitHub Pages."""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from internship_watch import (
    load_json, compile_filters, matches, CONFIG_PATH,
    BOARD_FETCHERS, fetch_workday, fetch_usajobs,
)
from web import classify

HERE = Path(__file__).parent
DASHBOARD = HERE / "dashboard.html"
OUT_DIR = HERE / "_site"

LEVEL_RULES = [
    ("intern",     re.compile(r"\bintern(?:ship)?\b|\bco-?op\b|\bextern(?:ship)?\b|\btrainee\b|\bpracticum\b", re.I)),
    ("fellow",     re.compile(r"\bfellow(?:ship)?\b", re.I)),
    ("apprentice", re.compile(r"\bapprentice(?:ship)?\b", re.I)),
    ("entry",      re.compile(r"\b(?:associate|junior|jr\.?|entry[\s-]level|new[\s-]grad|analyst\s*I\b)", re.I)),
    ("manager+",   re.compile(r"\b(?:manager|director|vp\b|vice\s*president|head\s+of|chief|president)\b", re.I)),
    ("senior+",    re.compile(r"\b(?:senior|sr\.?|lead|staff|principal)\b", re.I)),
]


def run_scan():
    cfg = load_json(CONFIG_PATH, None)
    if cfg is None:
        sys.exit("missing config.json")

    title_inc, title_exc, loc_inc = compile_filters(cfg)
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

        hits = [j for j in jobs if matches(j, title_inc, title_exc, loc_inc)]
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
    }, default=str)

    html = DASHBOARD.read_text()

    static_script = f"<script>const STATIC_DATA = {static_data};</script>\n<script>"
    html = html.replace("<script>", static_script, 1)

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "index.html").write_text(html)
    print(f"\nWrote _site/index.html ({len(jobs)} jobs baked in)")


if __name__ == "__main__":
    build()
