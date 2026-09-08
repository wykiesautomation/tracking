from datetime import datetime,timedelta
from flask import Blueprint,render_template,request,redirect,url_for,flash,jsonify,current_app,send_file
from flask_login import login_user,logout_user,login_required,current_user
from sqlalchemy import func
from .models import *
bp=Blueprint('main',__name__)
def cid():return current_user.customer_id
def audit(action,kind,eid,detail=None):db.session.add(AuditEvent(customer_id=cid(),user_id=current_user.id,action=action,entity_type=kind,entity_id=str(eid),detail=detail or {}))
@bp.route('/login',methods=['GET','POST'])
def login():
 if current_user.is_authenticated:return redirect(url_for('main.dashboard'))
 if request.method=='POST':
  u=User.query.filter(func.lower(User.email)==request.form.get('email','').lower()).first()
  if u and u.check_password(request.form.get('password','')):login_user(u);return redirect(url_for('main.dashboard'))
 return render_template('login.html')
@bp.get('/logout')
def logout():logout_user();return redirect(url_for('main.login'))
@bp.get('/')
@login_required
def dashboard():
 vehicles=Vehicle.query.filter_by(customer_id=cid()).all();rows=[];cut=datetime.utcnow()-timedelta(minutes=15)
 for v in vehicles:rows.append((v,Location.query.filter_by(customer_id=cid(),vehicle_id=v.id).order_by(Location.sampled_at.desc()).first(),Device.query.filter_by(customer_id=cid(),vehicle_id=v.id).first()))
 events=SecurityEvent.query.filter(SecurityEvent.customer_id==cid(),SecurityEvent.state.in_(['OPEN','ACKNOWLEDGED'])).all();return render_template('dashboard.html',rows=rows,events=events,total=len(vehicles),driving=sum(1 for _,p,_ in rows if p and (p.speed_kmh or 0)>=5),offline=sum(1 for _,_,d in rows if not d or not d.last_seen or d.last_seen<cut))
@bp.get('/tracking')
@login_required
def tracking():return render_template('tracking.html',rows=[])
@bp.get('/vehicles')
@login_required
def vehicles():return render_template('generic.html',title='Fleet Registry')
@bp.get('/vehicles/<int:vid>')
@login_required
def vehicle_detail(vid):return render_template('vehicle_detail.html',v=Vehicle.query.filter_by(id=vid,customer_id=cid()).first_or_404())
@bp.get('/drivers')
@login_required
def drivers():return render_template('generic.html',title='Drivers')
@bp.get('/assignments')
@login_required
def assignments():return render_template('generic.html',title='Assignments')
@bp.get('/devices')
@login_required
def devices():return render_template('installation_studio.html',installations=AutomotiveInstallationProfile.query.filter_by(customer_id=cid()).order_by(AutomotiveInstallationProfile.created_at.desc()).all(),vehicles=Vehicle.query.filter_by(customer_id=cid()).all(),devices=Device.query.filter_by(customer_id=cid()).all())
@bp.get('/security')
@login_required
def security():return render_template('generic.html',title='Security Events')
@bp.get('/fuel')
@login_required
def fuel():return render_template('fuel_studio.html',profiles=FuelCalibrationProfile.query.filter_by(customer_id=cid()).order_by(FuelCalibrationProfile.created_at.desc()).all(),vehicles=Vehicle.query.filter_by(customer_id=cid()).all())
@bp.get('/reports')
@login_required
def reports():return render_template('reports_admin.html',vehicles=Vehicle.query.filter_by(customer_id=cid()).all(),runs=ReportRun.query.filter_by(customer_id=cid()).order_by(ReportRun.created_at.desc()).limit(50).all())
@bp.get('/geofences')
@login_required
def geofences():return render_template('generic.html',title='Geofences')
@bp.get('/map-data')
@login_required
def map_data():
 data=[]
 for v in Vehicle.query.filter_by(customer_id=cid()).all():
  p=Location.query.filter_by(customer_id=cid(),vehicle_id=v.id).order_by(Location.sampled_at.desc()).first()
  if p:data.append({'vehicle_id':v.id,'fleet_no':v.fleet_no,'registration':v.registration,'latitude':p.latitude,'longitude':p.longitude,'speed_kmh':p.speed_kmh,'state':'ONLINE'})
 return jsonify(data=data,tile_url=current_app.config['MAP_TILE_URL'],attribution=current_app.config['MAP_ATTRIBUTION'],max_zoom=current_app.config['MAP_MAX_ZOOM'])
@bp.get('/geofence-data')
@login_required
def geofence_data():return jsonify(data=[])
@bp.get('/settings')
@login_required
def settings():return render_template('settings.html',audits=AuditEvent.query.filter_by(customer_id=cid()).order_by(AuditEvent.created_at.desc()).limit(50).all(),worker=WorkerLease.query.filter_by(name='fleet-correlation').first(),runs=CorrelationRun.query.order_by(CorrelationRun.started_at.desc()).limit(15).all(),notifications=NotificationQueue.query.filter_by(customer_id=cid()).order_by(NotificationQueue.created_at.desc()).limit(50).all())

@bp.post('/notifications/<int:nid>/retry')
@login_required
def retry_notification(nid):
    n=NotificationQueue.query.filter_by(id=nid,customer_id=cid()).first_or_404();n.state='PENDING';n.next_attempt_at=datetime.utcnow();n.last_error=None;audit('notification.retry','NotificationQueue',n.id);db.session.commit();return redirect(url_for('main.settings'))

@bp.route('/fuel-calibrations',methods=['POST'])
@login_required
def create_fuel_calibration():
 p=FuelCalibrationProfile(customer_id=cid(),vehicle_id=request.form.get('vehicle_id',type=int),name=request.form['name'],sensor_type=request.form['sensor_type'],electrical_min=request.form.get('electrical_min',type=float),electrical_max=request.form.get('electrical_max',type=float),engineering_unit=request.form.get('engineering_unit','V'),tank_capacity_l=request.form.get('tank_capacity_l',type=float),tank_shape=request.form.get('tank_shape','CUSTOM'),filtering_seconds=request.form.get('filtering_seconds',30,type=int),deadband_l=request.form.get('deadband_l',2,type=float),slosh_suppression=bool(request.form.get('slosh_suppression')));db.session.add(p);db.session.flush();audit('fuel.profile.created','FuelCalibrationProfile',p.id);db.session.commit();flash('Fuel calibration profile created. Add verified points before approval.','ok');return redirect(url_for('main.fuel'))
@bp.route('/fuel-calibrations/<int:pid>/points',methods=['POST'])
@login_required
def add_calibration_point(pid):
 p=FuelCalibrationProfile.query.filter_by(id=pid,customer_id=cid()).first_or_404()
 if p.approved:return ('Approved profiles are locked.',409)
 x=FuelCalibrationPoint(profile_id=p.id,sequence=request.form.get('sequence',type=int),raw_value=request.form.get('raw_value',type=float),percent=request.form.get('percent',type=float),litres=request.form.get('litres',type=float),note=request.form.get('note'));db.session.add(x);audit('fuel.point.added','FuelCalibrationProfile',p.id);db.session.commit();return redirect(url_for('main.calibration_detail',pid=p.id))
@bp.get('/fuel-calibrations/<int:pid>')
@login_required
def calibration_detail(pid):return render_template('calibration_detail.html',p=FuelCalibrationProfile.query.filter_by(id=pid,customer_id=cid()).first_or_404())
@bp.post('/fuel-calibrations/<int:pid>/approve')
@login_required
def approve_calibration(pid):
 from .calibration import validate_points
 p=FuelCalibrationProfile.query.filter_by(id=pid,customer_id=cid()).first_or_404();errors,_=validate_points(p.points,p.tank_capacity_l)
 if errors:
  for e in errors:flash(e,'error')
 else:
  FuelCalibrationProfile.query.filter_by(customer_id=cid(),vehicle_id=p.vehicle_id,active=True).update({'active':False});p.approved=True;p.active=True;p.approved_by=current_user.id;p.approved_at=datetime.utcnow();audit('fuel.profile.approved','FuelCalibrationProfile',p.id);db.session.commit();flash('Calibration approved and activated.','ok')
 return redirect(url_for('main.calibration_detail',pid=p.id))
@bp.post('/installations')
@login_required
def create_installation():
 x=AutomotiveInstallationProfile(customer_id=cid(),vehicle_id=request.form.get('vehicle_id',type=int),device_id=request.form.get('device_id',type=int),board_revision=request.form['board_revision'],interface_revision=request.form['interface_revision'],electrical_system_v=request.form.get('electrical_system_v',type=int),ignition_source=request.form.get('ignition_source'),engine_run_source=request.form.get('engine_run_source'),charging_source=request.form.get('charging_source'),supply_voltage_source=request.form.get('supply_voltage_source'),fuel_sensor_source=request.form.get('fuel_sensor_source'),notes=request.form.get('notes'));db.session.add(x);db.session.flush()
 for code,label in [('POWER','Fused protected tracker power verified'),('POLARITY','Reverse-polarity protection verified'),('TRANSIENT','Automotive transient protection verified'),('IGNITION','Ignition input individually tested'),('ENGINE','Engine-running source individually tested'),('CHARGE','Charging source individually tested'),('FUEL','Fuel sensor interface and calibration verified'),('OUTPUTS','Physical outputs confirmed safe boot OFF'),('POWER_CYCLE','Power-cycle persistent reconnect verified')]:db.session.add(CommissioningCheck(installation_id=x.id,code=code,label=label,required=True))
 audit('installation.created','AutomotiveInstallationProfile',x.id);db.session.commit();return redirect(url_for('main.installation_detail',iid=x.id))
@bp.get('/installations/<int:iid>')
@login_required
def installation_detail(iid):return render_template('installation_detail.html',x=AutomotiveInstallationProfile.query.filter_by(id=iid,customer_id=cid()).first_or_404())
@bp.post('/installations/<int:iid>/checks/<int:check_id>')
@login_required
def update_installation_check(iid,check_id):
 x=AutomotiveInstallationProfile.query.filter_by(id=iid,customer_id=cid()).first_or_404();c=CommissioningCheck.query.filter_by(id=check_id,installation_id=x.id).first_or_404();c.state=request.form.get('state','PENDING');c.evidence=request.form.get('evidence');c.checked_by=current_user.id;c.checked_at=datetime.utcnow();audit('commissioning.check.updated','CommissioningCheck',c.id,{'state':c.state});db.session.commit();return redirect(url_for('main.installation_detail',iid=x.id))
@bp.post('/installations/<int:iid>/commission')
@login_required
def commission_installation(iid):
 x=AutomotiveInstallationProfile.query.filter_by(id=iid,customer_id=cid()).first_or_404();failed=[c for c in x.checks if c.required and c.state!='PASS']
 if failed:flash(f'{len(failed)} required checks are not passed.','error')
 elif not x.protected_inputs_verified or not x.outputs_safe_boot_off:flash('Safety confirmations must be selected before commissioning.','error')
 else:x.commissioned=True;x.commissioned_by=current_user.id;x.commissioned_at=datetime.utcnow();audit('installation.commissioned','AutomotiveInstallationProfile',x.id);db.session.commit();flash('Installation commissioned.','ok')
 return redirect(url_for('main.installation_detail',iid=x.id))

@bp.post('/reports/generate')
@login_required
def generate_report():
 from .reporting import route_report,stop_report,security_report,fuel_report
 from io import BytesIO
 kind=request.form['report_type'];vid=request.form.get('vehicle_id',type=int);start=datetime.fromisoformat(request.form['start']);end=datetime.fromisoformat(request.form['end'])
 if kind=='ROUTE':data,count=route_report(cid(),vid,start,end)
 elif kind=='STOPS':data,count=stop_report(cid(),vid,start,end)
 elif kind=='FUEL':data,count=fuel_report(cid(),vid,start,end)
 else:data,count=security_report(cid(),start,end)
 filename=f'FleetTrack_{kind}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv';r=ReportRun(customer_id=cid(),report_type=kind,vehicle_id=vid,period_start=start,period_end=end,format='CSV',generated_by=current_user.id,filename=filename,row_count=count);db.session.add(r);audit('report.generated','ReportRun','pending',{'type':kind,'rows':count});db.session.commit();return send_file(BytesIO(data),mimetype='text/csv',as_attachment=True,download_name=filename)
@bp.route('/admin/users',methods=['GET','POST'])
@login_required
def admin_users():
 if current_user.role!='fleet_admin':return ('Forbidden',403)
 if request.method=='POST':
  u=User(customer_id=cid(),email=request.form['email'].strip().lower(),name=request.form['name'],role=request.form.get('role','fleet_viewer'),active=True);u.set_password(request.form['temporary_password']);db.session.add(u);db.session.flush();db.session.add(UserSecurityProfile(user_id=u.id,password_changed_at=datetime.utcnow()));audit('user.created','User',u.id,{'role':u.role});db.session.commit();flash('User created.','ok');return redirect(url_for('main.admin_users'))
 return render_template('admin_users.html',users=User.query.filter_by(customer_id=cid()).order_by(User.name).all())
@bp.post('/admin/users/<int:uid>/state')
@login_required
def user_state(uid):
 if current_user.role!='fleet_admin':return ('Forbidden',403)
 u=User.query.filter_by(id=uid,customer_id=cid()).first_or_404()
 if u.id==current_user.id:return ('Cannot disable current session user.',409)
 u.active=request.form.get('action')=='enable';audit('user.state.changed','User',u.id,{'active':u.active});db.session.commit();return redirect(url_for('main.admin_users'))
@bp.get('/admin/recovery')
@login_required
def recovery_admin():
 if current_user.role!='fleet_admin':return ('Forbidden',403)
 return render_template('recovery_admin.html',backups=BackupJob.query.filter_by(customer_id=cid()).order_by(BackupJob.created_at.desc()).all(),webhooks=WebhookEndpoint.query.filter_by(customer_id=cid()).all(),failed=NotificationQueue.query.filter_by(customer_id=cid(),state='FAILED').order_by(NotificationQueue.created_at.desc()).all())
@bp.post('/admin/dead-letter/replay')
@login_required
def replay_dead_letters():
 if current_user.role!='fleet_admin':return ('Forbidden',403)
 rows=NotificationQueue.query.filter_by(customer_id=cid(),state='FAILED').all()
 for n in rows:n.state='PENDING';n.next_attempt_at=datetime.utcnow();n.last_error=None
 audit('dead_letter.replayed','NotificationQueue','batch',{'count':len(rows)});db.session.commit();flash(f'{len(rows)} failed deliveries queued for replay.','ok');return redirect(url_for('main.recovery_admin'))
@bp.post('/admin/webhooks')
@login_required
def create_webhook():
 if current_user.role!='fleet_admin':return ('Forbidden',403)
 import secrets
 from werkzeug.security import generate_password_hash
 raw=secrets.token_urlsafe(32);x=WebhookEndpoint(customer_id=cid(),name=request.form['name'],url=request.form['url'],event_types=request.form.getlist('event_types'),signing_secret_hash=generate_password_hash(raw));db.session.add(x);db.session.flush();audit('webhook.created','WebhookEndpoint',x.id);db.session.commit();flash('Webhook created. One-time signing secret: '+raw,'ok');return redirect(url_for('main.recovery_admin'))

@bp.route('/acceptance',methods=['GET','POST'])
@login_required
def acceptance():
 if request.method=='POST':
  if current_user.role!='fleet_admin':return ('Forbidden',403)
  from .acceptance import seed_campaign
  c=AcceptanceCampaign(customer_id=cid(),name=request.form['name'],release_name='Production Release',environment=request.form.get('environment','STAGING'),target_start=datetime.fromisoformat(request.form['target_start']) if request.form.get('target_start') else None,target_end=datetime.fromisoformat(request.form['target_end']) if request.form.get('target_end') else None,created_by=current_user.id);db.session.add(c);db.session.flush();seed_campaign(c);audit('acceptance.campaign.created','AcceptanceCampaign',c.id);db.session.commit();return redirect(url_for('main.acceptance_detail',campaign_id=c.id))
 return render_template('acceptance.html',campaigns=AcceptanceCampaign.query.filter_by(customer_id=cid()).order_by(AcceptanceCampaign.created_at.desc()).all())
@bp.get('/acceptance/<int:campaign_id>')
@login_required
def acceptance_detail(campaign_id):
 from .acceptance import stats
 c=AcceptanceCampaign.query.filter_by(id=campaign_id,customer_id=cid()).first_or_404();return render_template('acceptance_detail.html',c=c,stats=stats(c),pilots=PilotVehicle.query.filter_by(campaign_id=c.id).all(),runs=EnduranceRun.query.filter_by(campaign_id=c.id).all(),vehicles=Vehicle.query.filter_by(customer_id=cid()).all(),devices=Device.query.filter_by(customer_id=cid()).all())
@bp.post('/acceptance/<int:campaign_id>/items/<int:item_id>')
@login_required
def acceptance_item_update(campaign_id,item_id):
 c=AcceptanceCampaign.query.filter_by(id=campaign_id,customer_id=cid()).first_or_404();x=AcceptanceItem.query.filter_by(id=item_id,campaign_id=c.id).first_or_404();x.state=request.form.get('state','NOT_TESTED');x.evidence_reference=request.form.get('evidence_reference');x.evidence_note=request.form.get('evidence_note');x.executed_by=current_user.id;x.executed_at=datetime.utcnow();audit('acceptance.item.updated','AcceptanceItem',x.id,{'state':x.state});db.session.commit();return redirect(url_for('main.acceptance_detail',campaign_id=c.id))
@bp.post('/acceptance/<int:campaign_id>/pilot')
@login_required
def acceptance_add_pilot(campaign_id):
 c=AcceptanceCampaign.query.filter_by(id=campaign_id,customer_id=cid()).first_or_404();p=PilotVehicle(campaign_id=c.id,vehicle_id=request.form.get('vehicle_id',type=int),device_id=request.form.get('device_id',type=int),planned_hours=request.form.get('planned_hours',168,type=int),notes=request.form.get('notes'));db.session.add(p);db.session.commit();return redirect(url_for('main.acceptance_detail',campaign_id=c.id))
@bp.post('/acceptance/<int:campaign_id>/endurance')
@login_required
def acceptance_add_endurance(campaign_id):
 c=AcceptanceCampaign.query.filter_by(id=campaign_id,customer_id=cid()).first_or_404();x=EnduranceRun(campaign_id=c.id,name=request.form['name'],target_devices=request.form.get('target_devices',160,type=int),duration_hours=request.form.get('duration_hours',24,type=float),expected_interval_seconds=request.form.get('expected_interval_seconds',60,type=int));x.messages_expected=int(x.target_devices*x.duration_hours*3600/x.expected_interval_seconds);db.session.add(x);db.session.commit();return redirect(url_for('main.acceptance_detail',campaign_id=c.id))
@bp.post('/acceptance/<int:campaign_id>/decision')
@login_required
def acceptance_decision(campaign_id):
 if current_user.role!='fleet_admin':return ('Forbidden',403)
 from .acceptance import stats,can_accept
 c=AcceptanceCampaign.query.filter_by(id=campaign_id,customer_id=cid()).first_or_404();decision=request.form.get('decision')
 st=stats(c)
 if decision=='ACCEPTED' and not can_accept(c):flash(f'Production acceptance blocked: {st["blocking"]} blocking items are not PASS.','error');return redirect(url_for('main.acceptance_detail',campaign_id=c.id))
 c.state=decision;c.approved_by=current_user.id if decision=='ACCEPTED' else None;c.approved_at=datetime.utcnow() if decision=='ACCEPTED' else None;c.rejection_reason=request.form.get('note') if decision!='ACCEPTED' else None;db.session.add(ReleaseDecision(campaign_id=c.id,decision=decision,decided_by=current_user.id,item_total=st['total'],item_passed=st['passed'],item_failed=st['failed'],item_not_tested=st['untested'],blocking_open=st['blocking'],note=request.form.get('note')));audit('release.decision','AcceptanceCampaign',c.id,{'decision':decision});db.session.commit();return redirect(url_for('main.acceptance_detail',campaign_id=c.id))
