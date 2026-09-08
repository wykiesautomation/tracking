from app import create_app
from app.models import db
app=create_app()
with app.app_context():
 print('Database:',db.engine.url.render_as_string(hide_password=True))
 print('Tables:',', '.join(sorted(db.metadata.tables)))
 missing=[x for x in ['fuel_calibration_profile','fuel_calibration_point','automotive_installation_profile','commissioning_check','data_retention_policy'] if x not in db.metadata.tables]
 if missing:raise SystemExit('Missing model metadata: '+', '.join(missing))
 print('REV5 model metadata check passed.')
