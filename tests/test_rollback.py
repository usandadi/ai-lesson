"""Rollback intent (spec §8, §12) — the highest-stakes logic in the app.

A regression here removes access users held before the run ever touched them.
"""

from sapapp.rollback import plan_rollback


def test_rollback_removes_only_roles_the_run_added():
    """The load-bearing distinction: added vs. already-present.

    Z_EXISTING was the user's before this run. Removing it during a rollback would
    take away access nobody asked us to touch.
    """
    entries = [
        {
            "kind": "user",
            "user": "JDOE",
            "status": "updated",
            "roles_added": ["Z_NEW_ONE", "Z_NEW_TWO"],
            "roles_skipped": ["Z_EXISTING"],
        }
    ]
    actions = plan_rollback(entries)

    assert len(actions) == 1
    assert actions[0]["action"] == "remove_roles"
    assert actions[0]["roles"] == ["Z_NEW_ONE", "Z_NEW_TWO"]
    assert "Z_EXISTING" not in actions[0]["roles"]


def test_users_created_by_the_run_are_deleted_not_role_stripped():
    entries = [
        {
            "kind": "user",
            "user": "NEWUSER",
            "status": "created",
            "roles_added": ["Z_A"],
            "roles_skipped": [],
        }
    ]
    actions = plan_rollback(entries)

    assert actions == [{"action": "delete_user", "user": "NEWUSER", "roles": []}]


def test_failed_users_are_not_rolled_back():
    """A user the run never changed must not be touched by the undo."""
    entries = [
        {"kind": "user", "user": "JDOE", "status": "failed", "roles_added": [], "roles_skipped": []}
    ]
    assert plan_rollback(entries) == []


def test_dry_run_entries_are_not_rolled_back():
    """A planned run wrote nothing, so there is nothing to compensate for."""
    entries = [
        {
            "kind": "user",
            "user": "JDOE",
            "status": "planned",
            "roles_added": ["Z_A"],
            "roles_skipped": [],
        }
    ]
    assert plan_rollback(entries) == []


def test_user_updated_with_no_new_roles_needs_no_action():
    """Every role was already present, so the run changed nothing to undo."""
    entries = [
        {
            "kind": "user",
            "user": "JDOE",
            "status": "updated",
            "roles_added": [],
            "roles_skipped": ["Z_EXISTING"],
        }
    ]
    assert plan_rollback(entries) == []
