from datetime import datetime
from flask import Blueprint,jsonify
api=Blueprint('api',__name__)
@api.get('/health')
def health():return jsonify(status='ok',product='FleetTrack 360',version='1.2.0',time=datetime.utcnow().isoformat()+'Z')
