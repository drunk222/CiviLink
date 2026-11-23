"""Validate original image CRCs, create local thumbnails/viewers, match by ID + title.
Run with the bundled Python (Pillow). Original image payloads remain untouched.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageOps
import json,re,zlib,unicodedata,collections
ROOT=Path(__file__).resolve().parents[1]
for name in ['thumbs','views']:(ROOT/'assets/official'/name).mkdir(parents=True,exist_ok=True)
files=json.loads((ROOT/'data/image-files.json').read_text(encoding='utf-8'))
rows=json.loads((ROOT/'data/official-records.json').read_text(encoding='utf-8'))
overrides=json.loads((ROOT/'data/image-match-overrides.json').read_text(encoding='utf-8'))
cache_path=ROOT/'data/image-render-cache.json'
cache=json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
def norm(s):
    if s is None or str(s).strip()=='——':return ''
    variants=str.maketrans({'瓚':'瓒','書':'书','詩':'诗','冊':'册','圖':'图','畫':'画','軸':'轴','蓮':'莲','龍':'龙','鳳':'凤','雲':'云','絲':'丝','織':'织','錦':'锦','緙':'缂','綢':'绸','繡':'绣','雙':'双','鴛':'鸳','鴦':'鸯','萬':'万','國':'国','聖':'圣','壽':'寿','壺':'壶','寶':'宝','觀':'观','鳥':'鸟','葉':'叶','紋':'纹','獅':'狮','羅':'罗','楊':'杨','趙':'赵','陳':'陈','張':'张','吳':'吴','劉':'刘','顏':'颜','黃':'黄','體':'体','繪':'绘','經':'经'})
    return re.sub(r'[^a-z0-9\u3400-\u9fff]','',unicodedata.normalize('NFKD',str(s)).lower().translate(variants))
def build(f):
    try:
        source=ROOT/f['file'];b=source.read_bytes();crc=f'{zlib.crc32(b)&0xffffffff:08x}'
        if f['crc32'] and crc!=f['crc32']:raise ValueError('Original file CRC mismatch')
        key=f['key'];thumb=f'assets/official/thumbs/{key}.jpg';view=f'assets/official/views/{key}.jpg';cached=cache.get(key)
        if cached and cached.get('crc32')==crc and (ROOT/thumb).exists() and (ROOT/view).exists():return cached
        with Image.open(source) as im:
            im=ImageOps.exif_transpose(im);size=im.size
            if im.mode in ['RGBA','LA','P']:
                rgba=im.convert('RGBA');background=Image.new('RGBA',rgba.size,'#f4f1e9');background.alpha_composite(rgba);im=background.convert('RGB')
            else:im=im.convert('RGB')
            small=im.copy();small.thumbnail((180,180),Image.Resampling.LANCZOS);small.save(ROOT/thumb,'JPEG',quality=80,optimize=True)
            im.thumbnail((1600,1600),Image.Resampling.LANCZOS);im.save(ROOT/view,'JPEG',quality=88,optimize=True)
        return dict(key=key,originalName=f['originalName'],original=f['file'],image=view,thumbnail=thumb,crc32=crc,width=size[0],height=size[1])
    except Exception as e:return dict(error=str(e),file=f['file'],originalName=f['originalName'])
valid=[];errors=[]
with ThreadPoolExecutor(max_workers=4) as pool:
    for item in pool.map(build,files):
        (errors if 'error' in item else valid).append(item)
cache.update({x['key']:x for x in valid});cache_path.write_text(json.dumps(cache,ensure_ascii=False),encoding='utf-8')
groups=collections.defaultdict(list)
for row in rows:groups[str(row['ID'])].append(row)
manifest={};unmatched=[];ambiguous=[]
for img in valid:
    filename=Path(img['originalName']).name;m=re.match(r'^(\d+)_(.*)\.[^.]+$',filename)
    if not m:unmatched.append(filename);continue
    group=groups.get(m[1],[]);stem=re.sub(r'^\d+_','',m[2]);base=norm(re.sub(r'_[0-9]+$','',stem))
    owner=None;method='ID唯一匹配'
    if filename in overrides:
        entry=overrides[filename];owner=next((r for r in group if str(r['Main_ID'])==entry['mainId']),None)
        if owner is None:raise ValueError('Manual mapping does not belong to image ID group')
        method=entry['basis']
    elif len(group)==1:owner=group[0]
    elif len(group)>1:
        scores=[]
        for row in group:
            names=[norm(row.get('藏品名称_ZN')),norm(row.get('藏品名称_EN'))];names=[n for n in names if n]
            score=max([200 if base==n else 160 if base.startswith(n) and len(n)>=3 else 140 if n.startswith(base) and len(base)>=4 else 100 if n in base and len(n)>=6 else 0 for n in names] or [0])
            if not names and not base:score=190
            scores.append((score,row))
        scores.sort(key=lambda x:x[0],reverse=True)
        if scores[0][0]>0 and (len(scores)==1 or scores[0][0]>scores[1][0]):owner=scores[0][1];method='重复ID以原图名称与中英文标题消歧'
        else:ambiguous.append(dict(image=filename,candidates=[str(x['Main_ID']) for x in group]));continue
    else:unmatched.append(filename);continue
    key=str(owner['Main_ID']);entry=manifest.setdefault(key,dict(images=[],matchMethod=method))
    entry['images'].append({k:img[k] for k in ['image','thumbnail','original','originalName','width','height']})
for entry in manifest.values():
    entry['images'].sort(key=lambda x:x['originalName']);entry['image']=entry['images'][0]['image'];entry['thumbnail']=entry['images'][0]['thumbnail']
(ROOT/'data/image-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
report=dict(archiveEntries=len(files),validImages=len(valid),recordsMapped=len(manifest),recordsWithoutImages=len(rows)-len(manifest),mappedFiles=sum(len(x['images']) for x in manifest.values()),ambiguous=ambiguous,unmatched=unmatched,errors=errors,integrity='Every rendered original file CRC32 checked against its original RAR entry')
(ROOT/'data/image-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['ambiguous','unmatched','errors']},ensure_ascii=True));print('ambiguous',len(ambiguous),'unmatched',len(unmatched),'errors',len(errors))
