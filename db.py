"""db.py — SQLite storage for scan history and application tracking."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "data.db"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT '',
            url TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT '',
            pay TEXT NOT NULL DEFAULT '',
            pay_type TEXT NOT NULL DEFAULT '',
            level TEXT NOT NULL DEFAULT '',
            schedule TEXT NOT NULL DEFAULT '',
            posted_at TEXT NOT NULL DEFAULT '',
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            pay TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'saved'
                CHECK(status IN ('saved','applied','phone_screen','interview',
                                 'offer','accepted','rejected','withdrawn')),
            applied_at TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.close()


def upsert_jobs(jobs):
    if not jobs:
        return
    now = _now()
    conn = _connect()
    conn.executemany("""
        INSERT INTO jobs (id, title, company, location, url, source,
                          pay, pay_type, level, schedule, posted_at,
                          first_seen, last_seen)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title, location=excluded.location,
            url=excluded.url, pay=excluded.pay, pay_type=excluded.pay_type,
            level=excluded.level, schedule=excluded.schedule,
            last_seen=excluded.last_seen
    """, [
        (j["id"], j["title"], j["company"], j.get("location", ""),
         j.get("url", ""), j.get("source", ""), j.get("pay", ""),
         j.get("pay_type", ""), j.get("level", ""), j.get("schedule", ""),
         j.get("posted_at", ""), now, now)
        for j in jobs
    ])
    conn.commit()
    conn.close()


def get_seen_ids():
    conn = _connect()
    ids = {r["id"] for r in conn.execute("SELECT id FROM jobs").fetchall()}
    conn.close()
    return ids


def list_applications():
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM applications ORDER BY updated_at DESC"
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def add_application(company, title, url="", location="", pay="",
                    status="saved", notes="", job_id=None, applied_at=""):
    now = _now()
    conn = _connect()
    cur = conn.execute(
        """INSERT INTO applications
           (job_id, company, title, url, location, pay,
            status, applied_at, notes, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (job_id, company, title, url, location, pay,
         status, applied_at, notes, now, now),
    )
    conn.commit()
    app_id = cur.lastrowid
    conn.close()
    return app_id


def update_application(app_id, **fields):
    allowed = {"company", "title", "url", "location", "pay",
               "status", "applied_at", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    updates["updated_at"] = _now()
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [app_id]
    conn = _connect()
    conn.execute(f"UPDATE applications SET {cols} WHERE id=?", vals)
    conn.commit()
    conn.close()


def delete_application(app_id):
    conn = _connect()
    conn.execute("DELETE FROM applications WHERE id=?", (app_id,))
    conn.commit()
    conn.close()
