import json,zipfile,platform,sys,os
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'support_bundles';OUT.mkdir(exist_ok=True);stamp=datetime.utcnow().strftime('%Y%m%d_%H%M%S');out=OUT/f'FleetTrack_Support_{stamp}.zip'
info={'generated_at':datetime.utcnow().isoformat()+'Z','python':sys.version,'platform':platform.platform(),'environment_keys':[k for k in os.environ if k.startswith(('DATABASE_','MAP_','SEED_','CORRELATION_','OFFLINE_','DELAYED_'))]}
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('system.json',json.dumps(info,indent=2));
 for name in ['README.md','.env.example','render.yaml','Procfile']:
  p=ROOT/name
  if p.exists():z.write(p,name)
print(out)
