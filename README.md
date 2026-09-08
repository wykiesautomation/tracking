# FleetTrack 360 GitHub Ready REV7

Cumulative 100% acceptance framework baseline with real Leaflet maps, route/map surfaces, fleet workflows and production deployment files.

## Scheduled workers
Run the web app and both workers as separate processes:

```powershell
python -m flask --app wsgi:app run --host=127.0.0.1 --port=5000
python worker.py
python notification_worker.py
```

In production, deploy the web, correlation worker and notification worker separately. Do not start the scheduler inside Gunicorn workers.

## REV7 production-data checks
```powershell
python migration_check.py
```
Fuel calibrations remain DRAFT until monotonic multi-point validation succeeds. Installations remain uncommissioned until all required checks and safety gates pass.

## REV7 operational commands
```powershell
python backup_restore.py
python support_bundle.py
python migration_check.py
```
Backup files, support bundles, local databases and secrets are excluded from Git.

## Production acceptance
Create an acceptance campaign in the web UI. The release cannot be accepted while any blocking checklist item lacks a PASS result. Field and security evidence must be real.

Authorized synthetic endurance example:
```powershell
python endurance_harness.py --url https://staging.example.com --token-file test_tokens.txt --rounds 10 --workers 20
```
Never use production customer tokens in a shared test file.
