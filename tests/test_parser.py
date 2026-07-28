"""Parser intent (spec §12).

These encode WHY the parsing behaves as it does, not just that it runs.
"""

from openpyxl import Workbook

from sapapp.excel_parser import (
    find_header_row,
    match_header,
    normalise_date,
    parse_file,
    parse_workbook,
)


def _sheet(tmp_path, rows, name="in.xlsx"):
    book = Workbook()
    sheet = book.active
    for row in rows:
        sheet.append(row)
    path = tmp_path / name
    book.save(path)
    return str(path)


def test_repeated_username_becomes_one_user_with_many_roles(tmp_path):
    """Layout B. The whole point: 3 rows for one person is one user, never three.

    This regresses silently — three users would each be created with one role,
    and SU01 would happily accept the first and reject the duplicates.
    """
    path = _sheet(
        tmp_path,
        [
            ["User ID", "Last Name", "Role"],
            ["JDOE", "Doe", "Z_FIN_DISPLAY"],
            ["JDOE", "Doe", "Z_FIN_POST"],
            ["JDOE", "Doe", "Z_MM_DISPLAY"],
        ],
    )
    result = parse_workbook(path)

    assert len(result.users) == 1
    user = result.users[0]
    assert user.username == "JDOE"
    assert [r.name for r in user.roles] == ["Z_FIN_DISPLAY", "Z_FIN_POST", "Z_MM_DISPLAY"]
    assert user.source_rows == [2, 3, 4]


def test_delimited_role_cell_becomes_many_roles(tmp_path):
    """Layout A. Same user, same outcome, different sheet convention."""
    path = _sheet(
        tmp_path,
        [
            ["User", "Surname", "Roles"],
            ["JDOE", "Doe", "Z_FIN_DISPLAY; Z_FIN_POST, Z_MM_DISPLAY"],
        ],
    )
    result = parse_workbook(path)

    assert len(result.users) == 1
    assert [r.name for r in result.users[0].roles] == [
        "Z_FIN_DISPLAY",
        "Z_FIN_POST",
        "Z_MM_DISPLAY",
    ]


def test_header_variants_resolve_to_the_same_field():
    """Requirement 4: the schema comes from the header, whatever the site calls it."""
    for spelling in ("User ID", "user_id", "USERID", "BNAME", "Logon Name", "SAP User"):
        assert match_header(spelling) == "username", spelling
    for spelling in ("Role", "Roles", "Role Name", "AGR_NAME", "Single Role"):
        assert match_header(spelling) == "roles", spelling


def test_header_row_is_found_below_a_title_banner():
    """Real exports carry title rows; assuming row 1 would map every column wrong."""
    rows = [
        ["Quarterly access request", None, None],
        [None, None, None],
        ["User ID", "Last Name", "Role"],
        ["JDOE", "Doe", "Z_ROLE"],
    ]
    assert find_header_row(rows) == 2


def test_conflicting_attribute_across_rows_is_reported_not_silently_merged(tmp_path):
    """Two rows disagreeing about one person is a data problem the operator must see.

    Picking one silently would provision a user with an address nobody approved.
    """
    path = _sheet(
        tmp_path,
        [
            ["User ID", "Last Name", "Email", "Role"],
            ["JDOE", "Doe", "j.doe@example.com", "Z_A"],
            ["JDOE", "Doe", "jane.doe@example.com", "Z_B"],
        ],
    )
    result = parse_workbook(path)

    assert len(result.users) == 1
    assert any("conflicting" in p.message for p in result.problems)


def test_missing_required_column_is_reported(tmp_path):
    path = _sheet(tmp_path, [["User ID", "Last Name"], ["JDOE", "Doe"]])
    result = parse_workbook(path)
    assert any(p.field == "roles" for p in result.problems)


def test_csv_reaches_the_same_inference_as_xlsx(tmp_path):
    """Real SAP templates ship as CSV; both formats must land on one code path."""
    path = tmp_path / "in.csv"
    path.write_text(
        "USERID,FNAME,LNAME,EMAIL,ROLE\nTEST_GRC01,GRC01,TEST,a@b.com,Z_FIN\n",
        encoding="utf-8-sig",  # Excel writes a BOM
    )
    result = parse_file(str(path))

    assert result.mapping["username"] == "USERID"
    assert result.mapping["last_name"] == "LNAME"
    assert result.mapping["first_name"] == "FNAME"
    assert len(result.users) == 1
    assert result.users[0].username == "TEST_GRC01"
    assert result.users[0].last_name == "TEST"


def test_snc_name_is_captured_from_the_sheet(tmp_path):
    """These users log on via SNC, so the identity is not optional decoration."""
    path = tmp_path / "in.csv"
    path.write_text(
        "USERID,LNAME,SNC_NAME,ROLE\nTEST_GRC01,TEST,p:CN=TEST_GRC01@HPHOOD.COM,Z_FIN\n",
        encoding="utf-8-sig",
    )
    result = parse_file(str(path))

    assert result.mapping["snc_name"] == "SNC_NAME"
    assert result.users[0].snc_name == "p:CN=TEST_GRC01@HPHOOD.COM"
    assert "SNC_NAME" not in result.unmapped


def test_abbreviated_name_headers_resolve():
    """SAP's own template uses FNAME/LNAME; missing these failed every row."""
    assert match_header("LNAME") == "last_name"
    assert match_header("FNAME") == "first_name"


def test_dates_normalise_to_sap_format():
    assert normalise_date("2026-07-28") == "20260728"
    assert normalise_date("28.07.2026") == "20260728"
    assert normalise_date("") == ""
    # Unparseable text survives to the validator so it is reported against a real row.
    assert normalise_date("next monday") == "next monday"
