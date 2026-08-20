#!/usr/bin/env python3
"""
Design patterns for the internship watch system.

Implements five GoF patterns:
    Observer  — decouple scan events from notification channels
    Memento   — undo/redo for application status changes
    Strategy  — swappable job filtering logic
    Factory   — create the right ATS fetcher from a config entry
    Facade    — single entry point to scan, filter, track, and notify
"""

import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests

from internship_watch import (
    load_json, compile_filters, matches,
    fetch_greenhouse, fetch_lever, fetch_ashby, fetch_smartrecruiters,
    fetch_workday, fetch_usajobs,
    CONFIG_PATH, TIMEOUT,
)
import db


# ── Observer ─────────────────────────────────────────────────────────


class JobObserver(ABC):
    """Interface for objects that react to scan events."""

    @abstractmethod
    def on_new_jobs(self, jobs) -> None:
        """Called when new (unseen) jobs are found."""

    @abstractmethod
    def on_scan_complete(self, stats) -> None:
        """Called when a full scan finishes."""

    @abstractmethod
    def on_scan_error(self, company, error) -> None:
        """Called when a single company's fetch fails."""


class ConsoleObserver(JobObserver):
    """Prints scan events to stdout."""

    def on_new_jobs(self, jobs):
        for j in jobs:
            pay = f" | {j.get('pay')}" if j.get("pay") else ""
            print(f"  NEW: {j['company']} | {j['title']} | {j.get('location', '')}{pay}")
            print(f"       {j.get('url', '')}")

    def on_scan_complete(self, stats):
        print(
            f"\nScan complete: {stats['total_matches']} matches, "
            f"{stats['new']} new, {stats['errors']} errors"
        )

    def on_scan_error(self, company, error):
        print(f"  ERROR: {company}: {error}")


class NtfyObserver(JobObserver):
    """Pushes new-job alerts to an ntfy.sh topic."""

    def __init__(self):
        self.topic = os.environ.get("NTFY_TOPIC")

    def on_new_jobs(self, jobs):
        if not self.topic or not jobs:
            return
        lines = []
        for j in jobs:
            pay = f"\n💰 {j['pay']}" if j.get("pay") else ""
            lines.append(
                f"{j['company']} — {j['title']}\n"
                f"{j.get('location', '')}{pay}\n{j.get('url', '')}"
            )
        body = "\n\n".join(lines)
        subject = f"{len(jobs)} new internship posting{'s' if len(jobs) != 1 else ''}"
        try:
            requests.post(
                f"https://ntfy.sh/{self.topic}",
                data=body.encode("utf-8"),
                headers={"Title": subject, "Tags": "briefcase"},
                timeout=TIMEOUT,
            )
        except requests.RequestException:
            pass

    def on_scan_complete(self, stats):
        pass

    def on_scan_error(self, company, error):
        pass


class DiscordObserver(JobObserver):
    """Posts new-job alerts to a Discord webhook as rich embeds."""

    EMBED_COLOR = 0x5865F2  # Discord blurple

    def __init__(self):
        self.webhook = os.environ.get("DISCORD_WEBHOOK")
        self._new_jobs = []

    def on_new_jobs(self, jobs):
        if not self.webhook or not jobs:
            return
        self._new_jobs.extend(jobs)

    def on_scan_complete(self, stats):
        if not self.webhook:
            return
        jobs = self._new_jobs
        self._new_jobs = []

        if not jobs:
            return

        by_company = {}
        for j in jobs:
            by_company.setdefault(j["company"], []).append(j)

        embeds = []
        for company, postings in by_company.items():
            lines = []
            for j in postings:
                parts = [f"[{j['title']}]({j.get('url', '')})"]
                if j.get("location"):
                    parts.append(f"📍 {j['location']}")
                if j.get("pay"):
                    parts.append(f"💰 {j['pay']}")
                lines.append(" · ".join(parts))
            embeds.append({
                "title": f"{company} ({len(postings)})",
                "description": "\n".join(lines),
                "color": self.EMBED_COLOR,
            })

        summary = (
            f"**{len(jobs)}** new posting{'s' if len(jobs) != 1 else ''} "
            f"across **{len(by_company)}** compan{'ies' if len(by_company) != 1 else 'y'}"
        )

        # Discord allows max 10 embeds per message
        for i in range(0, len(embeds), 10):
            batch = embeds[i:i + 10]
            payload = {"embeds": batch}
            if i == 0:
                payload["content"] = f"🔔 {summary}"
            try:
                requests.post(self.webhook, json=payload, timeout=TIMEOUT)
                time.sleep(0.5)
            except requests.RequestException:
                pass

    def on_scan_error(self, company, error):
        pass


class EventBus:
    """Central dispatcher — manages observers and broadcasts scan events."""

    def __init__(self):
        self._observers = []

    def subscribe(self, observer):
        """Register an observer to receive events."""
        self._observers.append(observer)

    def unsubscribe(self, observer):
        """Remove an observer."""
        self._observers.remove(observer)

    def notify_new_jobs(self, jobs):
        for obs in self._observers:
            obs.on_new_jobs(jobs)

    def notify_scan_complete(self, stats):
        for obs in self._observers:
            obs.on_scan_complete(stats)

    def notify_scan_error(self, company, error):
        for obs in self._observers:
            obs.on_scan_error(company, error)


# ── Memento ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ApplicationMemento:
    """Immutable snapshot of an application's state before a change."""

    app_id: int
    fields: dict
    description: str


class ApplicationCaretaker:
    """Stores mementos so application changes can be undone."""

    def __init__(self):
        self._history = []

    def save(self, memento):
        """Push a memento onto the undo stack."""
        self._history.append(memento)

    def undo(self):
        """Pop and return the most recent memento, or None."""
        return self._history.pop() if self._history else None

    @property
    def can_undo(self):
        return len(self._history) > 0

    @property
    def history_size(self):
        return len(self._history)


# ── Strategy ─────────────────────────────────────────────────────────


class FilterStrategy(ABC):
    """Defines a job-filtering algorithm that can be swapped at runtime."""

    @abstractmethod
    def apply(self, jobs) -> list:
        """Return the subset of jobs that pass this filter."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this strategy."""


class DefaultFilterStrategy(FilterStrategy):
    """Filters using the title_include / title_exclude / location_include regexes from config.json."""

    def __init__(self, cfg):
        self._title_inc, self._title_exc, self._loc_inc = compile_filters(cfg)

    def apply(self, jobs):
        return [j for j in jobs if matches(j, self._title_inc, self._title_exc, self._loc_inc)]

    @property
    def name(self):
        return "default"


class UXOnlyFilterStrategy(FilterStrategy):
    """Strict filter: title must mention both a UX discipline and an internship-level role."""

    _UX = re.compile(
        r"(UX|user experience|design|research|product|content strategy"
        r"|interaction|usability|human factors)",
        re.I,
    )
    _INTERN = re.compile(
        r"\bintern(?:ship)?\b|\bco-?op\b|\bfellow(?:ship)?\b|\bapprentice\b", re.I
    )

    def apply(self, jobs):
        return [
            j for j in jobs
            if self._UX.search(j.get("title", "")) and self._INTERN.search(j.get("title", ""))
        ]

    @property
    def name(self):
        return "ux-only"


class PaidOnlyFilterStrategy(FilterStrategy):
    """Decorator: wraps another strategy and keeps only jobs that list pay."""

    def __init__(self, inner):
        self._inner = inner

    def apply(self, jobs):
        return [j for j in self._inner.apply(jobs) if j.get("pay")]

    @property
    def name(self):
        return f"paid-only ({self._inner.name})"


class RemoteFilterStrategy(FilterStrategy):
    """Decorator: wraps another strategy and keeps only remote/hybrid jobs."""

    _RE = re.compile(r"\bremote\b|\bhybrid\b", re.I)

    def __init__(self, inner):
        self._inner = inner

    def apply(self, jobs):
        return [
            j for j in self._inner.apply(jobs)
            if self._RE.search(j.get("location", "")) or not j.get("location")
        ]

    @property
    def name(self):
        return f"remote ({self._inner.name})"


# ── Factory ──────────────────────────────────────────────────────────


class Fetcher(ABC):
    """Interface for objects that pull job listings from an ATS."""

    @abstractmethod
    def fetch(self) -> list:
        """Return a list of job dicts from this source."""


class GreenhouseFetcher(Fetcher):
    def __init__(self, slug, company):
        self.slug, self.company = slug, company

    def fetch(self):
        return list(fetch_greenhouse(self.slug, self.company))


class LeverFetcher(Fetcher):
    def __init__(self, slug, company):
        self.slug, self.company = slug, company

    def fetch(self):
        return list(fetch_lever(self.slug, self.company))


class AshbyFetcher(Fetcher):
    def __init__(self, slug, company):
        self.slug, self.company = slug, company

    def fetch(self):
        return list(fetch_ashby(self.slug, self.company))


class SmartRecruitersFetcher(Fetcher):
    def __init__(self, slug, company):
        self.slug, self.company = slug, company

    def fetch(self):
        return list(fetch_smartrecruiters(self.slug, self.company))


class WorkdayFetcher(Fetcher):
    def __init__(self, cfg, company):
        self.cfg, self.company = cfg, company

    def fetch(self):
        return list(fetch_workday(self.cfg, self.company))


class USAJobsFetcher(Fetcher):
    def __init__(self, cfg):
        self.cfg = cfg

    def fetch(self):
        return list(fetch_usajobs(self.cfg))


class FetcherFactory:
    """Creates the correct Fetcher subclass from a config.json company entry."""

    _BOARD_MAP = {
        "greenhouse": GreenhouseFetcher,
        "lever": LeverFetcher,
        "ashby": AshbyFetcher,
        "smartrecruiters": SmartRecruitersFetcher,
    }

    @classmethod
    def create(cls, entry):
        """Return a Fetcher for the given config entry, or None if the board is unknown."""
        board = entry["board"]
        company = entry.get("name", entry.get("slug", board))
        if board in cls._BOARD_MAP:
            return cls._BOARD_MAP[board](entry["slug"], company)
        if board == "workday":
            return WorkdayFetcher(entry, company)
        if board == "usajobs":
            return USAJobsFetcher(entry)
        return None


# ── Facade ───────────────────────────────────────────────────────────


class InternshipFacade:
    """
    Unified interface to the internship watch system.

    Combines scanning (Factory), filtering (Strategy), notifications (Observer),
    application tracking, and undo (Memento) behind a single object.
    """

    def __init__(self):
        self.cfg = load_json(CONFIG_PATH, {})
        self.event_bus = EventBus()
        self.caretaker = ApplicationCaretaker()
        self._filter_strategy = DefaultFilterStrategy(self.cfg) if self.cfg else None
        self._last_scan_results = []

        db.init_db()

        self.event_bus.subscribe(ConsoleObserver())
        if os.environ.get("NTFY_TOPIC"):
            self.event_bus.subscribe(NtfyObserver())
        if os.environ.get("DISCORD_WEBHOOK"):
            self.event_bus.subscribe(DiscordObserver())

    @property
    def filter_strategy(self):
        return self._filter_strategy

    def set_filter_strategy(self, strategy):
        """Swap the active filter strategy."""
        self._filter_strategy = strategy

    def scan(self):
        """Run a full scan across all configured companies. Returns matched jobs."""
        if not self.cfg:
            print("No config.json found.")
            return []

        seen = db.get_seen_ids()
        all_matches = []
        errors = 0
        companies = self.cfg.get("companies", [])

        for i, entry in enumerate(companies):
            company = entry.get("name", entry.get("slug", entry["board"]))
            print(f"  [{i+1}/{len(companies)}] {company}...", end=" ", flush=True)

            fetcher = FetcherFactory.create(entry)
            if not fetcher:
                print(f"unknown board '{entry['board']}'")
                continue

            try:
                jobs = fetcher.fetch()
            except Exception as e:
                self.event_bus.notify_scan_error(company, f"{type(e).__name__}: {e}")
                errors += 1
                continue

            hits = self._filter_strategy.apply(jobs) if self._filter_strategy else jobs
            print(f"{len(jobs)} open, {len(hits)} match")

            new = [j for j in hits if j["id"] not in seen]
            if new:
                self.event_bus.notify_new_jobs(new)

            all_matches.extend(hits)
            db.upsert_jobs(hits)
            time.sleep(0.4)

        self._last_scan_results = all_matches
        new_total = sum(1 for j in all_matches if j["id"] not in seen)

        stats = {
            "total_matches": len(all_matches),
            "new": new_total,
            "companies_scanned": len(companies),
            "errors": errors,
        }
        self.event_bus.notify_scan_complete(stats)
        return all_matches

    def get_last_results(self):
        """Return jobs from the most recent scan."""
        return self._last_scan_results

    def list_applications(self):
        """Return all tracked applications."""
        return db.list_applications()

    def save_job(self, job, notes=""):
        """Save a matched job as a tracked application. Returns the new application ID."""
        return db.add_application(
            company=job["company"],
            title=job["title"],
            url=job.get("url", ""),
            location=job.get("location", ""),
            pay=job.get("pay", ""),
            status="saved",
            notes=notes,
            job_id=job.get("id"),
        )

    def update_application_status(self, app_id, new_status):
        """Change an application's status, saving a memento for undo."""
        apps = db.list_applications()
        current = next((a for a in apps if a["id"] == app_id), None)
        if not current:
            raise ValueError(f"Application {app_id} not found")

        self.caretaker.save(ApplicationMemento(
            app_id=app_id,
            fields={"status": current["status"]},
            description=(
                f"{current['company']} — {current['title']}: "
                f"'{current['status']}' → '{new_status}'"
            ),
        ))
        db.update_application(app_id, status=new_status)

    def undo(self):
        """Undo the last application status change. Returns description or None."""
        memento = self.caretaker.undo()
        if not memento:
            return None
        db.update_application(memento.app_id, **memento.fields)
        return memento.description

    def delete_application(self, app_id):
        """Remove a tracked application."""
        db.delete_application(app_id)
