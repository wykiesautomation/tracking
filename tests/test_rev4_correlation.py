from datetime import datetime,timedelta
import os
os.environ['SEED_DEMO']='true'
from app import create_app
from app.models import db,Device,DeviceState,SecurityEvent
from app.correlation import evaluate_devices

def test_offline_dedup_and_recovery():
    app=create_app(True)
    with app.app_context():
        d=Device.query.first();d.last_seen=datetime.utcnow()-timedelta(minutes=20);db.session.commit()
        evaluate_devices();evaluate_devices()
        assert DeviceState.query.filter_by(device_id=d.id).first().current_state=='OFFLINE'
        assert SecurityEvent.query.filter_by(vehicle_id=d.vehicle_id,event_type='TRACKER OFFLINE',state='OPEN').count()==1
        d.last_seen=datetime.utcnow();db.session.commit();evaluate_devices()
        assert DeviceState.query.filter_by(device_id=d.id).first().current_state=='ONLINE'
        assert SecurityEvent.query.filter_by(vehicle_id=d.vehicle_id,event_type='TRACKER OFFLINE',state='RESOLVED').count()>=1
