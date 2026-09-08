-- REV5 production data and installation schema
-- Apply to PostgreSQL in a controlled deployment transaction.
BEGIN;
CREATE INDEX IF NOT EXISTS ix_location_customer_vehicle_time ON location(customer_id,vehicle_id,sampled_at);
CREATE INDEX IF NOT EXISTS ix_security_event_customer_state_time ON security_event(customer_id,state,created_at);
CREATE INDEX IF NOT EXISTS ix_fuel_observation_customer_vehicle_time ON fuel_observation(customer_id,vehicle_id,sampled_at);
-- ORM-created REV5 tables are represented in app/models.py. Use the deployment migration runner after schema review.
COMMIT;
