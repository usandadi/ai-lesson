"""The single control-ID lookup table demanded by spec §7.

GUI Scripting addresses controls by path, and those paths vary by SAP GUI version,
screen variant, and user parameters. They live here and nowhere else so that a
landscape mismatch is one edit, not a hunt through templates.

THESE DEFAULTS ARE UNVERIFIED against your system. They are the common paths for
SU01 on recent SAP GUI for Windows, but the only way to know is to run the probe
(emitter.build_probe_script) against the sandbox and compare. The generated script
fails loudly on a missing control rather than clicking something else — see
FindOrFail in the emitted VBScript.
"""

SU01_IDS: dict[str, str] = {
    # Command box + main window
    "okcd": "wnd[0]/tbar[0]/okcd",
    "main": "wnd[0]",
    "statusbar": "wnd[0]/sbar",
    # SU01 initial screen
    "username_field": "wnd[0]/usr/ctxtSUID_ST_BNAME-BNAME",
    "btn_display": "wnd[0]/tbar[1]/btn[7]",
    "btn_change": "wnd[0]/tbar[1]/btn[6]",
    "btn_create": "wnd[0]/tbar[1]/btn[5]",
    "btn_save": "wnd[0]/tbar[0]/btn[11]",
    "btn_back": "wnd[0]/tbar[0]/btn[3]",
    "btn_delete": "wnd[0]/tbar[1]/btn[12]",  # rollback only
    # Address tab
    "tab_address": "wnd[0]/usr/tabsTABSTRIP1/tabpADDRESS",
    "field_last_name": "wnd[0]/usr/tabsTABSTRIP1/tabpADDRESS/ssubMAINAREA:SAPLSUID_MAINTENANCE:1900/subSUBSCREEN_ADDRESS:SAPLSZXX:0300/subCOUNTRY_SCREEN:SAPLSZXX:5000/txtADDR1_DATA-NAME_LAST",
    "field_first_name": "wnd[0]/usr/tabsTABSTRIP1/tabpADDRESS/ssubMAINAREA:SAPLSUID_MAINTENANCE:1900/subSUBSCREEN_ADDRESS:SAPLSZXX:0300/subCOUNTRY_SCREEN:SAPLSZXX:5000/txtADDR1_DATA-NAME_FIRST",
    "field_email": "wnd[0]/usr/tabsTABSTRIP1/tabpADDRESS/ssubMAINAREA:SAPLSUID_MAINTENANCE:1900/subSUBSCREEN_ADDRESS:SAPLSZXX:0300/subCOUNTRY_SCREEN:SAPLSZXX:5000/txtSZA5_D0700-SMTP_ADDR",
    # Logon data tab
    "tab_logondata": "wnd[0]/usr/tabsTABSTRIP1/tabpLOGONDATA",
    "field_password": "wnd[0]/usr/tabsTABSTRIP1/tabpLOGONDATA/ssubMAINAREA:SAPLSUID_MAINTENANCE:1100/pwdPASSWORD1",
    "field_password_repeat": "wnd[0]/usr/tabsTABSTRIP1/tabpLOGONDATA/ssubMAINAREA:SAPLSUID_MAINTENANCE:1100/pwdPASSWORD2",
    "field_user_type": "wnd[0]/usr/tabsTABSTRIP1/tabpLOGONDATA/ssubMAINAREA:SAPLSUID_MAINTENANCE:1100/cmbSUID_ST_NODE_LOGONDATA-LIC_TYPE",
    "field_user_group": "wnd[0]/usr/tabsTABSTRIP1/tabpLOGONDATA/ssubMAINAREA:SAPLSUID_MAINTENANCE:1100/ctxtSUID_ST_NODE_LOGONDATA-CLASS",
    # SNC tab — SSO identity, written at user creation only
    "tab_snc": "wnd[0]/usr/tabsTABSTRIP1/tabpSNC",
    "field_snc_name": "wnd[0]/usr/tabsTABSTRIP1/tabpSNC/ssubMAINAREA:SAPLSUID_MAINTENANCE:1500/ctxtSUID_ST_NODE_SNC-SNC_NAME",
    # Roles tab — an ALV grid shell
    "tab_roles": "wnd[0]/usr/tabsTABSTRIP1/tabpROLE",
    "role_grid": "wnd[0]/usr/tabsTABSTRIP1/tabpROLE/ssubMAINAREA:SAPLSUID_MAINTENANCE:1105/cntlGRIDCONTROL/shellcont/shell",
    "role_column": "AGR_NAME",
    "role_from_column": "FROM_DAT",
    "role_to_column": "TO_DAT",
}

# Controls the preflight probe must find before any write is attempted (spec §7).
#
# Split by screen, because the detail controls do not exist on the SU01 initial
# screen — they only appear once create/change mode is entered. Probing only the
# initial screen is what let a landscape mismatch through: the probe passed, and
# user creation then failed at save because the mandatory last-name write had been
# silently skipped. The probe enters create mode to check the second list.
PROBE_INITIAL_CONTROLS = [
    "okcd",
    "statusbar",
    "username_field",
    "btn_display",
    "btn_change",
    "btn_create",
    "btn_save",
]

# Reachable only inside create/change mode, and every one is load-bearing:
# without tab_address + field_last_name a user cannot be created at all, and
# without the role grid no role can be assigned.
#
# The optional field controls (first name, email, password, user group, SNC) are
# deliberately absent — a missing one skips optional data rather than failing the
# run, so probing them would turn a cosmetic gap into a hard stop.
PROBE_DETAIL_CONTROLS = [
    "tab_address",
    "field_last_name",
    "tab_logondata",
    "tab_roles",
    "role_grid",
]
