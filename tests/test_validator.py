"""Validation intent (spec §6, §12): fail the whole run rather than half-provision."""

from sapapp.models import RoleSpec, UserSpec
from sapapp.validator import validate


def _user(**overrides):
    base = dict(username="JDOE", last_name="Doe", roles=[RoleSpec("Z_ROLE")], source_rows=[2])
    base.update(overrides)
    return UserSpec(**base)


def test_valid_user_produces_no_problems():
    assert validate([_user()]) == []


def test_username_over_twelve_chars_is_rejected():
    """BNAME is 12. SAP truncates or rejects; either way the wrong user gets the roles."""
    problems = validate([_user(username="THISNAMEISWAYTOOLONG")])
    assert any(p.field == "username" for p in problems)


def test_missing_surname_is_rejected():
    """SU01 will not save without one, so catching it here saves a failed run."""
    problems = validate([_user(last_name="")])
    assert any(p.field == "last_name" for p in problems)


def test_user_with_no_roles_is_rejected():
    """Creating a user with no access is never the intent of a role-assignment sheet."""
    problems = validate([_user(roles=[])])
    assert any(p.field == "roles" for p in problems)


def test_unknown_user_type_is_rejected():
    problems = validate([_user(user_type="X")])
    assert any(p.field == "user_type" for p in problems)


def test_backwards_validity_window_is_rejected():
    problems = validate([_user(valid_from="20261231", valid_to="20260101")])
    assert any("after" in p.message for p in problems)


def test_problems_carry_the_spreadsheet_row():
    """An operator fixing a 200-row sheet needs the row number, not just the field."""
    problems = validate([_user(username="", source_rows=[47])])
    assert problems[0].rows == (47,)
    assert "row 47" in problems[0].describe()


def test_one_bad_user_among_good_ones_still_reports():
    """Fail-closed: the app refuses the batch, so the bad row must surface."""
    users = [_user(), _user(username="BADUSER", last_name="", source_rows=[3])]
    problems = validate(users)
    assert len(problems) == 1
    assert problems[0].rows == (3,)
