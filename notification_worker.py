import os,time,json,hmac,hashlib
from datetime import datetime,timedelta
import requests
from app import create_app
from app.models import db,NotificationQueue
app=create_app();interval=max(10,int(os.getenv('NOTIFICATION_INTERVAL_SECONDS','30')));secret=os.getenv('WEBHOOK_SIGNING_SECRET','')
def deliver():
    now=datetime.utcnow();rows=NotificationQueue.query.filter(NotificationQueue.state.in_(['PENDING','RETRY']),NotificationQueue.next_attempt_at<=now).order_by(NotificationQueue.created_at).limit(100).all()
    for x in rows:
        if x.channel=='IN_APP':x.state='DELIVERED';x.delivered_at=now;continue
        if x.channel!='WEBHOOK' or not x.destination:x.state='FAILED';x.last_error='Unsupported channel or missing destination';continue
        body=json.dumps(x.payload or {},separators=(',',':')).encode();headers={'Content-Type':'application/json','User-Agent':'FleetTrack-360-Webhook/1.0'}
        if secret:headers['X-FleetTrack-Signature']='sha256='+hmac.new(secret.encode(),body,hashlib.sha256).hexdigest()
        try:
            x.last_attempt_at=now;x.attempt_count=(x.attempt_count or 0)+1;r=requests.post(x.destination,data=body,headers=headers,timeout=10);x.http_status=r.status_code
            if 200<=r.status_code<300:x.state='DELIVERED';x.delivered_at=datetime.utcnow();x.last_error=None
            else:raise RuntimeError(f'HTTP {r.status_code}')
        except Exception as e:
            x.last_error=str(e);x.state='FAILED' if x.attempt_count>=6 else 'RETRY';x.next_attempt_at=now+timedelta(minutes=min(60,2**x.attempt_count))
    db.session.commit()
if __name__=='__main__':
    with app.app_context():
        print(f'FleetTrack notification worker started, interval={interval}s',flush=True)
        while True:deliver();time.sleep(interval)
