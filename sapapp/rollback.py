"""Delta-based rollback (spec §8).

Because this app only ever *adds* roles, undo does not need full prior-state
restoration — it needs the delta actually applied. Removing a role the run merely
found already present would strip access the user held before we touched them,
so `roles_skipped` is never a rollback candidate.
"""

from . import journal


def plan_rollback(entries: list[dict]) -> list[dict]:
    """Build compensating actions from a run journal.

    Users the run created are deleted. Users it only modified have exactly the
    roles it added removed — nothing else.
    """
    actions: list[dict] = []

    for entry in entries:
        if entry.get("kind") != "user":
            continue
        user = entry.get("user")
        status = entry.get("status")
        if not user or status not in journal.DONE_STATUSES:
            continue

        if status == "created":
            actions.append({"action": "delete_user", "user": user, "roles": []})
            continue

        added = [r for r in (entry.get("roles_added") or []) if r]
        if added:
            actions.append({"action": "remove_roles", "user": user, "roles": added})

    return actions


def describe(actions: list[dict]) -> list[str]:
    lines = []
    for action in actions:
        if action["action"] == "delete_user":
            lines.append(f"DELETE user {action['user']} (created by this run)")
        else:
            lines.append(f"REMOVE from {action['user']}: {', '.join(action['roles'])}")
    return lines
