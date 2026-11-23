"""Rebuild the curated dataset from retained official API responses. No network."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITORIAL = {
451841: ('葡萄纹青花盘', '土耳其', '石英质陶胎', '釉下彩', ['葡萄', '花卉', '海浪'], '16世纪第二个四分之一', '馆方将中心葡萄纹与明代青花联系起来，并指出口沿海浪纹取材于更早的元代器物。', '博物馆解读'),
453599: ('花卉纹多彩盘', '土耳其', '石英质陶胎', '釉下彩', ['花卉', '海浪'], '约1545—1560年', '馆方指出盘沿与中国器物的联系，同时介绍郁金香等奥斯曼花卉风格。', '博物馆解读'),
453324: ('万花筒纹盘', '土耳其', '石英质陶胎', '釉下彩', ['莲花', '几何'], '约1580—1585年', '馆方将放射状构图中的莲瓣与中国灵感相联系；几何化的重组形成了新的视觉语言。', '博物馆解读'),
76550: ('莲池鸳鸯盘', '中国', '珐琅', '掐丝珐琅', ['莲花', '鸟禽'], '15世纪晚期至16世纪早期', '馆方以莲花与鸳鸯解释婚姻和谐的寓意。本件用于比较同一植物主题在不同工艺中的呈现。', '博物馆解读'),
49313: ('花鸟虫纹深盘', '日本', '瓷', '釉下彩', ['花卉', '鸟禽'], '18世纪上半叶', '肥前烧柿右卫门类型的青花器物。馆方介绍了这类器物在日本国内贸易中的流通。', '博物馆解读'),
46342: ('荷花形彩瓷盘', '中国', '瓷', '釉上彩', ['莲花'], '19世纪上半叶', '景德镇瓷器，施釉上多彩珐琅并带贴饰。作品以荷花为主题。', '名称与材质字段'),
625008: ('莲花纹瓷盘', '中国', '瓷', '彩绘珐琅', ['莲花'], '清康熙时期（1662—1722）', '馆藏名称标明莲花纹，材质为瓷胎彩绘珐琅。本地未提供图像。', '名称与材质字段'),
3336: ('中国外销瓷盘', '中国', '瓷', '未标注', [], '1736—1795年', '馆方记载本件来自纽约Verplanck家族传承的餐具组，提供外销瓷使用语境。', '博物馆解读'),
451063: ('伊兹尼克釉下彩盘', '土耳其', '石英质陶胎', '釉下彩', [], '16世纪下半叶', '伊兹尼克制作，石英质陶胎施透明釉下彩。纹样暂未编辑标注。', '材质与地理字段'),
451843: ('伊兹尼克白化妆土彩盘', '土耳其', '石英质陶胎', '釉下彩', [], '16世纪', '馆方将产地归于土耳其伊兹尼克，使用白色化妆土上的釉下彩。纹样暂未编辑标注。', '材质与地理字段'),
}
items=[]
for i, e in EDITORIAL.items():
    d=json.loads((ROOT/f'data/raw/{i}.json').read_text(encoding='utf-8'))
    title, region, material, technique, motifs, label, summary, basis=e
    items.append(dict(id=f'met-{i}', accession=d['accessionNumber'], title=title,
        originalTitle=d['title'], dateLabel=label, originalDate=d['objectDate'],
        start=d['objectBeginDate'], end=d['objectEndDate'], region=region,
        place=d.get('city') or d.get('country') or d.get('culture') or '未标注',
        material=material, originalMedium=d['medium'], technique=technique, motifs=motifs,
        museum='The Metropolitan Museum of Art', collectionCity='纽约',
        source=f'https://www.metmuseum.org/art/collection/search/{i}',
        apiSource=f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}',
        image=f'assets/objects/{i}.jpg' if d['isPublicDomain'] and (ROOT/f'assets/objects/{i}.jpg').exists() else None,
        rights='Public Domain' if d['isPublicDomain'] else '未获取公共领域图片',
        summary=summary, annotation=f'中文标题及纹样标签为项目编辑标注；依据：{basis}。',
        retrievedAt='2026-11-08'))
(ROOT/'data/collection.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
report={'records':len(items),'images':sum(bool(x['image']) for x in items),'regions':sorted(set(x['region'] for x in items)), 'unlabelledMotifs':sum(not x['motifs'] for x in items),'sampleType':'目的性精选，非赛事全集、非随机样本','dateNote':'时间线使用API边界，详情保留原始年代文字；两者精度可能不同。'}
(ROOT/'data/audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
