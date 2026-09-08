# REV6 Operations

## Reports
Evidence exports are generated directly from tenant-scoped database queries. Route, stop, fuel and security CSV exports preserve UTC timestamps and never invent missing points.

## Backup
Run `python backup_restore.py` from the deployment host. SQLite uses the online backup API. PostgreSQL uses `pg_dump --format=custom`. Every backup receives a SHA-256 manifest. A separate restore test must be performed before marking a backup verified.

## Support bundle
Run `python support_bundle.py`. The bundle contains operational metadata and public configuration templates only. Secrets, database content, passwords, device tokens and customer telemetry are deliberately excluded.

## Administration
Only `fleet_admin` can create/disable users, create webhooks or replay failed notifications. The current signed-in administrator cannot disable the same account.

## MFA and recovery
REV6 adds persistent security-profile and reset-token models. Enabling live email delivery and final MFA enrollment remains deployment-specific because the production mail provider and encrypted secret store must be selected by the customer.
