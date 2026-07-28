"""Local web UI (spec §9).

Bound to 127.0.0.1 only. It drives a privileged desktop session, so it must never
listen on a routable interface. No authentication: localhost-only, single operator.
"""

import os
import shutil
import uuid

from flask import Flask, abort, redirect, render_template, request, url_for

from . import emitter, journal, rollback, runner
from .excel_parser import ParseResult, parse_file, split_roles
from .models import RoleSpec, UserSpec
from .validator import validate

RUNS_DIR = os.environ.get("SAPAPP_RUNS", os.path.join(os.getcwd(), "runs"))

app = Flask(__name__)
_runs: dict[str, dict] = {}


def _run_dir(run_id: str) -> str:
    return os.path.join(RUNS_DIR, run_id)


def _get(run_id: str) -> dict:
    state = _runs.get(run_id)
    if state is None:
        abort(404, "unknown run — the app was probably restarted; re-upload the sheet")
    return state


def _new_run(result: ParseResult, source: str) -> str:
    run_id = uuid.uuid4().hex[:8]
    os.makedirs(_run_dir(run_id), exist_ok=True)
    _runs[run_id] = {
        "id": run_id,
        "source": source,
        "users": result.users,
        "mapping": result.mapping,
        "unmapped": result.unmapped,
        "problems": list(result.problems) + validate(result.users),
        "executed": False,
    }
    return run_id


@app.route("/")
def index():
    return render_template("index.html", runs=sorted(_runs.values(), key=lambda r: r["id"]))


@app.post("/upload")
def upload():
    upload_file = request.files.get("sheet")
    if not upload_file or not upload_file.filename:
        return redirect(url_for("index"))

    staging = os.path.join(RUNS_DIR, "_incoming")
    os.makedirs(staging, exist_ok=True)
    path = os.path.join(staging, upload_file.filename)
    upload_file.save(path)

    result = parse_file(path)
    run_id = _new_run(result, f"file: {upload_file.filename}")
    shutil.move(path, os.path.join(_run_dir(run_id), upload_file.filename))
    return redirect(url_for("review", run_id=run_id))


@app.post("/manual")
def manual():
    """Requirement 3 — a few users by hand, through the same validator and emitter."""
    users: list[UserSpec] = []
    for line_no, line in enumerate(request.form.get("entries", "").splitlines(), start=1):
        if not line.strip():
            continue
        fields = [part.strip() for part in line.split("|")]
        fields += [""] * (4 - len(fields))
        users.append(
            UserSpec(
                username=fields[0].upper(),
                last_name=fields[1],
                email=fields[2],
                roles=[RoleSpec(name) for name in split_roles(fields[3])],
                source_rows=[line_no],
            )
        )

    result = ParseResult(users=users, mapping={"(manual entry)": "typed in the UI"})
    run_id = _new_run(result, "manual entry")
    return redirect(url_for("review", run_id=run_id))


@app.get("/run/<run_id>")
def review(run_id: str):
    state = _get(run_id)
    script = None
    if not state["problems"]:
        script = emitter.build_run_script(
            state["users"], os.path.join(_run_dir(run_id), "journal.jsonl")
        )
    return render_template("review.html", state=state, script=script)


@app.post("/run/<run_id>/execute")
def execute(run_id: str):
    """Dry-run is the default; executing requires the explicit checkbox (spec §8)."""
    state = _get(run_id)
    if state["problems"]:
        abort(400, "fix the reported problems first — the app will not emit a partial script")

    dry_run = request.form.get("mode") != "execute"
    sid = request.form.get("sid", "").strip()
    client = request.form.get("client", "").strip()

    directory = _run_dir(run_id)
    journal_path = os.path.join(directory, "journal.jsonl")
    script = emitter.build_run_script(
        state["users"], journal_path, sid=sid, client=client, dry_run=dry_run
    )
    script_path = runner.write_script(directory, "run.vbs", script)

    outcome = runner.run(script_path, journal_path)
    state["outcome"] = outcome
    state["executed"] = not dry_run
    state["sid"], state["client"] = sid, client
    return render_template("results.html", state=state, outcome=outcome, dry_run=dry_run)


@app.post("/run/<run_id>/probe")
def probe(run_id: str):
    """Preflight the control IDs against this system before trusting any of them."""
    directory = _run_dir(run_id)
    journal_path = os.path.join(directory, "probe.jsonl")
    script_path = runner.write_script(
        directory, "probe.vbs", emitter.build_probe_script(journal_path)
    )
    outcome = runner.run(script_path, journal_path)
    return render_template("results.html", state=_get(run_id), outcome=outcome, dry_run=True,
                           probe=True)


@app.post("/run/<run_id>/rollback")
def rollback_run(run_id: str):
    state = _get(run_id)
    directory = _run_dir(run_id)
    entries = journal.read(os.path.join(directory, "journal.jsonl"))
    actions = rollback.plan_rollback(entries)

    if not actions:
        return render_template(
            "results.html", state=state, outcome=state.get("outcome"), dry_run=True,
            message="Nothing to roll back — this run made no durable change.",
        )

    dry_run = request.form.get("mode") != "execute"
    journal_path = os.path.join(directory, "rollback.jsonl")
    script = emitter.build_rollback_script(
        actions,
        journal_path,
        sid=state.get("sid", ""),
        client=state.get("client", ""),
        dry_run=dry_run,
    )
    script_path = runner.write_script(directory, "rollback.vbs", script)
    outcome = runner.run(script_path, journal_path)

    return render_template(
        "results.html",
        state=state,
        outcome=outcome,
        dry_run=dry_run,
        rollback_plan=rollback.describe(actions),
    )


def main():
    os.makedirs(RUNS_DIR, exist_ok=True)
    # 127.0.0.1 only — see the module docstring and spec §9.
    app.run(host="127.0.0.1", port=int(os.environ.get("SAPAPP_PORT", "5000")), debug=False)


if __name__ == "__main__":
    main()
