# Design Spec — SAP User/Role Script Generator

Status: **draft for review**. Nothing built yet.

## 1. Problem

A security/Basis admin receives a spreadsheet of users and the roles they need.
Today that becomes manual SU01 work. This app turns the spreadsheet into a script
that performs the same creation and role assignment in SAP.

## 2. Scope

**In scope**
- Read an Excel file of users + roles; infer the column meaning from the header row.
- Manual entry mode for one or a few users, without a file.
- Validate everything, then emit a runnable script plus a report.

- Connect to a target SAP system and apply the change, dry-run by default.

**Out of scope (v1)**
- CUA distribution logic, licence/UCLASS management, PFCG role generation.
- Deleting or locking users; modifying role assignments other than additively.
- Unattended/scheduled runs. Execution is operator-initiated and operator-confirmed.

The app can now change a live system, so §8 governs how that is allowed to happen.

## 3. Architecture

```
Excel file ──┐
             ├──> Parser ──> UserSpec[] ──> Validator ──> Emitter ──> run.vbs
Manual entry ┘                                                          │
                                                    Runner ──> cscript ─┘
                                                       │
                                                journal.jsonl ──> results / rollback script
```

Five parts, one canonical data type between them:

- **Parser** — two input adapters (file, manual) that both produce `UserSpec[]`.
- **UserSpec** — the single canonical record. Everything downstream sees only this.
- **Validator** — pure functions over `UserSpec[]`. No I/O.
- **Emitter** — renders `UserSpec[]` into VBScript.
- **Runner** — executes that VBScript against an attached SAP GUI session and reads the
  journal back.

**The Runner executes the Emitter's output** — the reverse of the previous draft. Choosing
GUI scripting leaves exactly one code path, so the artifact the operator reviews is the
artifact that runs. See §8.

The adapter split is the only abstraction here, and it exists because there are genuinely two
inputs (reqs 2 and 3). Everything after the Validator is a single line.

## 4. Canonical schema — `UserSpec`

| Field | SAP field | Required | Notes |
|---|---|---|---|
| `username` | `BNAME` | yes | ≤12 chars on-prem, uppercased |
| `last_name` | `NACHN` | yes | SU01 will not save without a surname |
| `first_name` | `VORNA` | no | |
| `email` | `SMTP_ADDR` | no | |
| `user_type` | `USTYP` | no | A=Dialog (default), B=System, C=Comm, S=Service, L=Reference |
| `user_group` | `CLASS` | no | drives who may administer the user |
| `valid_from` / `valid_to` | `GLTGV`/`GLTGB` | no | normalized to `YYYYMMDD` |
| `initial_password` | `PASSWORD` | no | see §10 |
| `roles` | `AGR_NAME[]` | yes | each with optional from/to dates |

## 5. Header inference (requirement 4)

Three stages, in order, stopping at the first that resolves a column:

1. **Normalize** — lowercase, trim, collapse whitespace/underscore/punctuation.
   `"User ID"`, `"user_id"`, `"USERID"` all become `userid`.
2. **Synonym table** — a hand-maintained map, e.g.
   `username ← {user, username, userid, bname, sap user, login, logon name}`
   `roles ← {role, roles, role name, agr_name, single role, composite role}`
3. **Unresolved columns** — reported to the user for manual mapping.

**The header row is not assumed to be row 1.** Real exports carry title banners and
blank rows, so the parser scans the first ~10 rows and picks the one with the most
synonym hits.

**The resolved mapping is always printed and confirmed before any script is generated.**
Silent guessing is the failure mode that produces a plausible script targeting the wrong
columns, so inference never runs unattended.

### Two row layouts, both must work

- **Layout A** — one row per user, roles in a single cell, delimited by `,` `;` or newline.
- **Layout B** — one row per user-role pair, username repeated.

Detected by checking whether any username appears in more than one row. Layout B must
collapse to *one* user with N roles — never N users.

### On using an LLM here (CLAUDE.md Rule 5)

Header matching is classification, which is a legitimate model use. But a synonym table
plus normalization resolves essentially every real-world header deterministically, at zero
cost and with reproducible output. **Recommendation: no LLM in v1.** If unmatched headers
turn out to be common in practice, add a model call *only* for columns stage 2 failed to
resolve, still surfaced for confirmation. The parse, validation, and emit paths stay
deterministic — code answers those.

## 6. Validation

Runs over the whole dataset **before** anything is emitted. A batch that fails halfway
through generation produces a script that is worse than no script.

- `username`: present, ≤12 chars, no spaces, no duplicates-with-conflicting-attributes
- `last_name`: present
- `role`: present, ≤30 chars (`AGR_NAME`), uppercased
- dates: parseable, `valid_from <= valid_to`, normalized to `YYYYMMDD`
- `user_type`: one of A/B/C/S/L
- email: shape check only

Errors are collected with **spreadsheet row numbers** and reported together. One bad row
fails the run; it does not emit a partial script.

## 7. Generated script requirements

Target format: **SAP GUI Scripting (VBScript)** driving SU01 in an attached session.

- **Attach to an existing session** (§8). Never open a connection, never type credentials.
- **Check existence first** — SU01 display, then branch create vs. add-roles-only.
- **Append role rows only.** Existing rows on the Roles tab are never cleared or overwritten.
  The BAPI hazard from the previous draft (`BAPI_USER_ACTGROUPS_ASSIGN` replacing the whole
  role list) **does not apply here** — SU01's role grid is naturally additive. The GUI
  equivalent is writing to fixed row indices and clobbering occupied rows, so rows are
  appended at `rowCount`.
- **Read the status bar (`sbar`) after every save.** Type `E`/`A`/`W` fails that user.
  GUI scripting raises nothing on a failed save — the screen simply doesn't advance, and a
  script that doesn't check will report success for work it never did.
- **Handle modals explicitly.** Expected dialogs are matched by title; anything unexpected
  aborts that user rather than blind-clicking Enter.
- **Record whether each role was already present or newly added** — this is what makes
  rollback possible (§8).
- **Emit one JSON journal line per user** so the Python side can read back what happened.
- **Never close the window or log out.** The operator owns the session.

### Element ID fragility

GUI scripting addresses controls by path (`wnd[0]/usr/ctxtUSR04-BNAME`), and those paths shift
with SAP GUI version, screen variant, and user parameters. Two mitigations:

- All control IDs live in **one lookup table** in the emitter, never scattered through templates.
- A **preflight probe** opens SU01 and asserts every expected control exists before any write,
  so a layout mismatch fails at step zero rather than on user 47.

## 8. Execution against a live SAP system

### How execution works

Choosing GUI scripting **collapses the (A)/(B) question** from the previous draft, which is
why answer 1 depending on answer 2 was the right read. The generated VBScript *is* the
executable artifact: the app renders it, the operator reviews it, and `cscript.exe` runs that
exact file. What was reviewed is what runs — there is no second code path that can drift from
the artifact, which is a genuine advantage over the RFC design.

```
Python renders run.vbs → operator reviews in UI → cscript //nologo run.vbs
   → VBScript writes JSON journal lines → Python reads them back → per-user results
```

### Session attachment, not authentication

**The app never authenticates.** It attaches to a SAP GUI session the operator has already
logged into:

```vbscript
GetObject("SAPGUI").GetScriptingEngine.Children(0).Children(0)
```

This dissolves the auth question completely — **userid/password and SSO both work**, because
the logon already happened in the GUI. The app handles no password in either case. The
`basic`/`sso` split from the previous draft is gone, and so are `pyrfc`, the NW RFC SDK, and
SNC configuration.

Consequences:
- **Windows only**, with SAP GUI for Windows installed.
- The web UI (§9) must run on the **same machine** as the GUI session.
- The run executes as **the operator's identity**, so they need the authorizations below
  directly. Every change is attributable to a real person in the audit trail.
- **No unattended runs**, by construction — a logged-in desktop session is required.
- If several sessions are open, the operator picks one in the UI. The app must not silently
  grab `Children(0)`.

### Hard prerequisites

Both must be true or nothing works:

- **Server:** profile parameter `sapgui/user_scripting = TRUE`. Off by default, and changing
  it is a Basis task — worth confirming on the sandbox before any code is written.
- **Client:** SAP GUI → Options → Accessibility & Scripting → Scripting → enabled, with
  *"Notify when a script attaches to SAP GUI"* and *"Notify when a script opens a connection"*
  **disabled**. Left on, every run stalls at a modal the script cannot dismiss.

Preflight checks both and names whichever is missing.

### Required safety controls

- **Dry-run is the default.** It renders the script and runs the preflight probe, and writes
  nothing. Executing requires a separate, explicit action.
- **Name the target.** The operator states the expected SID and client; the app reads
  `session.Info.SystemName` / `.Client` from the attached session and aborts on mismatch.
  This matters *more* here than with RFC — the session is whatever the operator happened to
  leave open, which may not be what they think it is.
- **Production guard.** Refuse a productive client without a separate acknowledgement.
- **Sandbox first.** Confirmed available; the first run of any sheet goes there.
- **Save per user**, so a failure at row 40 leaves rows 1-39 committed.
- **Capture prior roles first**, via SU01 display, recording which roles the user already has.
- **Journal every user** before and after, so a run is resumable and a re-run skips completed
  users.
- **Abort threshold.** Stop after N consecutive failures rather than producing 200 identical
  errors.

### Rollback

Because §11 answer 5 restricts this app to **adding** roles, undo does not need full
prior-state restoration — it needs the **delta actually applied**. The journal records, per
user: whether this run created them, which roles it added, and which roles it skipped as
already present.

Rollback generates a **second VBScript** that removes exactly the journaled additions and
deletes exactly the users this run created. It is itself reviewable and dry-runnable.

This is more robust than diffing against a scraped full prior state, and it is why the
"already present vs. newly added" distinction in §7 is load-bearing rather than bookkeeping.
Get that wrong and rollback strips roles the user held before the run ever touched them.

### Authorizations

The operator needs `S_USER_GRP`, `S_USER_AGR`, `S_USER_AUT` for SU01 and role assignment.
`S_RFC` is no longer relevant — there is no RFC anywhere in this design.

## 9. Local web UI

Python + Flask, bound to **127.0.0.1 only**. It drives a privileged desktop session, so it
must never listen on a routable interface. Stated explicitly here so nobody later exposes it
on the LAN for convenience.

Screens:

1. **Upload** — drop the `.xlsx`; see the inferred header mapping (§5); confirm or correct it.
2. **Manual entry** — a form for one or a few users/roles (req 3). Same `UserSpec[]`, same
   validator, same emitter as the file path.
3. **Review** — per-row validation results, plus the rendered VBScript shown in full.
4. **Run** — session picker, SID/client confirmation, dry-run, then execute with live per-user
   results.
5. **Rollback** — pick a previous run by journal, review the generated undo script, run it.

No authentication on the UI itself: localhost-only, single-operator by design.

## 10. Passwords

If the sheet carries plaintext initial passwords, the generated script contains plaintext
credentials — a file that tends to end up committed.

**Default: the script generates a random initial password per user at runtime and writes it
to a separate output file**, with the must-change flag set. Passing passwords through from
the sheet requires an explicit opt-in.

**Open:** if your *end users* log on via SSO, newly created users may need no initial password
at all, and this section largely disappears. "Or single sign-on" answered how the **operator**
reaches SAP — I still don't know how the **provisioned users** will. Answer decides whether
this section stays.

## 11. Decisions

All resolved:

| # | Question | Answer |
|---|---|---|
| — | Target system | On-prem |
| — | Auth | Userid/password *or* SSO — moot: the app attaches to a session and authenticates nothing (§8) |
| 1 | Execution model | Runs the generated VBScript. Collapses into 2 |
| 2 | Script format | **SAP GUI Scripting (VBScript)** |
| 3 | Form factor | **Local web UI** (§9) |
| 4 | Language | **Python** — Flask + openpyxl. No pyrfc, no RFC SDK |
| 5 | Existing users | **Add roles only.** Never modify existing attributes |
| 6 | Sandbox | **Available** — all first runs go there |
| 7 | Rollback | **Supported** — delta-based, see §8 |

### Remaining risk, not a question

**GUI scripting must be enabled server-side** (`sapgui/user_scripting = TRUE`) **and
client-side.** It is off by default and the server-side change needs Basis. If it turns out
to be disallowed in your landscape, this design does not work at all and we would be back to
the ABAP/BAPI route. Worth confirming on the sandbox **before** any code is written — it is
the one prerequisite that can invalidate everything downstream.

## 12. Testing approach (CLAUDE.md Rule 9)

Tests encode intent, not mechanics. **No test connects to a real SAP system.** The Runner is
tested against a fake session object that records every `findById` / `press` / `setFocus`
call, and the Emitter is pure text generation, so most of the app is testable offline.

Parsing and validation:
- A user appearing in 3 rows produces **one** user with 3 roles — the point of Layout B, and
  it regresses silently.
- A sheet with one invalid row emits **no script at all** — proves fail-closed.
- Header variants (`User ID` / `BNAME` / `Logon Name`) resolve to the same field.

Emission and execution:
- **Dry-run records zero write calls** on the fake session. This is the test protecting
  every accidental run.
- Generated script **appends** role rows and never clears the grid or writes to an occupied
  index (§7).
- A user whose status bar returns type `E` is journaled as **failed**, not succeeded — the
  GUI's silent-failure mode is the reason this test exists.
- A journal marking 3 of 5 users done drives exactly 2 users on resume.
- A session reporting a productive client aborts without acknowledgement.

Rollback — the highest-stakes tests:
- Rollback removes **only** roles journaled as newly added, and never one journaled as
  already present. A regression here strips roles users held before the run.
- Rollback deletes only users this run created.

## 13. Build order

1. `UserSpec` + validator (pure; no Excel, no SAP)
2. Excel parser + header inference
3. Manual entry mode
4. Emitter → `run.vbs` (pure text generation, fully testable offline)
5. Runner + journal readback against a **fake** session object
6. Guards, resume, and rollback script generation
7. Flask UI over the above
8. Sandbox pilot: 2-3 users, then one full sheet

**Step 0, before any of it:** confirm GUI scripting is enabled on the sandbox, server and
client. Everything above depends on it.

Steps 1-6 are fully testable without SAP. The UI is deliberately last — it is a thin shell
over logic that already works.
