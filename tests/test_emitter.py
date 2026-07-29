"""Emitter intent (spec §7, §12).

The generated VBScript cannot be executed in a test — that needs Windows, SAP GUI,
and a logged-in session. These assert the safety properties are present in the text
that will run, which is the part a refactor can silently drop.
"""

from sapapp.emitter import build_probe_script, build_rollback_script, build_run_script
from sapapp.models import RoleSpec, UserSpec
from sapapp.screen_ids import SU01_IDS

USERS = [
    UserSpec(
        username="JDOE",
        last_name="Doe",
        roles=[RoleSpec("Z_FIN_DISPLAY"), RoleSpec("Z_MM_POST", "20260101", "20261231")],
    )
]


def test_dry_run_script_declares_dry_run_and_journals_a_plan():
    """Dry-run must reach the journal without reaching a save."""
    script = build_run_script(USERS, "j.jsonl", dry_run=True)

    assert "Const DRY_RUN = True" in script
    assert '"planned"' in script
    # The dry-run branch exits before the save press.
    plan_at = script.index('JLog "user", uname, "planned"')
    save_at = script.index("Set fld = FindOrFail(ID_SAVE, ok)")
    assert plan_at < save_at


def test_execute_script_declares_execute():
    script = build_run_script(USERS, "j.jsonl", dry_run=False)
    assert "Const DRY_RUN = False" in script


def test_roles_are_appended_at_a_computed_row_never_a_fixed_index():
    """Spec §7: writing to a fixed row index clobbers roles the user already holds."""
    script = build_run_script(USERS, "j.jsonl")

    assert "target = grid.RowCount" in script
    assert "grid.modifyCell target, ROLE_COL, name" in script
    # No literal row index is ever written to.
    assert "modifyCell 0," not in script
    assert "modifyCell 1," not in script


def test_existing_roles_are_read_before_anything_is_added():
    """Feeds both the additive merge and the rollback delta."""
    script = build_run_script(USERS, "j.jsonl")
    assert "Function ReadExistingRoles(ByRef ok)" in script
    assert "existing.Exists(name)" in script


def test_save_is_followed_by_a_status_bar_check():
    """GUI Scripting raises nothing on a failed save — sbar is the only signal."""
    script = build_run_script(USERS, "j.jsonl", dry_run=False)
    save_at = script.index("Set fld = FindOrFail(ID_SAVE, ok)")
    check_at = script.index("If SaveFailed() Then", save_at)
    assert save_at < check_at
    # And SaveFailed must actually inspect the status bar, not just exist.
    assert 'SaveFailed = (t = "E" Or t = "A" Or t = "W")' in script
    assert 'JLog "user", uname, "failed"' in script


def test_target_guard_aborts_on_wrong_sid_or_client():
    """The session is whatever the operator left open (spec §8)."""
    script = build_run_script(USERS, "j.jsonl", sid="SBX", client="100")

    assert 'Const EXPECT_SID = "SBX"' in script
    assert 'Const EXPECT_CLIENT = "100"' in script
    assert "WScript.Quit 3" in script


def test_script_never_closes_the_operators_session():
    """The operator owns the session — spec §7."""
    script = build_run_script(USERS, "j.jsonl", dry_run=False)
    assert "wnd[0].close" not in script
    assert "/nex" not in script


def test_snc_name_is_written_only_when_creating_a_user():
    """Decision 5 is "add roles only" — rewriting SNC on a live account would change
    how that account authenticates, which is well outside adding a role."""
    users = [
        UserSpec(
            username="JDOE",
            last_name="Doe",
            snc_name="p:CN=JDOE@EXAMPLE.COM",
            roles=[RoleSpec("Z_A")],
        )
    ]
    script = build_run_script(users, "j.jsonl", dry_run=False)

    assert 'ProcessUser "JDOE", "Doe", "", "", "p:CN=JDOE@EXAMPLE.COM"' in script
    # The SNC write sits inside the create branch, after the create press and
    # before that branch closes.
    create_at = script.index("Set fld = FindOrFail(ID_CREATE, ok)")
    snc_at = script.index("Set fld = FindOrFail(ID_SNCNAME, ok)")
    append_at = script.index("added = AppendRoles(roleData, existing, ok)")
    assert create_at < snc_at < append_at


def test_users_without_snc_name_skip_the_snc_tab():
    script = build_run_script(USERS, "j.jsonl", dry_run=False)
    assert 'If sncname <> "" Then' in script


def test_usernames_with_quotes_cannot_break_out_of_the_string():
    """Sheet content is untrusted input to a code generator."""
    nasty = [UserSpec(username='X" & Evil() & "', last_name="Doe", roles=[RoleSpec("Z_A")])]
    script = build_run_script(nasty, "j.jsonl")
    assert 'ProcessUser "X"" & Evil() & """' in script


def test_role_validity_dates_are_carried_through():
    script = build_run_script(USERS, "j.jsonl")
    assert "Z_MM_POST|20260101|20261231" in script


def test_probe_checks_controls_without_writing():
    """Preflight fails at step zero rather than on user 47 (spec §7)."""
    script = build_probe_script("probe.jsonl")
    assert "username_field" in script
    assert "WScript.Quit missing" in script
    assert "ID_SAVE" not in script


def test_creating_a_user_fails_loudly_when_the_last_name_control_is_missing():
    """SU01 will not save without a surname, so a missing last-name control cannot be
    skipped the way an optional field can. Skipping it silently produced SAP's "fill in
    all required entry fields" at save, which names the wrong cause and is why user
    creation appeared to fail for reasons nobody could diagnose."""
    script = build_run_script(USERS, "j.jsonl", dry_run=False)

    # The old silent-skip form must not come back.
    assert "If ok Then fld.Text = lastname" not in script
    assert '"last name field not found' in script

    # And it must abort before the save, not after.
    fail_at = script.index('JLog "user", uname, "failed", "last name field not found')
    save_at = script.index("Set fld = FindOrFail(ID_SAVE, ok)")
    assert fail_at < save_at


def test_an_unreachable_role_grid_aborts_before_the_save():
    """Fail closed. Saving anyway would create the user with no roles and journal it as
    a success — reporting work that never happened (CLAUDE.md Rule 12)."""
    script = build_run_script(USERS, "j.jsonl", dry_run=False)

    grid_fail_at = script.index('"role grid not found - nothing was saved"')
    save_at = script.index("Set fld = FindOrFail(ID_SAVE, ok)")
    assert grid_fail_at < save_at


def test_missing_grid_never_reads_as_the_user_holding_no_roles():
    """An empty dictionary from a failed grid read means every role looks new, and
    rollback then strips roles the user held before the run ever touched them
    (spec §8). ReadExistingRoles must distinguish "no roles" from "could not read"."""
    script = build_run_script(USERS, "j.jsonl", dry_run=False)

    assert "Set existing = ReadExistingRoles(ok)" in script
    read_at = script.index("Set existing = ReadExistingRoles(ok)")
    guard_at = script.index("If Not ok Then", read_at)
    append_at = script.index("added = AppendRoles(roleData, existing, ok)")
    assert read_at < guard_at < append_at


def test_probe_covers_every_control_user_creation_needs():
    """The original probe checked only the initial screen, so it passed green on a
    system where creating a user was impossible. That gap is the whole bug."""
    script = build_probe_script("probe.jsonl")

    for control in ("tab_address", "field_last_name", "tab_roles", "role_grid"):
        assert control in script, f"{control} is not probed"


def test_probe_enters_create_mode_but_never_saves():
    """Phase 2 has to reach the detail screen, but a probe that writes is not a probe."""
    script = build_probe_script("probe.jsonl")

    assert "PROBE_USER" in script
    # Save is the only press that would commit anything.
    assert SU01_IDS["btn_save"] not in script.split("' --- phase 2")[1]
    # It backs out by re-entering the transaction rather than guessing a modal button.
    assert '.Text = "/nSU01"' in script


def test_rollback_script_only_touches_named_roles():
    actions = [
        {"action": "remove_roles", "user": "JDOE", "roles": ["Z_NEW"]},
        {"action": "delete_user", "user": "NEWUSER", "roles": []},
    ]
    script = build_rollback_script(actions, "j.jsonl", dry_run=False)

    assert 'RemoveRoles "JDOE", Array("Z_NEW")' in script
    assert 'DeleteUser "NEWUSER"' in script
