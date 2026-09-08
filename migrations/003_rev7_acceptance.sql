BEGIN;
CREATE INDEX IF NOT EXISTS ix_acceptance_campaign_customer_state ON acceptance_campaign(customer_id,state);
CREATE INDEX IF NOT EXISTS ix_acceptance_item_campaign_state ON acceptance_item(campaign_id,state);
CREATE INDEX IF NOT EXISTS ix_endurance_run_campaign_state ON endurance_run(campaign_id,state);
COMMIT;
