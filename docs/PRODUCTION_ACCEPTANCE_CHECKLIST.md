# FleetTrack 360 Production Acceptance Checklist

The application is a production candidate until every blocking checklist item has measured evidence and a PASS result. Code completion alone does not constitute production acceptance.

## Required acceptance domains
- Production configuration and migrations
- Backup and isolated restore drill
- Tenant isolation, authentication, authorization and application-security review
- Device API authentication, duplicate handling, malformed input and rate testing
- GPS quality, route gaps, stop detection and sustained speed events
- SIM808/SAMD21 physical field verification
- LILYGO capability validation or explicit feature lock
- 12/24 V automotive interface and safe-output testing
- Fuel calibration, slosh and false-loss tests
- Worker lease, heartbeat, deduplication, recovery and delivery endurance
- Map-provider production contract, quotas and attribution
- Evidence-export reconciliation
- Five-truck pilot
- Staged 160-device endurance test
- Monitoring ownership, manuals and tested rollback

## Release rule
`ACCEPTED` is blocked while any blocking item is not `PASS`. `NOT_APPLICABLE` does not satisfy a blocking item unless the checklist is formally revised and approved.
