import requests,json,concurrent.futures,pathlib
ids=[451841,453599,76550,49313,453324,451063,451843,3336,46342,625008]
def get(i):
 try:
  r=requests.get(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}',timeout=25);r.raise_for_status();d=r.json();pathlib.Path(f'data/raw/{i}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
  u=d.get('primaryImageSmall');p=''
  if u and d.get('isPublicDomain'):
   im=requests.get(u,timeout=25);im.raise_for_status();pathlib.Path(f'assets/objects/{i}.jpg').write_bytes(im.content);p=str(len(im.content))
  return [i,d.get('title'),d.get('objectBeginDate'),d.get('objectEndDate'),d.get('isPublicDomain'),p]
 except Exception as e:return [i,str(e)]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
 for r in ex.map(get,ids):print(r)
