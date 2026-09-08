from datetime import datetime,timedelta
from math import radians,sin,cos,asin,sqrt
from sqlalchemy.exc import IntegrityError
from .models import db,Device,DeviceState,Location,Geofence,SecurityEvent,NotificationQueue,CorrelationRun

def state_for(device,now,delayed_minutes=5,offline_minutes=15):
    if not device.last_seen:return 'NEVER_SEEN'
    age=(now-device.last_seen).total_seconds()
    if age<=delayed_minutes*60:return 'ONLINE'
    if age<=offline_minutes*60:return 'DELAYED'
    return 'OFFLINE'

def distance_m(lat1,lon1,lat2,lon2):
    r=6371000; p1=radians(lat1);p2=radians(lat2);dp=radians(lat2-lat1);dl=radians(lon2-lon1)
    a=sin(dp/2)**2+cos(p1)*cos(p2)*sin(dl/2)**2
    return 2*r*asin(min(1,a**0.5))

def open_event(customer_id,vehicle_id,device_id,event_type,severity,detail):
    existing=SecurityEvent.query.filter(SecurityEvent.customer_id==customer_id,SecurityEvent.vehicle_id==vehicle_id,SecurityEvent.event_type==event_type,SecurityEvent.state.in_(['OPEN','ACKNOWLEDGED'])).first()
    if existing:return existing,False
    e=SecurityEvent(customer_id=customer_id,vehicle_id=vehicle_id,event_type=event_type,severity=severity,state='OPEN',detail={**detail,'device_id':device_id});db.session.add(e);db.session.flush()
    db.session.add(NotificationQueue(customer_id=customer_id,event_type=event_type,event_id=str(e.id),channel='IN_APP',destination='CONTROL_CENTRE',payload={'event_id':e.id,'vehicle_id':vehicle_id,'severity':severity,'detail':detail}))
    return e,True

def resolve_open(customer_id,vehicle_id,event_type,resolution):
    rows=SecurityEvent.query.filter(SecurityEvent.customer_id==customer_id,SecurityEvent.vehicle_id==vehicle_id,SecurityEvent.event_type==event_type,SecurityEvent.state.in_(['OPEN','ACKNOWLEDGED'])).all()
    for e in rows:e.state='RESOLVED';e.resolution=resolution
    return len(rows)

def evaluate_devices(now=None,delayed_minutes=5,offline_minutes=15):
    now=now or datetime.utcnow();run=CorrelationRun(worker_name='fleet-correlation',started_at=now);db.session.add(run);db.session.flush();events=0;queued_before=NotificationQueue.query.count()
    try:
        for d in Device.query.filter_by(enabled=True).all():
            run.devices_evaluated+=1;new=state_for(d,now,delayed_minutes,offline_minutes);st=DeviceState.query.filter_by(device_id=d.id).first()
            if not st:st=DeviceState(customer_id=d.customer_id,device_id=d.id,current_state=new,previous_state=None,state_changed_at=now);db.session.add(st)
            old=st.current_state
            if old!=new:st.previous_state=old;st.current_state=new;st.state_changed_at=now
            st.last_evaluated_at=now
            if d.vehicle_id:
                if new=='DELAYED':
                    _,created=open_event(d.customer_id,d.vehicle_id,d.id,'TRACKER DELAYED','WARNING',{'last_seen':d.last_seen.isoformat()+'Z' if d.last_seen else None,'threshold_minutes':delayed_minutes});events+=int(created)
                elif new=='OFFLINE':
                    resolve_open(d.customer_id,d.vehicle_id,'TRACKER DELAYED','Escalated to tracker offline')
                    _,created=open_event(d.customer_id,d.vehicle_id,d.id,'TRACKER OFFLINE','CRITICAL',{'last_seen':d.last_seen.isoformat()+'Z' if d.last_seen else None,'threshold_minutes':offline_minutes});events+=int(created)
                elif new=='ONLINE':
                    recovered=resolve_open(d.customer_id,d.vehicle_id,'TRACKER DELAYED','Tracker communication recovered')+resolve_open(d.customer_id,d.vehicle_id,'TRACKER OFFLINE','Tracker communication recovered')
                    if recovered:
                        _,created=open_event(d.customer_id,d.vehicle_id,d.id,'TRACKER COMMUNICATION RECOVERED','INFO',{'recovered_at':now.isoformat()+'Z','previous_state':old});events+=int(created)
                latest=Location.query.filter_by(customer_id=d.customer_id,vehicle_id=d.vehicle_id,quality='GOOD').order_by(Location.sampled_at.desc()).first()
                if latest and new in ('ONLINE','DELAYED'):
                    for g in Geofence.query.filter_by(customer_id=d.customer_id,active=True).all():
                        inside=distance_m(latest.latitude,latest.longitude,g.latitude,g.longitude)<=g.radius_m
                        breach=(g.kind=='KEEP_IN' and not inside) or (g.kind in ('KEEP_OUT','HIGH_RISK') and inside)
                        et=f'GEOFENCE {g.kind} BREACH: {g.name}'
                        if breach:
                            _,created=open_event(d.customer_id,d.vehicle_id,d.id,et,g.severity,{'geofence_id':g.id,'latitude':latest.latitude,'longitude':latest.longitude,'sampled_at':latest.sampled_at.isoformat()+'Z'});events+=int(created)
                        else:resolve_open(d.customer_id,d.vehicle_id,et,'Vehicle position returned to permitted state')
        run.events_created=events;run.notifications_queued=NotificationQueue.query.count()-queued_before;run.completed_at=datetime.utcnow();run.state='COMPLETED';db.session.commit();return run
    except Exception as e:
        db.session.rollback();run=CorrelationRun(worker_name='fleet-correlation',started_at=now,completed_at=datetime.utcnow(),state='FAILED',error=str(e));db.session.add(run);db.session.commit();raise
