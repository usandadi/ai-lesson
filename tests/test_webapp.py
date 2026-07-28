"""Web UI intent (spec §9)."""

import pytest
from openpyxl import Workbook

from sapapp import webapp


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(webapp, "RUNS_DIR", str(tmp_path / "runs"))
    webapp._runs.clear()
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


def _sheet(tmp_path, rows):
    book = Workbook()
    sheet = book.active
    for row in rows:
        sheet.append(row)
    path = tmp_path / "in.xlsx"
    book.save(path)
    return path


def test_upload_shows_mapping_and_offers_the_script(client, tmp_path):
    path = _sheet(
        tmp_path,
        [["User ID", "Last Name", "Role"], ["JDOE", "Doe", "Z_FIN"], ["JDOE", "Doe", "Z_MM"]],
    )
    with open(path, "rb") as handle:
        response = client.post(
            "/upload", data={"sheet": (handle, "in.xlsx")}, follow_redirects=True
        )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Z_FIN, Z_MM" in body  # grouped into one user
    assert "ProcessUser" in body  # script rendered for review


def test_invalid_sheet_emits_no_script_at_all(client, tmp_path):
    """Fail-closed (spec §6): the operator must not be able to run a partial batch."""
    path = _sheet(tmp_path, [["User ID", "Last Name", "Role"], ["JDOE", "", "Z_FIN"]])
    with open(path, "rb") as handle:
        response = client.post(
            "/upload", data={"sheet": (handle, "in.xlsx")}, follow_redirects=True
        )
    body = response.get_data(as_text=True)

    assert "problem(s)" in body
    assert "ProcessUser" not in body
    assert "last_name" in body


def test_execute_is_refused_while_problems_remain(client, tmp_path):
    """Belt and braces: the UI hides the button, and the route refuses anyway."""
    path = _sheet(tmp_path, [["User ID", "Last Name", "Role"], ["JDOE", "", "Z_FIN"]])
    with open(path, "rb") as handle:
        client.post("/upload", data={"sheet": (handle, "in.xlsx")}, follow_redirects=True)
    run_id = next(iter(webapp._runs))

    response = client.post(f"/run/{run_id}/execute", data={"mode": "execute"})
    assert response.status_code == 400


def test_manual_entry_uses_the_same_pipeline(client):
    """Requirement 3 — typed users get the same validator and emitter as a sheet."""
    response = client.post(
        "/manual",
        data={"entries": "JDOE | Doe | j.doe@example.com | Z_FIN, Z_MM"},
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)

    assert "JDOE" in body
    assert "Z_FIN, Z_MM" in body
    assert "ProcessUser" in body
