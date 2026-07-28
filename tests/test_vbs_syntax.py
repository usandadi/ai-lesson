"""Does the generated VBScript actually parse? (spec §7)

WSH compiles a whole script before executing any of it, so injecting an immediate
WScript.Quit gives a real syntax check that never reaches GetObject("SAPGUI") —
no session is attached and nothing in SAP is touched.

Skipped where cscript is unavailable.
"""

import shutil
import subprocess

import pytest

from sapapp.emitter import build_probe_script, build_rollback_script, build_run_script
from sapapp.models import RoleSpec, UserSpec

pytestmark = pytest.mark.skipif(shutil.which("cscript") is None, reason="cscript not available")

USERS = [
    UserSpec(
        username="JDOE",
        last_name="Doe",
        first_name="John",
        email="j.doe@example.com",
        roles=[RoleSpec("Z_FIN_DISPLAY"), RoleSpec("Z_MM_POST", "20260101", "20261231")],
    )
]


def _compiles(script: str, tmp_path, name: str) -> tuple[int, str]:
    # First executable statement becomes Quit, so nothing after it ever runs.
    guarded = script.replace("Q = Chr(34)", "WScript.Quit 0\nQ = Chr(34)", 1)
    assert "WScript.Quit 0\nQ = Chr(34)" in guarded, "guard anchor missing from generated script"

    path = tmp_path / name
    path.write_text(guarded, encoding="utf-8", newline="\r\n")
    result = subprocess.run(
        ["cscript", "//nologo", "//B", str(path)], capture_output=True, text=True, timeout=60
    )
    return result.returncode, (result.stdout + result.stderr)


def test_run_script_compiles(tmp_path):
    code, output = _compiles(build_run_script(USERS, "j.jsonl", dry_run=False), tmp_path, "run.vbs")
    assert code == 0, output


def test_dry_run_script_compiles(tmp_path):
    code, output = _compiles(build_run_script(USERS, "j.jsonl"), tmp_path, "dry.vbs")
    assert code == 0, output


def test_rollback_script_compiles(tmp_path):
    actions = [
        {"action": "remove_roles", "user": "JDOE", "roles": ["Z_NEW"]},
        {"action": "delete_user", "user": "NEWUSER", "roles": []},
    ]
    code, output = _compiles(
        build_rollback_script(actions, "j.jsonl", dry_run=False), tmp_path, "rb.vbs"
    )
    assert code == 0, output


def test_probe_script_compiles(tmp_path):
    """The probe has no Q assignment to anchor on, so it is guarded after its Dim."""
    script = build_probe_script("p.jsonl").replace(
        "Q = Chr(34)", "WScript.Quit 0\nQ = Chr(34)", 1
    )
    path = tmp_path / "probe.vbs"
    path.write_text(script, encoding="utf-8", newline="\r\n")
    result = subprocess.run(
        ["cscript", "//nologo", "//B", str(path)], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stdout + result.stderr
