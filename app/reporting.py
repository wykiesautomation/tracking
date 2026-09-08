import csv,io
from datetime import datetime
from .models import Location,StopEvent,SpeedEvent,SecurityEvent,FuelObservation,Device

def csv_bytes(headers,rows):
 out=io.StringIO(newline='');writer=csv.writer(out);writer.writerow(headers);writer.writerows(rows);return out.getvalue().encode('utf-8-sig')
def route_report(customer_id,vehicle_id,start,end):
 q=Location.query.filter(Location.customer_id==customer_id,Location.vehicle_id==vehicle_id,Location.sampled_at>=start,Location.sampled_at<=end).order_by(Location.sampled_at)
 rows=[[x.sampled_at.isoformat()+'Z',x.latitude,x.longitude,x.accuracy_m,x.speed_kmh,x.heading_deg,x.quality] for x in q.all()]
 return csv_bytes(['sampled_at_utc','latitude','longitude','accuracy_m','speed_kmh','heading_deg','quality'],rows),len(rows)
def stop_report(customer_id,vehicle_id,start,end):
 rows=StopEvent.query.filter(StopEvent.customer_id==customer_id,StopEvent.vehicle_id==vehicle_id,StopEvent.started_at>=start,StopEvent.started_at<=end).order_by(StopEvent.started_at).all()
 values=[[x.started_at.isoformat()+'Z',x.ended_at.isoformat()+'Z' if x.ended_at else '',x.duration_seconds,x.reason] for x in rows]
 return csv_bytes(['started_at_utc','ended_at_utc','duration_seconds','reason'],values),len(values)
def security_report(customer_id,start,end):
 rows=SecurityEvent.query.filter(SecurityEvent.customer_id==customer_id,SecurityEvent.created_at>=start,SecurityEvent.created_at<=end).order_by(SecurityEvent.created_at).all()
 values=[[x.created_at.isoformat()+'Z',x.vehicle_id,x.event_type,x.severity,x.state,x.resolution or ''] for x in rows]
 return csv_bytes(['created_at_utc','vehicle_id','event_type','severity','state','resolution'],values),len(values)
def fuel_report(customer_id,vehicle_id,start,end):
 rows=FuelObservation.query.filter(FuelObservation.customer_id==customer_id,FuelObservation.vehicle_id==vehicle_id,FuelObservation.sampled_at>=start,FuelObservation.sampled_at<=end).order_by(FuelObservation.sampled_at).all()
 values=[[x.sampled_at.isoformat()+'Z',x.litres,x.percent,x.quality] for x in rows]
 return csv_bytes(['sampled_at_utc','litres','percent','quality'],values),len(values)
