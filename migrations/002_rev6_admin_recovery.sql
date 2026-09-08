BEGIN;
CREATE INDEX IF NOT EXISTS ix_report_run_customer_created ON report_run(customer_id,created_at);
CREATE INDEX IF NOT EXISTS ix_backup_job_customer_created ON backup_job(customer_id,created_at);
CREATE INDEX IF NOT EXISTS ix_notification_queue_customer_state ON notification_queue(customer_id,state);
COMMIT;
