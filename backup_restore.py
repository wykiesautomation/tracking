import os,sys,hashlib,shutil,sqlite3,subprocess,json
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'backups';OUT.mkdir(exist_ok=True)
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def sqlite_backup(db_path):
 stamp=datetime.utcnow().strftime('%Y%m%d_%H%M%S');dest=OUT/f'fleettrack_{stamp}.db';src=sqlite3.connect(db_path);dst=sqlite3.connect(dest);src.backup(dst);dst.close();src.close();return dest,sha(dest)
def postgres_backup(url):
 stamp=datetime.utcnow().strftime('%Y%m%d_%H%M%S');dest=OUT/f'fleettrack_{stamp}.dump';subprocess.run(['pg_dump','--format=custom','--file',str(dest),url],check=True);return dest,sha(dest)
def main():
 url=os.getenv('DATABASE_URL','sqlite:///fleettrack360.db')
 if url.startswith('sqlite:///'):
  p=Path(url.removeprefix('sqlite:///'));p=p if p.is_absolute() else ROOT/'instance'/p;dest,digest=sqlite_backup(p)
 else:dest,digest=postgres_backup(url)
 manifest={'file':dest.name,'size':dest.stat().st_size,'sha256':digest,'created_at':datetime.utcnow().isoformat()+'Z'};(dest.with_suffix(dest.suffix+'.json')).write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
