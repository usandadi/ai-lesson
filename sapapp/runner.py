"""Executes the emitted VBScript via cscript and reads the journal back (spec §8).

The subprocess call is injectable so tests drive a fake session without cscript,
SAP GUI, or Windows.
"""

import os
import subprocess
from dataclasses import dataclass

from . import journal

EXIT_MEANING = {
    0: "completed",
    2: "SAP GUI not reachable — is it running, and is client-side scripting enabled?",
    3: "aborted: attached session is not the SID/client you named",
}


@dataclass
class RunOutcome:
    exit_code: int
    entries: list[dict]
    summary: dict
    message: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.summary.get("failed")


def default_invoke(script_path: str, timeout: int) -> int:
    completed = subprocess.run(
        ["cscript", "//nologo", "//B", script_path],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return completed.returncode


def run(script_path: str, journal_path: str, timeout: int = 1800, invoke=None) -> RunOutcome:
    """Run a generated script, then report what the journal says actually happened.

    The journal is the source of truth, not the exit code: a script can exit 0
    having failed individual users.
    """
    invoke = invoke or default_invoke

    # Start from a clean journal so a resumed run does not read stale entries.
    if os.path.exists(journal_path):
        os.remove(journal_path)

    exit_code = invoke(script_path, timeout)
    entries = journal.read(journal_path)
    summary = journal.summarise(entries)

    message = EXIT_MEANING.get(exit_code, f"cscript exited {exit_code}")
    if summary.get("failed"):
        message += f" — {summary['failed']} user(s) failed"
    if summary.get("aborted"):
        message += " — run aborted early"

    return RunOutcome(exit_code=exit_code, entries=entries, summary=summary, message=message)


def write_script(directory: str, name: str, content: str) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, name)
    # cscript on Windows wants CRLF; newline="" stops Python translating twice.
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(content.replace("\n", "\r\n"))
    return path
