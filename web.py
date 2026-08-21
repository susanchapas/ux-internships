#!/usr/bin/env python3
"""web.py — browser dashboard for internship_watch. Run: python web.py"""

import json
import re
import sys
import time
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from internship_watch import (
    load_json, compile_filters, matches, CONFIG_PATH, HIDDEN_PATH,
    fetch_greenhouse, fetch_lever, fetch_ashby, fetch_smartrecruiters,
    fetch_workday, fetch_usajobs, BOARD_FETCHERS,
)
import db
import auth as user_auth
from models import Role
from schemas import UserCreate, UserRead

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

    def _get_token(self):
        cookie_header = self.headers.get("Cookie", "")
        c = SimpleCookie(cookie_header)
        return c["session"].value if "session" in c else None

    def _current_user(self):
        token = self._get_token()
        if not token:
            return None
        return user_auth.get_current_user(token)

    def _require_login(self):
        user = self._current_user()
        if not user:
            self._json_response({"error": "Login required"}, 401)
        return user

    def _require_admin(self):
        user = self._require_login()
        if not user:
            return None
        if user.role != Role.admin:
            self._json_response({"error": "Admin access required"}, 403)
            return None
        return user

    def do_GET(self):
        if self.path in ("/", "/scanner", "/tracker", "/profile"):
            self._serve_dashboard()
        elif self.path == "/api/scan":
            self._run_scan()
        elif self.path == "/api/applications":
            self._json_response(db.list_applications())
        elif self.path == "/api/hidden":
            self._json_response(sorted(db.get_hidden_ids()))
        elif self.path == "/api/me":
            user = self._require_login()
            if user:
                self._json_response(UserRead.model_validate(user).model_dump())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/register":
            self._handle_register()
        elif self.path == "/api/login":
            self._handle_login()
        elif self.path == "/api/logout":
            token = self._get_token()
            if token:
                user_auth.logout(token)
            self._set_cookie("session", "", max_age=0)
            self._json_response({"ok": True})
        elif self.path.startswith("/api/hidden/"):
            job_id = self.path[len("/api/hidden/"):]
            db.hide_job(job_id)
            self._sync_hidden_json()
            self._json_response({"ok": True})
        elif self.path == "/api/applications":
            user = self._require_admin()
            if not user:
                return
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
        if self.path == "/api/me/username":
            user = self._require_login()
            if not user:
                return
            body = self._read_body()
            new_username = body.get("username", "").strip()
            if not new_username:
                self._json_response({"error": "Username required"}, 400)
                return
            try:
                updated = user_auth.update_username(user.id, new_username)
            except Exception:
                self._json_response({"error": "Username already taken"}, 409)
                return
            self._json_response(UserRead.model_validate(updated).model_dump())
        elif self.path == "/api/me/email":
            user = self._require_login()
            if not user:
                return
            body = self._read_body()
            new_email = body.get("email", "").strip()
            if not new_email:
                self._json_response({"error": "Email required"}, 400)
                return
            try:
                updated = user_auth.update_email(user.id, new_email)
            except Exception:
                self._json_response({"error": "Email already taken"}, 409)
                return
            self._json_response(UserRead.model_validate(updated).model_dump())
        elif self.path == "/api/me/password":
            user = self._require_login()
            if not user:
                return
            body = self._read_body()
            current = body.get("current_password", "")
            new_pw = body.get("new_password", "")
            if not current or not new_pw:
                self._json_response({"error": "Both current and new password required"}, 400)
                return
            try:
                user_auth.update_password(user.id, current, new_pw)
            except PermissionError:
                self._json_response({"error": "Current password is incorrect"}, 403)
                return
            self._json_response({"ok": True})
        elif self.path.startswith("/api/applications/"):
            user = self._require_admin()
            if not user:
                return
            app_id = int(self.path.split("/")[-1])
            body = self._read_body()
            db.update_application(app_id, **body)
            self._json_response({"ok": True})
        else:
            self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith("/api/hidden/"):
            job_id = self.path[len("/api/hidden/"):]
            db.unhide_job(job_id)
            self._sync_hidden_json()
            self._json_response({"ok": True})
        elif self.path.startswith("/api/applications/"):
            user = self._require_admin()
            if not user:
                return
            app_id = int(self.path.split("/")[-1])
            db.delete_application(app_id)
            self._json_response({"ok": True})
        else:
            self.send_error(404)

    def _handle_register(self):
        body = self._read_body()
        try:
            data = UserCreate(**body)
        except Exception as e:
            self._json_response({"error": str(e)}, 400)
            return
        if data.role == Role.admin:
            self._json_response({"error": "Cannot self-register as admin"}, 403)
            return
        try:
            user = user_auth.register_user(data.username, data.email, data.password)
        except Exception:
            self._json_response({"error": "Username or email already taken"}, 409)
            return
        self._json_response(UserRead.model_validate(user).model_dump(), 201)

    def _handle_login(self):
        body = self._read_body()
        result = user_auth.login_user(body.get("username", ""), body.get("password", ""))
        if not result:
            self._json_response({"error": "Invalid credentials"}, 401)
            return
        user, token = result
        self._set_cookie("session", token)
        self._json_response(UserRead.model_validate(user).model_dump())

    def _set_cookie(self, name, value, max_age=86400 * 30):
        cookie = f"{name}={value}; HttpOnly; SameSite=Strict; Path=/; Max-Age={max_age}"
        self._pending_cookie = cookie

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _json_response(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if hasattr(self, "_pending_cookie"):
            self.send_header("Set-Cookie", self._pending_cookie)
            del self._pending_cookie
        self.end_headers()
        self.wfile.write(body)

    def _sync_hidden_json(self):
        HIDDEN_PATH.write_text(json.dumps(sorted(db.get_hidden_ids()), indent=1))

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
    user_auth.get_engine()
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
