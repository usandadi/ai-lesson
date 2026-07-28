"""Journal and runner intent (spec §8, §12)."""

from sapapp import journal, runner

ENTRIES = [
    {"kind": "run", "status": "started"},
    {"kind": "user", "user": "A", "status": "created", "roles_added": ["Z1"], "roles_skipped": []},
    {"kind": "user", "user": "B", "status": "updated", "roles_added": ["Z2"], "roles_skipped": ["Z3"]},
    {"kind": "user", "user": "C", "status": "failed", "roles_added": [], "roles_skipped": []},
]


def _journal_file(tmp_path, lines):
    path = tmp_path / "journal.jsonl"
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def test_resume_skips_only_users_that_actually_completed(tmp_path):
    """A journal of 3 done out of 5 must drive exactly the remaining 2.

    Failed users are NOT complete — re-running must retry them, or a partial run
    silently becomes a permanent one.
    """
    import json

    path = _journal_file(tmp_path, [json.dumps(e) for e in ENTRIES])
    entries = journal.read(path)

    done = journal.completed_users(entries)
    assert done == {"A", "B"}

    planned = ["A", "B", "C", "D", "E"]
    assert [u for u in planned if u not in done] == ["C", "D", "E"]


def test_truncated_final_line_from_a_killed_run_is_survivable(tmp_path):
    """A run killed mid-write must still yield a usable journal for rollback."""
    path = _journal_file(
        tmp_path,
        ['{"kind":"user","user":"A","status":"created","roles_added":[],"roles_skipped":[]}',
         '{"kind":"user","user":"B","stat'],
    )
    entries = journal.read(path)
    assert len(entries) == 1
    assert entries[0]["user"] == "A"


def test_summary_counts_what_happened(tmp_path):
    import json

    path = _journal_file(tmp_path, [json.dumps(e) for e in ENTRIES])
    summary = journal.summarise(journal.read(path))

    assert summary["created"] == 1
    assert summary["updated"] == 1
    assert summary["failed"] == 1
    assert summary["roles_added"] == 2


def test_runner_reports_failure_even_when_cscript_exits_zero(tmp_path):
    """The journal is the source of truth, not the exit code.

    A script can complete cleanly having failed individual users; reporting the
    exit code alone would call that a success.
    """
    import json

    journal_path = str(tmp_path / "j.jsonl")

    def fake_invoke(script_path, timeout):
        with open(journal_path, "w", encoding="utf-8") as handle:
            for entry in ENTRIES:
                handle.write(json.dumps(entry) + "\n")
        return 0

    outcome = runner.run("run.vbs", journal_path, invoke=fake_invoke)

    assert outcome.exit_code == 0
    assert outcome.summary["failed"] == 1
    assert outcome.ok is False
    assert "1 user(s) failed" in outcome.message


def test_runner_explains_a_wrong_target_abort(tmp_path):
    journal_path = str(tmp_path / "j.jsonl")

    def fake_invoke(script_path, timeout):
        return 3

    outcome = runner.run("run.vbs", journal_path, invoke=fake_invoke)
    assert "not the SID/client you named" in outcome.message


def test_stale_journal_is_cleared_before_a_run(tmp_path):
    """Otherwise a re-run reports last run's successes as this run's."""
    journal_path = str(tmp_path / "j.jsonl")
    with open(journal_path, "w", encoding="utf-8") as handle:
        handle.write('{"kind":"user","user":"OLD","status":"created"}\n')

    def fake_invoke(script_path, timeout):
        return 0

    outcome = runner.run("run.vbs", journal_path, invoke=fake_invoke)
    assert outcome.entries == []
