#!/usr/bin/env python3
"""
repl.py — Read-Eval-Print Loop for the internship watch system.

Provides continuous interactive access to scanning, filtering,
application tracking, and undo — all through the Facade.

    python repl.py
"""

import shlex

from patterns import (
    InternshipFacade,
    DefaultFilterStrategy,
    UXOnlyFilterStrategy,
    PaidOnlyFilterStrategy,
    RemoteFilterStrategy,
)

VALID_STATUSES = (
    "saved", "applied", "phone_screen", "interview",
    "offer", "accepted", "rejected", "withdrawn",
)

HELP = """\
Commands:
  scan                        Scan all configured companies
  jobs                        Show results from last scan
  apps                        List tracked applications
  save <job#> [notes]         Save a job from last scan to applications
  status <app_id> <status>    Update application status
  delete <app_id>             Delete a tracked application
  undo                        Undo last status change (Memento)
  filter [name]               Show or switch filter strategy (Strategy)
  config                      Show configuration summary
  help                        Show this help
  quit                        Exit

Filter strategies: default, ux-only, paid, remote

Statuses: saved, applied, phone_screen, interview,
          offer, accepted, rejected, withdrawn
"""


def _print_jobs(jobs):
    """Render a table of job results."""
    if not jobs:
        print("  No results.")
        return
    print(f"  {'#':<5} {'Company':<25} {'Title':<45} {'Location':<25} {'Pay'}")
    print(f"  {'─'*5} {'─'*25} {'─'*45} {'─'*25} {'─'*20}")
    for i, j in enumerate(jobs, 1):
        print(
            f"  {i:<5} {(j.get('company') or '')[:24]:<25} "
            f"{(j.get('title') or '')[:44]:<45} "
            f"{(j.get('location') or '')[:24]:<25} "
            f"{(j.get('pay') or '')[:20]}"
        )


def _print_apps(apps):
    """Render a table of tracked applications."""
    if not apps:
        print("  No applications tracked.")
        return
    print(f"  {'ID':<5} {'Company':<25} {'Title':<35} {'Status':<15} {'Updated'}")
    print(f"  {'─'*5} {'─'*25} {'─'*35} {'─'*15} {'─'*20}")
    for a in apps:
        print(
            f"  {a['id']:<5} {a['company'][:24]:<25} "
            f"{a['title'][:34]:<35} {a['status']:<15} "
            f"{a['updated_at'][:10]}"
        )


def _handle_scan(facade, _args):
    print("Scanning...")
    facade.scan()


def _handle_jobs(facade, _args):
    _print_jobs(facade.get_last_results())


def _handle_apps(facade, _args):
    _print_apps(facade.list_applications())


def _handle_save(facade, args):
    if not args:
        print("Usage: save <job#> [notes]")
        return
    idx = int(args[0]) - 1
    results = facade.get_last_results()
    if not (0 <= idx < len(results)):
        print(f"  Invalid job number. Range: 1–{len(results)}")
        return
    notes = " ".join(args[1:])
    app_id = facade.save_job(results[idx], notes)
    print(f"  Saved as application #{app_id}")


def _handle_status(facade, args):
    if len(args) < 2:
        print(f"Usage: status <app_id> <{'|'.join(VALID_STATUSES)}>")
        return
    app_id = int(args[0])
    new_status = args[1]
    if new_status not in VALID_STATUSES:
        print(f"  Invalid status. Choose: {', '.join(VALID_STATUSES)}")
        return
    facade.update_application_status(app_id, new_status)
    print(f"  Updated #{app_id} → '{new_status}'")


def _handle_delete(facade, args):
    if not args:
        print("Usage: delete <app_id>")
        return
    app_id = int(args[0])
    facade.delete_application(app_id)
    print(f"  Deleted application #{app_id}")


def _handle_undo(facade, _args):
    desc = facade.undo()
    if desc:
        print(f"  Undone: {desc}")
    else:
        print("  Nothing to undo.")


def _handle_filter(facade, args):
    if not args:
        current = facade.filter_strategy.name if facade.filter_strategy else "none"
        print(f"  Current: {current}")
        print("  Available: default, ux-only, paid, remote")
        return

    name = args[0].lower()
    base = DefaultFilterStrategy(facade.cfg) if facade.cfg else None

    strategies = {
        "default": lambda: base,
        "ux-only": lambda: UXOnlyFilterStrategy(),
        "paid": lambda: PaidOnlyFilterStrategy(base or UXOnlyFilterStrategy()),
        "remote": lambda: RemoteFilterStrategy(base or UXOnlyFilterStrategy()),
    }

    builder = strategies.get(name)
    if not builder:
        print(f"  Unknown strategy '{name}'. Available: {', '.join(strategies)}")
        return

    facade.set_filter_strategy(builder())
    print(f"  Filter → {facade.filter_strategy.name}")


def _handle_config(facade, _args):
    if not facade.cfg:
        print("  No config loaded.")
        return
    companies = facade.cfg.get("companies", [])
    boards = {}
    for c in companies:
        b = c["board"]
        boards[b] = boards.get(b, 0) + 1
    print(f"  Companies: {len(companies)}")
    for b, n in sorted(boards.items(), key=lambda x: -x[1]):
        print(f"    {b:<20} {n}")
    print(f"  Filter: {facade.filter_strategy.name if facade.filter_strategy else 'none'}")
    print(f"  Undo history: {facade.caretaker.history_size} entries")


def _handle_help(_facade, _args):
    print(HELP)


COMMANDS = {
    "scan": _handle_scan,
    "jobs": _handle_jobs,
    "results": _handle_jobs,
    "apps": _handle_apps,
    "applications": _handle_apps,
    "save": _handle_save,
    "status": _handle_status,
    "delete": _handle_delete,
    "undo": _handle_undo,
    "filter": _handle_filter,
    "config": _handle_config,
    "help": _handle_help,
}


def repl():
    """Main Read-Eval-Print Loop."""
    facade = InternshipFacade()
    filter_name = facade.filter_strategy.name if facade.filter_strategy else "none"

    print("Internship Watch — Interactive Mode")
    print(f"Filter: {filter_name}  |  {len(facade.cfg.get('companies', []))} companies loaded")
    print("Type 'help' for commands.\n")

    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not line:
            continue

        try:
            parts = shlex.split(line)
        except ValueError:
            parts = line.split()

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("quit", "exit", "q"):
            print("Bye.")
            break

        handler = COMMANDS.get(cmd)
        if not handler:
            print(f"  Unknown command: '{cmd}'. Type 'help' for available commands.")
            continue

        try:
            handler(facade, args)
        except ValueError as e:
            print(f"  Error: {e}")
        except Exception as e:
            print(f"  Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    repl()
