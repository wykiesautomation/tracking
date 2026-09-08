from datetime import datetime
from .models import db,AcceptanceItem,ReleaseDecision
CHECKLIST=[
('FOUNDATION','PA-001','Production environment variables and secrets configured','No development secret, demo seed or local database in production.'),
('DATABASE','PA-010','PostgreSQL migrations applied and recorded','All migrations apply cleanly to a production-like copy.'),
('DATABASE','PA-011','Backup completed and SHA-256 manifest recorded','Backup artifact exists outside the application host.'),
('DATABASE','PA-012','Restore drill passed','Restore into an isolated target and verify critical row counts.'),
('SECURITY','PA-020','Tenant isolation review passed','Cross-tenant read and mutation attempts are denied.'),
('SECURITY','PA-021','Authentication and session controls reviewed','Password, lockout, session expiry and CSRF controls verified.'),
('SECURITY','PA-022','Authorization matrix passed','Viewer, operator, manager, installer and admin permissions tested.'),
('SECURITY','PA-023','OWASP ASVS security verification evidence attached','Security review references the chosen ASVS scope and findings.'),
('SECURITY','PA-024','Secrets and sensitive identifiers protected','Tokens, IMEI, ICCID and contact details are permission-controlled.'),
('API','PA-030','Device authentication and duplicate protection passed','Invalid tokens fail and duplicate sequences are idempotent.'),
('API','PA-031','Rate, payload and malformed-input tests passed','Oversized and invalid requests fail safely.'),
('TRACKING','PA-040','GPS quality filters verified with field evidence','Zero coordinates, poor accuracy and implausible speed are excluded.'),
('TRACKING','PA-041','Route gaps remain visible and unfilled','No fabricated line joins across telemetry gaps.'),
('TRACKING','PA-042','Stop and speed-event derivation verified','Stored evidence matches the configured thresholds.'),
('HARDWARE','PA-050','SIM808/SAMD21 tracker field test passed','Persistent token, APN, reconnect, GNSS and uploads verified.'),
('HARDWARE','PA-051','LILYGO board revision validated or feature remains locked','Only verified capabilities are customer-visible.'),
('HARDWARE','PA-052','12/24 V automotive interface safety verified','Fuse, reverse polarity, transient protection and protected scaling tested.'),
('HARDWARE','PA-053','Outputs boot OFF and simulation cannot energise outputs','Physical test evidence is required.'),
('FUEL','PA-060','Fuel calibration passed on each pilot tank','Raw, percent and litre points match measured fill evidence.'),
('FUEL','PA-061','Slosh and false-loss behaviour tested','Movement and stationary tests do not create nuisance critical events.'),
('WORKERS','PA-070','Offline and recovery worker endurance passed','Leases, heartbeats, deduplication and recovery remain stable.'),
('WORKERS','PA-071','Notification retries and dead-letter replay passed','HMAC, retry, terminal failure and replay tested.'),
('MAPS','PA-080','Production map provider and attribution verified','Provider terms, key restrictions, attribution and quotas are configured.'),
('REPORTS','PA-090','Evidence exports reconciled to database','Route, stop, fuel and security report counts match source records.'),
('PILOT','PA-100','Five-truck pilot completed','Each pilot truck completes the planned observation period.'),
('PILOT','PA-101','Pilot incidents resolved or formally accepted','No open blocking field issue remains.'),
('ENDURANCE','PA-110','Staged 160-device endurance test passed','Ingest, workers, database and notifications meet accepted thresholds.'),
('OPERATIONS','PA-120','Monitoring and alert ownership assigned','Worker, database, disk, backup and HTTP monitoring have owners.'),
('OPERATIONS','PA-121','Installer and administrator manuals reviewed','Operational users confirm procedures are usable.'),
('OPERATIONS','PA-122','Rollback plan tested','Deployment rollback preserves database integrity.'),
]
def seed_campaign(campaign):
 for cat,code,title,desc in CHECKLIST:
  db.session.add(AcceptanceItem(campaign_id=campaign.id,category=cat,code=code,title=title,description=desc,required=True,blocking=True))
def stats(campaign):
 total=len(campaign.items);passed=sum(x.state=='PASS' for x in campaign.items);failed=sum(x.state=='FAIL' for x in campaign.items);untested=sum(x.state in ('NOT_TESTED','IN_PROGRESS') for x in campaign.items);blocking=sum(x.blocking and x.state!='PASS' for x in campaign.items)
 return dict(total=total,passed=passed,failed=failed,untested=untested,blocking=blocking)
def can_accept(campaign):return stats(campaign)['blocking']==0 and len(campaign.items)>0
