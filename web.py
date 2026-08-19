#!/usr/bin/env python3
"""web.py — browser dashboard for internship_watch. Run: python web.py"""

import json
import re
import sys
import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from internship_watch import (
    load_json, compile_filters, matches, CONFIG_PATH,
    fetch_greenhouse, fetch_lever, fetch_ashby, fetch_smartrecruiters,
    fetch_workday, fetch_usajobs, BOARD_FETCHERS,
)
import db

HERE = Path(__file__).parent
DASHBOARD = HERE / "dashboard.html"

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

    emp = (job.get("commitment") or job.get("employment_type") or "").lower()
    tl = title.lower()
    if re.search(r"\bpart[\s-]?time\b", tl) or "part-time" in emp or "parttime" in emp:
        job["schedule"] = "part-time"
    elif re.search(r"\bfull[\s-]?time\b", tl) or "full-time" in emp or "fulltime" in emp:
        job["schedule"] = "full-time"
    elif "contract" in emp or "temporary" in emp or re.search(r"\bcontract\b", tl):
        job["schedule"] = "contract"
    else:
        job["schedule"] = ""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._serve_dashboard()
        elif self.path == "/api/scan":
            self._run_scan()
        elif self.path == "/api/applications":
            self._json_response(db.list_applications())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/applications":
            body = self._read_body()
            app_id = db.add_application(
                company=body.get("company", ""),
                title=body.get("title", ""),
                url=body.get("url", ""),
                location=body.get("location", ""),
                pay=body.get("pay", ""),
                status=body.get("status", "saved"),
                notes=body.get("notes", ""),
                job_id=body.get("job_id"),
                applied_at=body.get("applied_at", ""),
            )
            self._json_response({"id": app_id})
        else:
            self.send_error(404)

    def do_PUT(self):
        if self.path.startswith("/api/applications/"):
            app_id = int(self.path.split("/")[-1])
            body = self._read_body()
            db.update_application(app_id, **body)
            self._json_response({"ok": True})
        else:
            self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith("/api/applications/"):
            app_id = int(self.path.split("/")[-1])
            db.delete_application(app_id)
            self._json_response({"ok": True})
        else:
            self.send_error(404)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _json_response(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_dashboard(self):
        html = DASHBOARD.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def _run_scan(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        cfg = load_json(CONFIG_PATH, None)
        if cfg is None:
            self._sse("error", {"company": "—", "error": "config.json not found"})
            self._sse("done", {"total_matches": 0, "new": 0, "companies_scanned": 0, "errors": 1})
            return

        seen = db.get_seen_ids()
        title_inc, title_exc, loc_inc = compile_filters(cfg)
        companies = cfg["companies"]
        total_matches = 0
        total_new = 0
        error_count = 0

        for i, entry in enumerate(companies):
            board = entry["board"]
            company = entry.get("name", entry.get("slug", board))

            self._sse("progress", {"company": company, "index": i + 1, "total": len(companies)})

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
                self._sse("scan_error", {"company": company, "error": f"{type(e).__name__}: {e}"})
                error_count += 1
                continue

            hits = [j for j in jobs if matches(j, title_inc, title_exc, loc_inc)]
            for h in hits:
                h["is_new"] = h["id"] not in seen
                classify(h)

            new_count = sum(1 for h in hits if h["is_new"])
            total_matches += len(hits)
            total_new += new_count

            if hits:
                db.upsert_jobs(hits)
                self._sse("matches", {
                    "company": company,
                    "jobs": hits,
                    "total_open": len(jobs),
                    "matched": len(hits),
                    "new": new_count,
                })

            time.sleep(0.4)

        self._sse("done", {
            "total_matches": total_matches,
            "new": total_new,
            "companies_scanned": len(companies),
            "errors": error_count,
        })

    def _sse(self, event, data):
        msg = f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"
        try:
            self.wfile.write(msg.encode())
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, fmt, *args):
        pass


def main():
    db.init_db()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"  http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
