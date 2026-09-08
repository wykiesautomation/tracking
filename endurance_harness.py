import argparse,time,statistics,json,uuid,random
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib import request,error

def send(url,token,device,seq,lat,lon):
 body=json.dumps({'points':[{'sequence':seq,'sampled_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'latitude':lat,'longitude':lon,'accuracy_m':8,'speed_kmh':60}]}).encode();req=request.Request(url+'/api/fleet/v1/locations/batch',data=body,headers={'Content-Type':'application/json','Authorization':'Bearer '+token});start=time.perf_counter()
 try:
  with request.urlopen(req,timeout=15) as r:return r.status,(time.perf_counter()-start)*1000,None
 except Exception as e:return 0,(time.perf_counter()-start)*1000,str(e)
def main():
 p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--token-file',required=True);p.add_argument('--rounds',type=int,default=10);p.add_argument('--workers',type=int,default=20);p.add_argument('--output',default='endurance_result.json');a=p.parse_args();tokens=[x.strip() for x in open(a.token_file,encoding='utf-8') if x.strip()];results=[]
 with ThreadPoolExecutor(max_workers=a.workers) as ex:
  jobs=[]
  for r in range(a.rounds):
   for i,t in enumerate(tokens):jobs.append(ex.submit(send,a.url,t,i,f'{r}-{i}-{uuid.uuid4().hex[:8]}',-26.7+i*.0001,27.8+i*.0001))
  for f in as_completed(jobs):results.append(f.result())
 lat=[x[1] for x in results];ok=sum(x[0] in (202,207) for x in results);out={'synthetic_test':True,'target_url':a.url,'devices':len(tokens),'rounds':a.rounds,'requests':len(results),'accepted_http':ok,'failed_http':len(results)-ok,'p95_ms':sorted(lat)[int(.95*(len(lat)-1))] if lat else None,'errors':[x[2] for x in results if x[2]][:20]};open(a.output,'w').write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
