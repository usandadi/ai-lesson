"""Canonical records. Everything downstream of the parser sees only these (spec §4)."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RoleSpec:
    name: str
    valid_from: str = ""  # YYYYMMDD; "" means let SAP default it
    valid_to: str = ""


@dataclass
class UserSpec:
    username: str
    last_name: str = ""
    first_name: str = ""
    email: str = ""
    user_type: str = "A"  # A=Dialog B=System C=Comm S=Service L=Reference
    user_group: str = ""
    valid_from: str = ""
    valid_to: str = ""
    initial_password: str = ""
    snc_name: str = ""  # SNC tab; e.g. p:CN=USER@REALM. Set at creation only — see spec §11 answer 5.
    roles: list[RoleSpec] = field(default_factory=list)
    # Spreadsheet rows this user was built from, so errors point at real rows.
    source_rows: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class Problem:
    """A validation or parse failure, addressed to a spreadsheet row where possible."""

    rows: tuple[int, ...]
    field: str
    message: str

    def describe(self) -> str:
        where = f"row {', '.join(str(r) for r in self.rows)}" if self.rows else "sheet"
        return f"{where}: {self.field} — {self.message}"
