"""Pure validation over UserSpec[] (spec §6). No I/O.

Runs over the whole dataset before anything is emitted: one bad row fails the run
rather than producing a partially-valid script.
"""

import re

from .models import Problem, UserSpec

USER_TYPES = {"A", "B", "C", "S", "L"}
MAX_USERNAME = 12  # BNAME
MAX_ROLE = 30  # AGR_NAME
MAX_SNC_NAME = 255  # SNC printable name

_USERNAME_OK = re.compile(r"^[A-Z0-9_.\-]+$")
_EMAIL_OK = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DATE_OK = re.compile(r"^\d{8}$")


def validate(users: list[UserSpec]) -> list[Problem]:
    problems: list[Problem] = []

    if not users:
        problems.append(Problem((), "sheet", "no users found"))
        return problems

    for user in users:
        rows = tuple(user.source_rows)
        problems.extend(_validate_user(user, rows))

    return problems


def _validate_user(user: UserSpec, rows: tuple[int, ...]) -> list[Problem]:
    found: list[Problem] = []

    name = user.username
    if not name:
        found.append(Problem(rows, "username", "missing"))
    else:
        if len(name) > MAX_USERNAME:
            found.append(
                Problem(rows, "username", f"'{name}' is {len(name)} chars, max {MAX_USERNAME}")
            )
        if not _USERNAME_OK.match(name):
            found.append(Problem(rows, "username", f"'{name}' has characters SAP will reject"))

    if not user.last_name:
        found.append(Problem(rows, "last_name", "missing — SU01 will not save without a surname"))

    if user.user_type not in USER_TYPES:
        found.append(
            Problem(rows, "user_type", f"'{user.user_type}' not one of {sorted(USER_TYPES)}")
        )

    if user.email and not _EMAIL_OK.match(user.email):
        found.append(Problem(rows, "email", f"'{user.email}' is not a valid address"))

    # Length only. SNC names vary by security product (p:CN=..., p:user@REALM, and
    # others), so format-checking them here would reject valid values.
    if user.snc_name and len(user.snc_name) > MAX_SNC_NAME:
        found.append(
            Problem(rows, "snc_name", f"{len(user.snc_name)} chars, max {MAX_SNC_NAME}")
        )

    found.extend(_validate_dates(rows, "user validity", user.valid_from, user.valid_to))

    if not user.roles:
        found.append(Problem(rows, "roles", "no roles — nothing to assign"))

    seen: set[str] = set()
    for role in user.roles:
        if not role.name:
            found.append(Problem(rows, "role", "empty role name"))
            continue
        if len(role.name) > MAX_ROLE:
            found.append(
                Problem(rows, "role", f"'{role.name}' is {len(role.name)} chars, max {MAX_ROLE}")
            )
        if role.name in seen:
            found.append(Problem(rows, "role", f"'{role.name}' listed twice"))
        seen.add(role.name)
        found.extend(_validate_dates(rows, f"role {role.name}", role.valid_from, role.valid_to))

    return found


def _validate_dates(rows: tuple[int, ...], label: str, start: str, end: str) -> list[Problem]:
    found: list[Problem] = []
    for value, which in ((start, "from"), (end, "to")):
        if value and not _DATE_OK.match(value):
            found.append(Problem(rows, label, f"{which} date '{value}' is not YYYYMMDD"))
    if start and end and _DATE_OK.match(start) and _DATE_OK.match(end) and start > end:
        found.append(Problem(rows, label, f"valid-from {start} is after valid-to {end}"))
    return found
