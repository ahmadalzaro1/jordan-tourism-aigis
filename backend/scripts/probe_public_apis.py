"""Small read-only probes; no credentials and no writes to project datasets."""
import json,time,urllib.parse,urllib.request,concurrent.futures
from pathlib import Path
checks={
'osm_overpass':('https://overpass-api.de/api/interpreter',urllib.parse.urlencode({'data':'[out:json][timeout:10];nwr(around:500,30.3285,35.4444)[tourism];out tags center 3;'}).encode()),
'wikimedia':('https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/Petra/monthly/2025010100/2025033100',None),
}
def probe(item):
 name,(url,body)=item;t=time.time()
 try:
  request=urllib.request.Request(url,data=body,headers={'User-Agent':'SyntaxLabs-GIS-validation/1.0 (https://thesyntaxlabs.com)'})
  with urllib.request.urlopen(request,timeout=20) as response: data=json.load(response);status=response.status
  (out/f'api-{name}.json').write_text(json.dumps(data,indent=2))
  return {'name':name,'status':status,'rows':len(data.get('elements',data.get('items',[]))),'seconds':round(time.time()-t,2)}
 except Exception as exc:return {'name':name,'error':str(exc),'seconds':round(time.time()-t,2)}
out=Path(__file__).resolve().parents[2]/'output/validation'
results=list(concurrent.futures.ThreadPoolExecutor(2).map(probe,checks.items()))
(out/'extra-api-probes.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
