"""Normalize every official row, preserving provenance and unknown values. No network."""
import json, re, collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def clean(v):
    s=str(v).strip() if v is not None else ''
    return '' if s in ('——','—','--','None','nan','NA') else s
def year(v):
    try:return int(float(v))
    except (ValueError,TypeError,OverflowError):return None
MATERIAL_RULES=[('纺织',r'silk|wool|linen|cotton|textile|fabric|麻|绸|丝|羊毛|棉|织物'),('陶瓷',r'porcelain|stoneware|earthenware|ceramic|pottery|瓷|陶|石器|骨瓷'),('纸本',r'paper|papyrus|纸|纸草'),('玻璃',r'glass|玻璃'),('木竹漆',r'wood|bamboo|lacquer|木|竹|漆'),('金属',r'bronze|copper|silver|gold|iron|brass|金|银|铜|铁|锡'),('玉石骨角',r'jade|stone|ivory|bone|horn|玉|石|骨|角|象牙')]
# 多标签规则与主类规则分开：主类保持既有口径，多标签使用词边界并排除已知复合词误配。
MATERIAL_ALL_RULES=[('纺织',r'\b(?:silk|wool|linen|cotton|textiles?|fabrics?|cloth|velvet|satin|lace|felt|polyester|nylon|rayon)\b|麻|绸|丝|缎|绒|毡|羊毛|棉|织物'),('陶瓷',r'\b(?:porcelain|stoneware|earthenware|ceramics?|pottery|fritware|celadon|terracotta|maiolica)\b|bone\s*china|瓷|陶|石器|骨瓷|骨质瓷|炻器|青瓷|彩陶'),('纸本',r'\b(?:paper|papyrus|cardboard|parchment|vellum)\b|纸|纸草|纸板|卡纸'),('玻璃',r'\b(?:glass|fibreglass|fiberglass)\b|玻璃|玻璃纤维'),('木竹漆',r'\b(?:wood|plywood|boxwood|ebony|zitan|bamboo|lacquer)\b|木(?!版)|竹|漆|紫檀|黄杨'),('金属',r'\b(?:bronze|copper|silver|gold|iron|brass|steel|tin|lead|aluminium|aluminum|pewter|nickel|zinc)\b|金|银|铜|铁|钢(?!笔)|锡|铅(?!笔)|铝|镍|锌'),('玉石骨角',r'\bjade\b|\bstone\b(?!ware)|\bbone\b(?!\s*china)|\bivory\b|\bhorn\b|\bturquoise\b|\bcarnelian\b|\bagate\b|\bamber\b|\bcoral\b|\bmother-of-pearl\b|\bshell\b|玉|石(?!器|墨|膏)|骨(?!质?瓷)|角|象牙|绿松石|玛瑙|琥珀|珊瑚|贝壳')]
TECH_RULES=[('织绣',r'weav|woven|tapestry|embroider|织|绣|挂毯|帆布|平纹'),('烧造施釉',r'glaz|fired|釉|烧制'),('彩绘印刷',r'paint|print|lithograph|彩绘|印刷|绘画|染'),('雕刻镶嵌',r'carv|engrave|inlay|雕|刻|镶'),('铸锻',r'cast|hammer|铸|锻')]
MOTIF_RULES=[('莲花',r'lotus|蓮|莲|荷花'),('花卉',r'floral|flowers|peon|chrysanthem|tulip|花卉|花鸟|花紋|花纹|牡丹|菊|郁金香'),('鸟禽',r'\b(?!thunderbirds?\b)\w*birds?\b|\b(?:ducks?|cranes?)\b|(?<!雷)鸟|鳥|鴛|鸳|鹤|鶴'),('龙凤',r'\bdragons?\b|\bphoenix(?:es)?\b|龍|龙(?!眼)|凤(?!梨)|鳳'),('几何',r'geometric|geometry|幾何|几何'),('人物',r'figures?|human|portrait|人物|人像|肖像'),('葡萄',r'\bgrapes?\b|葡萄'),('海浪',r'\bwaves?\b|海浪|波浪|波涛|波濤')]
FALLBACK_MATERIAL_RULES=[('纺织',r'\b(?:silk|wool|linen|cotton|textiles?|fabrics?)\b'),('陶瓷',r'\b(?:porcelain|stoneware|earthenware|ceramics?|pottery)\b'),('纸本',r'\b(?:paper|papyrus)\b'),('玻璃',r'\bglass\b'),('木竹漆',r'\b(?:wood|bamboo|lacquer)\b'),('金属',r'\b(?:bronze|copper|silver|gold|iron|brass)\b'),('玉石骨角',r'\b(?:jade|stone|ivory|bone|horn)\b')]
FALLBACK_TECH_RULES=[('织绣',r'\b(?:weaving|woven|tapestry|embroidery|embroidered|knitting)\b'),('烧造施釉',r'\b(?:glazed|glazing|fired)\b'),('彩绘印刷',r'\b(?:painted|printing|lithograph|woodblock print)\b'),('雕刻镶嵌',r'\b(?:carved|engraved|inlaid)\b'),('铸锻',r'\b(?:cast|hammered|forged)\b')]
CLASS_NAMES={'sherd':'陶片','fragment':'残片','panel':'饰片','cylinder':'筒形器','axe head':'斧形器','pouring vessel':'注水器','figure':'人物像','vase':'瓶','jar':'罐','bowl':'碗','dish':'盘','plate':'盘','cup':'杯','bead':'珠饰','coin':'钱币','ring':'环','saucer':'碟','textile':'织物','various textiles':'织物','lidded box':'带盖盒','print':'版画','photograph':'照片'}
MATERIAL_NAMES={'porcelain':'瓷','stoneware':'炻器','earthenware':'陶','jade':'玉','bronze':'青铜','silk':'丝绸','paper':'纸','glass':'玻璃'}
def group(text,rules,other):
    if not text:return '未标注'
    return next((name for name,pat in rules if re.search(pat,text,re.I)),other)
def all_group(text,rules,other):
    """Return every matched category, ordered by the rule table; fall back to the primary label."""
    if not text:return [other]
    hits=[name for name,pat in rules if re.search(pat,text,re.I)]
    return sorted(set(hits),key=lambda x:[n for n,_ in rules].index(x)) or [other]
def all_material(text,primary):
    if not text:return [primary]
    hits=[name for name,pat in MATERIAL_ALL_RULES if re.search(pat,text,re.I)]
    if primary not in ('复合及其他','未标注') and primary not in hits:hits.append(primary)
    order=[n for n,_ in MATERIAL_ALL_RULES]
    return sorted(set(hits),key=order.index) or [primary]
def normalize_date(original_date,rawstart,rawend):
    """Prefer explicit original text over conflicting numeric columns; keep raw values untouched."""
    d=clean(original_date);start,end=rawstart,rawend
    note='使用原表数值年段';rule='raw'
    precision='unknown' if start is None or end is None else ('year' if start==end else 'range')
    clear=re.fullmatch(r'\s*(?:ca\.\s*)?(\d{3,4})\s*[-–—]\s*(\d{3,4})\s*\(made\)\s*',d,re.I)
    if clear:
        a,b=map(int,clear.groups())
        if a<=b and (a,b)!=(rawstart,rawend):
            return a,b,'按原文明确的公元年段规范化；原数值列存在冲突，已保留供核查','ad-made','range'
        return start,end,note,rule,'range'
    prefix=re.match(r'^\s*(?:ca\.\s*)?(\d{3,4})\s*[-–—]\s*(\d{3,4})\s*\(made\)',d,re.I)
    if prefix and tuple(map(int,prefix.groups()))!=(rawstart,rawend):
        return None,None,'原文含多个年段且与数值列冲突；绘图年代待核，保留记录','pending','unknown'
    century=re.fullmatch(r'\s*(?:ca\.\s*)?(\d{1,2})(?:st|nd|rd|th)\s+century\s+BC\s*(?:\(made\))?\s*',d,re.I)
    if century:
        n=int(century.group(1));s=-n*100;e=s+99
        if start is None or end is None or (end-start)<50:
            return s,e,'按原文公元前世纪表达展开为约100年区间；原数值列保留供核查','bc-century','century'
        return start,end,note,rule,'century'
    bcrange=re.fullmatch(r'\s*(?:ca\.\s*)?(\d{1,4})\s*BC\s*[-–—]\s*(\d{1,4})\s*BC\s*(?:\(made\))?\s*',d,re.I)
    if bcrange:
        a,b=map(int,bcrange.groups());s,e=sorted((-a,-b))
        if (start,end)!=(s,e):
            return s,e,'按原文公元前年段规范化；原数值列存在符号或端点冲突，已保留供核查','bc-range','range'
        return start,end,note,rule,'range'
    bcyear=re.fullmatch(r'\s*(?:ca\.\s*)?(\d{1,4})\s*BC\s*(?:\(made\))?\s*',d,re.I)
    if bcyear:
        a=-int(bcyear.group(1))
        if start!=a or end!=a:
            return a,a,'按原文公元前年份规范化；原数值列保留供核查','bc-year','year'
        return start,end,note,rule,'year'
    centuryad=re.fullmatch(r'\s*(?:ca\.\s*)?(\d{1,2})(?:st|nd|rd|th)\s+century\s*(?:\(made\))?\s*',d,re.I)
    if centuryad:
        n=int(centuryad.group(1));s=(n-1)*100;e=s+99
        if start is None or end is None or start==end:
            return s,e,'按原文世纪表达展开为约100年区间；原数值列保留供核查','century','century'
        return start,end,note,rule,'century'
    return start,end,note,rule,precision
rows=json.loads((ROOT/'data/official-records.json').read_text(encoding='utf-8'))
edits=json.loads((ROOT/'data/editorial-enrichment.json').read_text(encoding='utf-8'))
image_path=ROOT/'data/image-manifest.json'
images=json.loads(image_path.read_text(encoding='utf-8')) if image_path.exists() else {}
items=[]
(ROOT/'data/records').mkdir(exist_ok=True)
for index,r in enumerate(rows):
    (ROOT/f'data/records/cv-{clean(r["Main_ID"])}.json').write_text(json.dumps(r,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    evidence=[];motifs=[]
    for name,pat in MOTIF_RULES:
        hits=[{'field':k,'text':clean(r.get(k))[:240]} for k in ['藏品名称_ZN','藏品名称_EN','Metadata_ZN','Metadata_EN'] if re.search(pat,clean(r.get(k)),re.I)]
        if hits:motifs.append(name);evidence.append({'motif':name,'hits':hits})
    m=clean(r['博物馆']);accession=clean(r['博物馆索引号']);source=None
    if m=='the V&A' and re.fullmatch(r'O\d+',accession):source=f'https://collections.vam.ac.uk/item/{accession}/'
    if m=='卢浮宫博物馆' and re.fullmatch(r'cl\d+',accession):source=f'https://collections.louvre.fr/ark:/53355/{accession}'
    rawmat=' | '.join(filter(None,[clean(r.get('材质_EN')),clean(r.get('材质_ZN'))]));rawtech=' | '.join(filter(None,[clean(r.get('技法_EN')),clean(r.get('技法_ZN'))]))
    material=group(rawmat,MATERIAL_RULES,'复合及其他');technique=group(rawtech,TECH_RULES,'其他工艺');material_basis=[];technique_basis=[]
    for field in ['藏品名称_EN','分类_EN']:
        text=clean(r.get(field));basis_type='title' if field=='藏品名称_EN' else 'category'
        if material=='未标注' and text:
            inferred=group(text,FALLBACK_MATERIAL_RULES,'未标注')
            if inferred!='未标注':material=inferred;material_basis=[dict(field=field,text=text,method='名称/分类明确词汇补全',type=basis_type)]
        if technique=='未标注' and text:
            inferred=group(text,FALLBACK_TECH_RULES,'未标注')
            if inferred!='未标注':technique=inferred;technique_basis=[dict(field=field,text=text,method='名称/分类明确词汇补全',type=basis_type)]
    edit=edits.get(clean(r['Main_ID']))
    if edit:
        if edit['evidence'] not in clean(r.get(edit['field'])):raise ValueError(f"编辑证据不在原文中: {r['Main_ID']}")
        material=edit['material'];material_basis=[dict(field=edit['field'],text=edit['evidence'],method=edit['note'],type='editorial')]
    material_all=all_material(rawmat,material)
    technique_all=all_group(rawtech,TECH_RULES,'其他工艺') if rawtech else [technique]
    original_title=clean(r['藏品名称_ZN']) or clean(r['藏品名称_EN'])
    first_class=clean(r['分类_EN']).split(';')[0].strip().lower()
    fallback_title=(CLASS_NAMES.get(first_class) or clean(r['分类_ZN']).split(';')[0] or '馆藏记录')+' · '+clean(r['Main_ID'])
    material_label=(edit or {}).get('materialLabel') or MATERIAL_NAMES.get(clean(r['材质_EN']).lower()) or (clean(r['材质_ZN']) if len(clean(r['材质_ZN']))<=40 else '') or material
    rawstart,rawend=year(r['起始年']),year(r['终止年']);original_date=clean(r['年代'])
    start,end,date_note,date_rule,date_precision=normalize_date(original_date,rawstart,rawend)
    items.append(dict(id='cv-'+clean(r['Main_ID']),mainId=clean(r['Main_ID']),imageId=clean(r['ID']),row=index+2,
        title=edit['title'] if edit else original_title or fallback_title,titleBasis='馆方描述补充' if edit else '原始名称' if original_title else '原始分类转写',
        originalTitle=clean(r['藏品名称_EN']),museum=m,accession=accession,region=clean(r['来源地']) or '未标注',place=clean(r['来源地']) or '未标注',
        material=material,materialLabel=material_label,materialAll=material_all,materialAmbiguous=len(material_all)>1,materialBasis=material_basis,materialStatus='补充资料' if material_basis else ('原字段' if rawmat else '原资料缺失'),originalMedium=rawmat or '原始材质字段未提供',technique=technique,techniqueAll=technique_all,techniqueAmbiguous=len(technique_all)>1,techniqueBasis=technique_basis,originalTechnique=rawtech or '原始技法字段未提供',
        start=start,end=end,rawStart=rawstart,rawEnd=rawend,dateNote=date_note,dateRule=date_rule,datePrecision=date_precision,dateLabel=clean(r['年代']) or clean(r['时代']) or '年代未标注',originalDate=clean(r['年代']),
        motifs=motifs,motifEvidence=evidence,source=source,rawIndex=index,image=images.get(clean(r['Main_ID']),{}).get('image'),thumbnail=images.get(clean(r['Main_ID']),{}).get('thumbnail'),images=images.get(clean(r['Main_ID']),{}).get('images',[]),rights=clean(r['版权声明']) or '原表未提供版权说明',summary=clean(r['描述_ZN'])[:700],
        annotation='数据来自ChinaVis官方表。中文字段包含机器翻译；补全依据与纹样主题来源可在下方查看。',retrievedAt='2026-11-08'))
accession_counts=collections.Counter(f"{x['museum']}|{x['accession']}" for x in items if x['accession']);seen=collections.Counter()
for x in items:
    key=f"{x['museum']}|{x['accession']}" if x['accession'] else None
    x['accessionKey']=key;x['duplicateGroupSize']=accession_counts.get(key,1) if key else 1
    if key:seen[key]+=1
    x['duplicateIndex']=seen[key] if key else 1;x['duplicatePrimary']=bool(key and x['duplicateGroupSize']>1 and x['duplicateIndex']==1)
if len(items)!=4312 or len({x['id'] for x in items})!=4312:raise ValueError(f'Expected 4312 unique official records, got {len(items)}')
(ROOT/'data/official-collection.json').write_text(json.dumps(items,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
audit=dict(records=len(items),dated=sum(x['start'] is not None and x['end'] is not None for x in items),rawMissingDates=sum(x['rawStart'] is None or x['rawEnd'] is None for x in items),normalizedDates=sum(x['dateRule']=='ad-made' for x in items),dateConflictsPending=sum(x['dateRule']=='pending' for x in items),bcNormalized=sum(x['dateRule'] in ('bc-range','bc-year','bc-century') for x in items),bcSignConflicts=sum('BC' in (x['originalDate'] or '').upper() and x['rawStart'] is not None and x['rawStart']>0 for x in items),bcEndpointConflicts=sum(x['dateRule']=='bc-range' for x in items),centuryExpanded=sum(x['dateRule']=='bc-century' for x in items),datePrecision=dict(collections.Counter(x['datePrecision'] for x in items)),motifTagged=sum(bool(x['motifs']) for x in items),motifCounts=dict(collections.Counter(m for x in items for m in x['motifs'])),
    imagesMapped=sum(bool(x['image']) for x in items),sourceCoverage=sum(bool(x['source']) for x in items),materialOriginallyMissing=sum(not clean(r.get('材质_EN')) and not clean(r.get('材质_ZN')) for r in rows),materialSupplemented=sum(bool(x['materialBasis']) for x in items),materialBasisTypes=dict(collections.Counter(b.get('type','unknown') for x in items for b in x['materialBasis'])),techniqueOriginallyMissing=sum(not clean(r.get('技法_EN')) and not clean(r.get('技法_ZN')) for r in rows),techniqueSupplemented=sum(bool(x['techniqueBasis']) for x in items),techniqueBasisTypes=dict(collections.Counter(b.get('type','unknown') for x in items for b in x['techniqueBasis'])),materialAllMulti=sum(len(x['materialAll'])>1 for x in items),techniqueAllMulti=sum(len(x['techniqueAll'])>1 for x in items),
    museums=dict(collections.Counter(x['museum'] for x in items)),materials=dict(collections.Counter(x['material'] for x in items)),techniques=dict(collections.Counter(x['technique'] for x in items)),
    repeatedAccessionRows=sum(n-1 for (m,a),n in collections.Counter((x['museum'],x['accession']) for x in items if x['accession']).items() if n>1),duplicateGroups=sum(1 for n in accession_counts.values() if n>1),duplicateRecords=sum(n for n in accession_counts.values() if n>1),
    countUnit='官方元数据记录；并非去重后的物理藏品',materialRule='primary: first explicit match in ordered MATERIAL_RULES; materialAll uses stricter boundaries and may include several categories',motifRule='title + Metadata only; AAT and description excluded; English terms use boundaries to avoid dragonfly/thunderbird',rulesVersion='0.4')
(ROOT/'data/normalized-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=True))
