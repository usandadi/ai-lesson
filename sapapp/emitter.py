"""VBScript generation (spec §7).

The emitted script IS the executable artifact — what the operator reviews is what
cscript runs (spec §8). Every control lookup goes through FindOrFail, and every save
is followed by a status-bar check, because GUI Scripting raises nothing on a failed
save: the screen simply doesn't advance.

VBScript quoting note: JSON is assembled with Chr(34) rather than doubled quotes.
It is wordier but keeps the generator readable and removes a whole class of
escaping bugs from generated code nobody wants to debug at 2am.
"""

import json

from .models import UserSpec
from .screen_ids import PROBE_CONTROLS, SU01_IDS


def _vbs_string(value: str) -> str:
    """Render a Python string as a VBScript literal, doubling embedded quotes."""
    return '"' + str(value).replace('"', '""') + '"'


def _vbs_array(values: list[str]) -> str:
    if not values:
        return "Array()"
    return "Array(" + ", ".join(_vbs_string(v) for v in values) + ")"


_DIMS = """\
Option Explicit

Dim SapGui, App, Conn, Session, FSO, Journal, Failures, Aborted, Q
Dim ID_OKCD, ID_SBAR, ID_UNAME, ID_DISPLAY, ID_CHANGE, ID_CREATE, ID_SAVE, ID_BACK, ID_DELETE
Dim ID_TAB_ADDRESS, ID_LASTNAME, ID_FIRSTNAME, ID_EMAIL
Dim ID_TAB_LOGON, ID_PWD1, ID_PWD2, ID_UGROUP
Dim ID_TAB_SNC, ID_SNCNAME
Dim ID_TAB_ROLES, ID_GRID, ROLE_COL, ROLE_FROM_COL, ROLE_TO_COL
"""

_HELPERS = """
' --- JSON journal helpers -------------------------------------------------
Function Esc(s)
  Dim t
  t = CStr(s)
  t = Replace(t, "\\", "\\\\")
  t = Replace(t, Chr(34), "\\" & Chr(34))
  t = Replace(t, vbCr, " ")
  t = Replace(t, vbLf, " ")
  t = Replace(t, vbTab, " ")
  Esc = t
End Function

Function KV(k, v)
  KV = Q & k & Q & ":" & Q & Esc(v) & Q
End Function

Function KVRaw(k, v)
  KVRaw = Q & k & Q & ":" & v
End Function

Function JsonList(arr)
  Dim i, out
  out = "["
  If IsArray(arr) Then
    If UBound(arr) >= 0 Then
      For i = 0 To UBound(arr)
        If i > 0 Then out = out & ","
        out = out & Q & Esc(arr(i)) & Q
      Next
    End If
  End If
  JsonList = out & "]"
End Function

Sub JLog(kind, user, status, detail, added, skipped)
  Journal.WriteLine "{" & KV("kind", kind) & "," & KV("user", user) & "," & _
    KV("status", status) & "," & KV("detail", detail) & "," & _
    KVRaw("roles_added", JsonList(added)) & "," & _
    KVRaw("roles_skipped", JsonList(skipped)) & "}"
End Sub

' --- control access -------------------------------------------------------
' Fails loudly rather than pressing whatever happens to sit at that path.
Function FindOrFail(controlId, ByRef ok)
  On Error Resume Next
  Set FindOrFail = Session.findById(controlId)
  If Err.Number <> 0 Then
    ok = False
    Err.Clear
  ElseIf FindOrFail Is Nothing Then
    ok = False
  Else
    ok = True
  End If
  On Error Goto 0
End Function

Function SbarType()
  Dim ok, bar
  Set bar = FindOrFail(ID_SBAR, ok)
  If Not ok Then
    SbarType = "?"
  Else
    SbarType = bar.MessageType
  End If
End Function

Function SbarText()
  Dim ok, bar
  Set bar = FindOrFail(ID_SBAR, ok)
  If Not ok Then
    SbarText = ""
  Else
    SbarText = bar.Text
  End If
End Function

Function SaveFailed()
  Dim t
  t = SbarType()
  SaveFailed = (t = "E" Or t = "A" Or t = "W")
End Function

Sub GotoSU01()
  Dim ok, box
  Set box = FindOrFail(ID_OKCD, ok)
  If ok Then
    box.Text = "/nSU01"
    Session.findById("wnd[0]").sendVKey 0
  End If
End Sub
"""

_ATTACH = """
' --- attach to the operator's existing session; never authenticate (spec §8) ---
Q = Chr(34)
Failures = 0
Aborted = False
Set FSO = CreateObject("Scripting.FileSystemObject")
Set Journal = FSO.OpenTextFile(JOURNAL_PATH, 8, True)

On Error Resume Next
Set SapGui = GetObject("SAPGUI")
If Err.Number <> 0 Or SapGui Is Nothing Then
  JLog "run", "", "aborted", "SAP GUI not running, or client-side scripting is disabled", Array(), Array()
  Journal.Close
  WScript.Quit 2
End If
On Error Goto 0

Set App = SapGui.GetScriptingEngine
Set Conn = App.Children(CONNECTION_INDEX)
Set Session = Conn.Children(SESSION_INDEX)

If Session Is Nothing Then
  JLog "run", "", "aborted", "no SAP GUI session at the requested index", Array(), Array()
  Journal.Close
  WScript.Quit 2
End If

' The session is whatever the operator left open, so confirm it is the right one.
If EXPECT_SID <> "" And UCase(Session.Info.SystemName) <> UCase(EXPECT_SID) Then
  JLog "run", "", "aborted", "expected SID " & EXPECT_SID & " but session is " & Session.Info.SystemName, Array(), Array()
  Journal.Close
  WScript.Quit 3
End If
If EXPECT_CLIENT <> "" And Session.Info.Client <> EXPECT_CLIENT Then
  JLog "run", "", "aborted", "expected client " & EXPECT_CLIENT & " but session is " & Session.Info.Client, Array(), Array()
  Journal.Close
  WScript.Quit 3
End If

JLog "run", "", "started", "SID " & Session.Info.SystemName & " client " & Session.Info.Client, Array(), Array()
"""

_PROCESS_USER = """
' --- per-user work --------------------------------------------------------
Function UserExists(uname)
  Dim ok, fld
  GotoSU01
  Set fld = FindOrFail(ID_UNAME, ok)
  If Not ok Then
    UserExists = -1
    Exit Function
  End If
  fld.Text = uname
  FindOrFail(ID_DISPLAY, ok).press
  If SbarType() = "E" Then
    UserExists = 0
  Else
    UserExists = 1
  End If
End Function

' Reads the Roles tab of the currently displayed user. Feeds both the additive
' merge and the rollback delta (spec §8).
Function ReadExistingRoles()
  Dim ok, tab, grid, i, value, found
  Set found = CreateObject("Scripting.Dictionary")
  Set tab = FindOrFail(ID_TAB_ROLES, ok)
  If ok Then tab.Select
  Set grid = FindOrFail(ID_GRID, ok)
  If ok Then
    For i = 0 To grid.RowCount - 1
      value = UCase(Trim(grid.GetCellValue(i, ROLE_COL)))
      If value <> "" Then found(value) = i
    Next
  End If
  Set ReadExistingRoles = found
End Function

Function MissingRoles(roleData, existing)
  Dim i, parts, name, out
  out = Array()
  For i = 0 To UBound(roleData)
    parts = Split(roleData(i), "|")
    name = UCase(Trim(parts(0)))
    If Not existing.Exists(name) Then
      ReDim Preserve out(UBound(out) + 1)
      out(UBound(out)) = name
    End If
  Next
  MissingRoles = out
End Function

Function PresentRoles(roleData, existing)
  Dim i, parts, name, out
  out = Array()
  For i = 0 To UBound(roleData)
    parts = Split(roleData(i), "|")
    name = UCase(Trim(parts(0)))
    If existing.Exists(name) Then
      ReDim Preserve out(UBound(out) + 1)
      out(UBound(out)) = name
    End If
  Next
  PresentRoles = out
End Function

' Appends at the first free row, never a fixed index — writing to an occupied
' row would clobber a role the user already holds (spec §7).
Function AppendRoles(roleData, existing)
  Dim ok, tab, grid, i, parts, name, target, added
  added = Array()
  Set tab = FindOrFail(ID_TAB_ROLES, ok)
  If ok Then tab.Select
  Set grid = FindOrFail(ID_GRID, ok)
  If Not ok Then
    AppendRoles = Array()
    Exit Function
  End If

  target = grid.RowCount
  For i = 0 To grid.RowCount - 1
    If Trim(grid.GetCellValue(i, ROLE_COL)) = "" Then
      target = i
      Exit For
    End If
  Next

  For i = 0 To UBound(roleData)
    parts = Split(roleData(i), "|")
    name = UCase(Trim(parts(0)))
    If Not existing.Exists(name) Then
      grid.modifyCell target, ROLE_COL, name
      If UBound(parts) >= 1 Then
        If parts(1) <> "" Then grid.modifyCell target, ROLE_FROM_COL, parts(1)
      End If
      If UBound(parts) >= 2 Then
        If parts(2) <> "" Then grid.modifyCell target, ROLE_TO_COL, parts(2)
      End If
      ReDim Preserve added(UBound(added) + 1)
      added(UBound(added)) = name
      target = target + 1
    End If
  Next
  AppendRoles = added
End Function

Sub ProcessUser(uname, lastname, firstname, email, sncname, ugroup, pwd, roleData)
  Dim exists, existing, added, skipped, planned, ok, created, tab, fld

  If Aborted Then Exit Sub
  created = False

  exists = UserExists(uname)
  If exists = -1 Then
    Failures = Failures + 1
    JLog "user", uname, "failed", "SU01 controls not found - run the probe against this system", Array(), Array()
    If Failures >= ABORT_AFTER Then Aborted = True
    Exit Sub
  End If

  If exists = 1 Then
    Set existing = ReadExistingRoles()
  Else
    Set existing = CreateObject("Scripting.Dictionary")
  End If

  skipped = PresentRoles(roleData, existing)

  If DRY_RUN Then
    planned = MissingRoles(roleData, existing)
    JLog "user", uname, "planned", "dry run - nothing written", planned, skipped
    GotoSU01
    Exit Sub
  End If

  GotoSU01
  Set fld = FindOrFail(ID_UNAME, ok)
  If ok Then fld.Text = uname

  If exists = 1 Then
    FindOrFail(ID_CHANGE, ok).press
  Else
    FindOrFail(ID_CREATE, ok).press
    created = True
    Set tab = FindOrFail(ID_TAB_ADDRESS, ok)
    If ok Then tab.Select
    Set fld = FindOrFail(ID_LASTNAME, ok)
    If ok Then fld.Text = lastname
    If firstname <> "" Then
      Set fld = FindOrFail(ID_FIRSTNAME, ok)
      If ok Then fld.Text = firstname
    End If
    If email <> "" Then
      Set fld = FindOrFail(ID_EMAIL, ok)
      If ok Then fld.Text = email
    End If
    Set tab = FindOrFail(ID_TAB_LOGON, ok)
    If ok Then tab.Select
    If pwd <> "" Then
      Set fld = FindOrFail(ID_PWD1, ok)
      If ok Then fld.Text = pwd
      Set fld = FindOrFail(ID_PWD2, ok)
      If ok Then fld.Text = pwd
    End If
    If ugroup <> "" Then
      Set fld = FindOrFail(ID_UGROUP, ok)
      If ok Then fld.Text = ugroup
    End If
    ' SNC identity, creation only: overwriting it on an existing user would change
    ' how a live account authenticates, which is outside "add roles only".
    If sncname <> "" Then
      Set tab = FindOrFail(ID_TAB_SNC, ok)
      If ok Then
        tab.Select
        Set fld = FindOrFail(ID_SNCNAME, ok)
        If ok Then fld.Text = sncname
      End If
    End If
  End If

  added = AppendRoles(roleData, existing)

  FindOrFail(ID_SAVE, ok).press

  ' GUI Scripting raises nothing on a failed save - the status bar is the only signal.
  If SaveFailed() Then
    Failures = Failures + 1
    JLog "user", uname, "failed", SbarText(), Array(), skipped
    If Failures >= ABORT_AFTER Then
      Aborted = True
      JLog "run", "", "aborted", "stopped after " & Failures & " consecutive failures", Array(), Array()
    End If
    GotoSU01
    Exit Sub
  End If

  Failures = 0
  If created Then
    JLog "user", uname, "created", SbarText(), added, skipped
  Else
    JLog "user", uname, "updated", SbarText(), added, skipped
  End If
  GotoSU01
End Sub
"""

_ROLLBACK_BODY = """
' --- compensating actions (spec §8) ---------------------------------------
Sub RemoveRoles(uname, roles)
  Dim ok, tab, grid, i, r, value, removed
  If Aborted Then Exit Sub
  removed = Array()
  GotoSU01
  Set tab = FindOrFail(ID_UNAME, ok)
  If ok Then tab.Text = uname
  FindOrFail(ID_CHANGE, ok).press
  Set tab = FindOrFail(ID_TAB_ROLES, ok)
  If ok Then tab.Select
  Set grid = FindOrFail(ID_GRID, ok)
  If Not ok Then
    JLog "rollback", uname, "failed", "role grid not found", Array(), Array()
    Exit Sub
  End If

  For i = 0 To UBound(roles)
    For r = 0 To grid.RowCount - 1
      value = UCase(Trim(grid.GetCellValue(r, ROLE_COL)))
      If value = UCase(roles(i)) Then
        If Not DRY_RUN Then grid.modifyCell r, ROLE_COL, ""
        ReDim Preserve removed(UBound(removed) + 1)
        removed(UBound(removed)) = value
        Exit For
      End If
    Next
  Next

  If DRY_RUN Then
    JLog "rollback", uname, "planned", "would remove these roles", removed, Array()
    GotoSU01
    Exit Sub
  End If

  FindOrFail(ID_SAVE, ok).press
  If SaveFailed() Then
    JLog "rollback", uname, "failed", SbarText(), Array(), Array()
  Else
    JLog "rollback", uname, "roles_removed", SbarText(), removed, Array()
  End If
  GotoSU01
End Sub

Sub DeleteUser(uname)
  Dim ok, fld
  If Aborted Then Exit Sub
  GotoSU01
  Set fld = FindOrFail(ID_UNAME, ok)
  If ok Then fld.Text = uname
  If DRY_RUN Then
    JLog "rollback", uname, "planned", "would delete this user", Array(), Array()
    Exit Sub
  End If
  FindOrFail(ID_DELETE, ok).press
  ' SU01 asks for confirmation before deleting.
  On Error Resume Next
  Session.findById("wnd[1]/usr/btnSPOP-OPTION1").press
  Err.Clear
  On Error Goto 0
  If SaveFailed() Then
    JLog "rollback", uname, "failed", SbarText(), Array(), Array()
  Else
    JLog "rollback", uname, "user_deleted", SbarText(), Array(), Array()
  End If
  GotoSU01
End Sub
"""

_EPILOGUE = """
JLog "run", "", "finished", "", Array(), Array()
Journal.Close
WScript.Quit 0
"""


def _config_block(
    ids: dict[str, str],
    journal_path: str,
    sid: str,
    client: str,
    dry_run: bool,
    abort_after: int,
    connection_index: int,
    session_index: int,
) -> str:
    lines = [
        f"Const JOURNAL_PATH = {_vbs_string(journal_path)}",
        f"Const EXPECT_SID = {_vbs_string(sid)}",
        f"Const EXPECT_CLIENT = {_vbs_string(client)}",
        f"Const DRY_RUN = {'True' if dry_run else 'False'}",
        f"Const ABORT_AFTER = {abort_after}",
        f"Const CONNECTION_INDEX = {connection_index}",
        f"Const SESSION_INDEX = {session_index}",
        "",
        "' Control paths come from sapapp/screen_ids.py — the single lookup table (spec §7).",
    ]
    for name, key in (
        ("ID_OKCD", "okcd"),
        ("ID_SBAR", "statusbar"),
        ("ID_UNAME", "username_field"),
        ("ID_DISPLAY", "btn_display"),
        ("ID_CHANGE", "btn_change"),
        ("ID_CREATE", "btn_create"),
        ("ID_SAVE", "btn_save"),
        ("ID_BACK", "btn_back"),
        ("ID_DELETE", "btn_delete"),
        ("ID_TAB_ADDRESS", "tab_address"),
        ("ID_LASTNAME", "field_last_name"),
        ("ID_FIRSTNAME", "field_first_name"),
        ("ID_EMAIL", "field_email"),
        ("ID_TAB_LOGON", "tab_logondata"),
        ("ID_PWD1", "field_password"),
        ("ID_PWD2", "field_password_repeat"),
        ("ID_UGROUP", "field_user_group"),
        ("ID_TAB_SNC", "tab_snc"),
        ("ID_SNCNAME", "field_snc_name"),
        ("ID_TAB_ROLES", "tab_roles"),
        ("ID_GRID", "role_grid"),
        ("ROLE_COL", "role_column"),
        ("ROLE_FROM_COL", "role_from_column"),
        ("ROLE_TO_COL", "role_to_column"),
    ):
        lines.append(f"{name} = {_vbs_string(ids[key])}")
    return "\n".join(lines) + "\n"


def _header(mode: str, sid: str, client: str) -> str:
    return (
        "' " + "-" * 72 + "\n"
        "' Generated by sapapp. Do not edit by hand - regenerate from the source.\n"
        f"' Mode:   {mode}\n"
        f"' Target: SID {sid or '(any)'} client {client or '(any)'}\n"
        "' " + "-" * 72 + "\n"
    )


def build_run_script(
    users: list[UserSpec],
    journal_path: str,
    sid: str = "",
    client: str = "",
    dry_run: bool = True,
    abort_after: int = 3,
    connection_index: int = 0,
    session_index: int = 0,
    ids: dict[str, str] | None = None,
) -> str:
    """Render the VBScript that creates users and appends their roles."""
    ids = {**SU01_IDS, **(ids or {})}

    parts = [
        _header("DRY RUN - nothing is written" if dry_run else "EXECUTE", sid, client),
        _DIMS,
        _config_block(
            ids, journal_path, sid, client, dry_run, abort_after, connection_index, session_index
        ),
        _HELPERS,
        _PROCESS_USER,
        _ATTACH,
        "\n' --- one call per user ---\n",
    ]

    for user in users:
        role_data = [f"{r.name}|{r.valid_from}|{r.valid_to}" for r in user.roles]
        parts.append(
            "ProcessUser {}, {}, {}, {}, {}, {}, {}, {}\n".format(
                _vbs_string(user.username),
                _vbs_string(user.last_name),
                _vbs_string(user.first_name),
                _vbs_string(user.email),
                _vbs_string(user.snc_name),
                _vbs_string(user.user_group),
                _vbs_string(user.initial_password),
                _vbs_array(role_data),
            )
        )

    parts.append(_EPILOGUE)
    return "".join(parts)


def build_rollback_script(
    actions: list[dict],
    journal_path: str,
    sid: str = "",
    client: str = "",
    dry_run: bool = True,
    connection_index: int = 0,
    session_index: int = 0,
    ids: dict[str, str] | None = None,
) -> str:
    """Render the compensating script: remove exactly what a run added (spec §8).

    `actions` come from rollback.plan_rollback, which only ever lists roles the run
    recorded as newly added — never one it recorded as already present.
    """
    ids = {**SU01_IDS, **(ids or {})}

    parts = [
        _header("ROLLBACK DRY RUN" if dry_run else "ROLLBACK EXECUTE", sid, client),
        _DIMS,
        _config_block(ids, journal_path, sid, client, dry_run, 99, connection_index, session_index),
        _HELPERS,
        _ROLLBACK_BODY,
        _ATTACH,
        "\n' --- one call per affected user ---\n",
    ]

    for action in actions:
        if action["action"] == "delete_user":
            parts.append(f"DeleteUser {_vbs_string(action['user'])}\n")
        else:
            parts.append(
                "RemoveRoles {}, {}\n".format(
                    _vbs_string(action["user"]), _vbs_array(action["roles"])
                )
            )

    parts.append(_EPILOGUE)
    return "".join(parts)


def build_probe_script(journal_path: str, ids: dict[str, str] | None = None) -> str:
    """Preflight: assert every control exists before any write (spec §7).

    A layout mismatch fails at step zero rather than on user 47. Writes nothing.
    """
    ids = {**SU01_IDS, **(ids or {})}
    lines = [
        _header("PREFLIGHT PROBE - writes nothing", "", ""),
        "Option Explicit",
        "Dim SapGui, App, Conn, Session, FSO, Journal, ctl, missing, Q",
        "Q = Chr(34)",
        "missing = 0",
        'Set FSO = CreateObject("Scripting.FileSystemObject")',
        f"Set Journal = FSO.OpenTextFile({_vbs_string(journal_path)}, 8, True)",
        "",
        "Sub Note(status, control, detail)",
        '  Journal.WriteLine "{" & Q & "kind" & Q & ":" & Q & "probe" & Q & "," & _',
        '    Q & "status" & Q & ":" & Q & status & Q & "," & _',
        '    Q & "control" & Q & ":" & Q & control & Q & "," & _',
        '    Q & "detail" & Q & ":" & Q & detail & Q & "}"',
        "End Sub",
        "",
        "On Error Resume Next",
        'Set SapGui = GetObject("SAPGUI")',
        "If Err.Number <> 0 Or SapGui Is Nothing Then",
        '  Note "failed", "", "SAP GUI not running, or client-side scripting is disabled"',
        "  Journal.Close",
        "  WScript.Quit 2",
        "End If",
        "On Error Goto 0",
        "",
        "Set App = SapGui.GetScriptingEngine",
        "Set Conn = App.Children(0)",
        "Set Session = Conn.Children(0)",
        'Note "session", "", Session.Info.SystemName & " client " & Session.Info.Client',
        f'Session.findById({_vbs_string(ids["okcd"])}).Text = "/nSU01"',
        'Session.findById("wnd[0]").sendVKey 0',
        "",
    ]
    for control in PROBE_CONTROLS:
        lines += [
            "On Error Resume Next",
            f"Set ctl = Session.findById({_vbs_string(ids[control])})",
            "If Err.Number <> 0 Or ctl Is Nothing Then",
            f'  Note "missing", "{control}", "control not found on this system"',
            "  missing = missing + 1",
            "  Err.Clear",
            "End If",
            "On Error Goto 0",
            "",
        ]
    lines += [
        'Note "done", "", "missing=" & missing',
        "Journal.Close",
        "WScript.Quit missing",
    ]
    return "\n".join(lines) + "\n"


def preview(users: list[UserSpec]) -> str:
    """Human-readable summary shown beside the script on the review screen."""
    return json.dumps(
        [{"user": u.username, "roles": [r.name for r in u.roles]} for u in users], indent=2
    )
