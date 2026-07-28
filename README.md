# ai-lesson

## SAP user/role provisioning app

Reads users and roles from Excel (or a few typed by hand), infers the schema from the
header row, generates SAP GUI Scripting VBScript, and runs it against a SAP GUI session
you are already logged into. Design spec: [SAP-User-Role-App.md](SAP-User-Role-App.md).

```
pip install -r requirements.txt
python -m sapapp.webapp        # http://127.0.0.1:5000
python -m pytest tests -q
```

### Before the first real run

1. Confirm GUI scripting is enabled — server (`sapgui/user_scripting = TRUE`) and client
   (SAP GUI → Options → Accessibility & Scripting → Scripting), with both "Notify when a
   script..." boxes cleared.
2. Log into the sandbox in SAP GUI and leave the session open.
3. Use **Run control probe** in the UI. The SU01 control paths in
   [sapapp/screen_ids.py](sapapp/screen_ids.py) are unverified defaults until the probe
   confirms them against your system.
4. Dry-run first. It reads existing roles and reports what it would do, writing nothing.
