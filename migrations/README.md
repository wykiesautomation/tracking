# FleetTrack schema migrations

REV5 introduces versioned SQL migration files for production PostgreSQL. Apply migrations through the controlled deployment job after taking and validating a database backup. SQLite development still uses `db.create_all()`.
