"""Run journal: what actually happened, per user (spec §8).

The journal is the basis for three things — reporting, resume, and rollback. It
records roles the run *added* separately from roles it found *already present*,
which is what lets rollback remove only what the run itself did.
"""

import json
import os

DONE_STATUSES = {"created", "updated"}


def read(path: str) -> list[dict]:
    """Tolerant reader: a truncated final line from a killed run is skipped, not fatal."""
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def completed_users(entries: list[dict]) -> set[str]:
    """Users a previous run finished, so a re-run skips them (spec §8)."""
    return {
        e.get("user", "")
        for e in entries
        if e.get("kind") == "user" and e.get("status") in DONE_STATUSES and e.get("user")
    }


def failed_users(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e.get("kind") == "user" and e.get("status") == "failed"]


def was_aborted(entries: list[dict]) -> bool:
    return any(e.get("kind") == "run" and e.get("status") == "aborted" for e in entries)


def summarise(entries: list[dict]) -> dict:
    users = [e for e in entries if e.get("kind") == "user"]
    return {
        "total": len(users),
        "created": sum(1 for e in users if e.get("status") == "created"),
        "updated": sum(1 for e in users if e.get("status") == "updated"),
        "planned": sum(1 for e in users if e.get("status") == "planned"),
        "failed": sum(1 for e in users if e.get("status") == "failed"),
        "roles_added": sum(len(e.get("roles_added") or []) for e in users),
        "aborted": was_aborted(entries),
    }
