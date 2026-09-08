import os,time,socket,uuid
from datetime import datetime,timedelta
from app import create_app
from app.models import db,WorkerLease
from app.correlation import evaluate_devices
app=create_app();owner=f'{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}'
interval=max(15,int(os.getenv('CORRELATION_INTERVAL_SECONDS','60')));lease_seconds=max(interval*3,180)
def acquire(now):
    lease=WorkerLease.query.filter_by(name='fleet-correlation').first()
    if not lease:lease=WorkerLease(name='fleet-correlation');db.session.add(lease);db.session.flush()
    if lease.owner and lease.owner!=owner and lease.expires_at and lease.expires_at>now:return None
    lease.owner=owner;lease.acquired_at=now;lease.heartbeat_at=now;lease.expires_at=now+timedelta(seconds=lease_seconds);db.session.commit();return lease
def cycle():
    now=datetime.utcnow();lease=acquire(now)
    if not lease:return
    try:
        lease.last_run_started_at=now;lease.heartbeat_at=now;lease.expires_at=now+timedelta(seconds=lease_seconds);db.session.commit()
        run=evaluate_devices(now=now,delayed_minutes=int(os.getenv('DELAYED_MINUTES','5')),offline_minutes=int(os.getenv('OFFLINE_MINUTES','15')))
        lease=WorkerLease.query.filter_by(name='fleet-correlation').first();lease.last_run_completed_at=datetime.utcnow();lease.heartbeat_at=datetime.utcnow();lease.expires_at=datetime.utcnow()+timedelta(seconds=lease_seconds);lease.processed_count=(lease.processed_count or 0)+run.devices_evaluated;lease.last_error=None;db.session.commit()
    except Exception as e:
        db.session.rollback();lease=WorkerLease.query.filter_by(name='fleet-correlation').first()
        if lease:lease.last_error=str(e);lease.heartbeat_at=datetime.utcnow();db.session.commit()
if __name__=='__main__':
    with app.app_context():
        print(f'FleetTrack worker started: {owner}, interval={interval}s',flush=True)
        while True:cycle();time.sleep(interval)
