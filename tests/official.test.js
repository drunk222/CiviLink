import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {filterItems,defaults,parseFilters,filterQuery} from '../lib.js';
import {MUSEUMS,MATERIALS,TECHNIQUES,countBy,temporalBins,flowLinks,motifCells,dateKnown} from '../viz-lib.js';
const data=JSON.parse(readFileSync(new URL('../data/official-collection.json',import.meta.url),'utf8'));
const raw=JSON.parse(readFileSync(new URL('../data/official-records.json',import.meta.url),'utf8'));
test('all 4312 official Main_IDs are retained and source rows trace correctly',()=>{
 assert.equal(data.length,4312);assert.equal(new Set(data.map(x=>x.id)).size,4312);
 data.forEach((x,i)=>{assert.equal(x.mainId,String(raw[i].Main_ID));assert.equal(x.row,i+2);assert.equal(x.rawIndex,i);assert.ok(MUSEUMS.includes(x.museum));assert.ok(MATERIALS.includes(x.material));assert.ok(TECHNIQUES.includes(x.technique));});
});
test('default includes unknown dates and BCE, explicit range excludes unknown',()=>{
 assert.equal(filterItems(data,defaults()).length,4312);
 assert.equal(filterItems(data,{...defaults(),dates:'unknown'}).length,12);
 assert.equal(filterItems(data,{...defaults(),dates:'known'}).length,4300);
 const bce=filterItems(data,{...defaults(),from:-3500,to:-1});assert.ok(bce.length>0);assert.ok(bce.every(x=>dateKnown(x)&&x.start<=-1));
});
test('material and technique partitions conserve current record count',()=>{
 for(const subset of [data,filterItems(data,{...defaults(),material:'陶瓷'}),filterItems(data,{...defaults(),motif:'莲花'}),[]]){
  for(const [key,order] of [['museum',MUSEUMS],['material',MATERIALS],['technique',TECHNIQUES]])assert.equal(countBy(subset,key,order).reduce((s,x)=>s+x.count,0),subset.length);
  for(const [a,b] of [['museum','material'],['material','technique']])assert.equal(flowLinks(subset,a,b).reduce((s,x)=>s+x.count,0),subset.length);
 }
});
test('century bins count each dated row once, never repeat broad intervals',()=>{
 const bins=temporalBins(data);assert.equal(bins.reduce((n,x)=>n+x.total,0),4300);
 for(const b of bins)assert.equal(Object.values(b.counts).reduce((a,b)=>a+b,0),b.total);
 assert.equal(temporalBins([{...data[0],start:-3500,end:2023}]).reduce((n,x)=>n+x.total,0),1);
});
test('matrix uses exact institution denominator and matches intersected filters',()=>{
 for(const cell of motifCells(data)){const filtered=filterItems(data,{...defaults(),museum:cell.museum,motif:cell.motif});assert.equal(filtered.length,cell.count);assert.equal(cell.denominator,data.filter(x=>x.museum===cell.museum).length);assert.ok(cell.ratio>=0&&cell.ratio<=1);}
});
test('candidate labels include field evidence and exclude noisy AAT/description',()=>{
 for(const x of data){assert.equal(x.motifs.length,x.motifEvidence.length);for(const e of x.motifEvidence){assert.ok(x.motifs.includes(e.motif));assert.ok(e.hits.length);for(const hit of e.hits)assert.ok(['藏品名称_ZN','藏品名称_EN','Metadata_ZN','Metadata_EN'].includes(hit.field));}}
 assert.equal(data.filter(x=>x.motifs.length).length,792);
});
test('full-dataset filter state including unknown dates round trips',()=>{
 const f={...defaults(),museum:'卢浮宫博物馆',technique:'织绣',from:-3500,to:2050,dates:'unknown'};assert.deepEqual(parseFilters(filterQuery(f)),f);
 assert.equal(filterItems(data,{...defaults(),material:'陶瓷'}).length,1211);
 assert.equal(filterItems(data,{...defaults(),museum:'the V&A',motif:'莲花'}).length,84);
});
test('P4 jade objects are supplemented from retained explicit descriptions',()=>{
 for(const [id,title] of [['258','玉斧'],['259','玉琮']]){
  const item=data.find(x=>x.mainId===id);assert.equal(item.title,title);assert.equal(item.material,'玉石骨角');assert.equal(item.materialLabel,'玉');assert.equal(item.technique,'未标注');assert.equal(item.materialStatus,'补充资料');
  const original=raw[item.rawIndex];assert.equal(original.材质_EN,'——');assert.ok(original.描述_EN.includes(item.materialBasis[0].text));
 }
 assert.equal(data.filter(x=>x.material==='未标注').length,606);
 assert.equal(data.filter(x=>x.materialBasis.length).length,432);
 assert.equal(data.filter(x=>x.techniqueBasis.length).length,92);
});
test('every supplemental material/craft label has a traceable original-field excerpt',()=>{
 for(const item of data){for(const basis of [...item.materialBasis,...item.techniqueBasis]){assert.ok(basis.field);assert.ok(['title','category','editorial'].includes(basis.type));assert.ok(String(raw[item.rawIndex][basis.field]).includes(basis.text));}}
 assert.equal(data.filter(x=>x.materialBasis.some(b=>b.type==='category')).length,405);
 assert.equal(data.filter(x=>x.materialBasis.some(b=>b.type==='title')).length,25);
 assert.equal(data.filter(x=>x.materialBasis.some(b=>b.type==='editorial')).length,2);
 assert.equal(data.filter(x=>x.techniqueBasis.some(b=>b.type==='category')).length,63);
 assert.equal(data.filter(x=>x.techniqueBasis.some(b=>b.type==='title')).length,29);
});
test('explicit original date ranges are normalized with original numeric provenance',()=>{
 const x=data.find(x=>x.mainId==='7054');assert.equal(x.rawStart,-1279);assert.equal(x.start,960);assert.equal(x.end,1279);assert.match(x.dateNote,/规范化/);
 assert.equal(data.filter(x=>x.dateRule==='ad-made').length,202);
 const pending=data.find(x=>x.mainId==='4132');assert.equal(pending.start,null);assert.equal(pending.rawStart,-1000);assert.equal(pending.dateRule,'pending');
});
test('BC dates follow explicit text and single centuries expand to full ranges',()=>{
 const bell=data.find(x=>x.mainId==='596');assert.deepEqual([bell.start,bell.end],[-1300,-1200]);assert.equal(bell.dateRule,'bc-range');
 const vessel=data.find(x=>x.mainId==='1003');assert.deepEqual([vessel.start,vessel.end],[-450,-250]);
 const bead=data.find(x=>x.mainId==='654');assert.deepEqual([bead.start,bead.end],[-1100,-1000]);
 const pendant=data.find(x=>x.mainId==='1110');assert.deepEqual([pendant.start,pendant.end],[-400,-301]);assert.equal(pendant.datePrecision,'century');
 assert.equal(data.filter(x=>x.dateRule==='bc-range').length,18);
 assert.equal(data.filter(x=>x.dateRule==='bc-century').length,32);
 assert.equal(data.filter(x=>x.dateRule==='bc-year').length,0);
 assert.equal(data.filter(x=>x.dateRule==='pending').length,1);
 assert.ok(data.every(x=>x.start===null||x.end===null||x.start<=x.end));
});
test('motif rules avoid dragonfly and thunderbird substrings',()=>{
 const dragonfly=data.find(x=>x.mainId==='115022');assert.ok(!dragonfly.motifs.includes('龙凤'));
 const plane=data.find(x=>x.mainId==='110920');assert.ok(!plane.motifs.includes('鸟禽'));
 assert.equal(data.filter(x=>x.motifs.length).length,792);
 assert.equal(data.filter(x=>x.motifs.includes('龙凤')).length,103);
 assert.equal(data.filter(x=>x.motifs.includes('鸟禽')).length,86);
});
test('multi-material and multi-technique labels are additive without changing the primary class',()=>{
 const silkGold=data.find(x=>x.mainId==='14466');assert.equal(silkGold.material,'纺织');assert.deepEqual(silkGold.materialAll,['纺织','金属']);
 const stoneware=data.find(x=>x.mainId==='10621');assert.equal(stoneware.material,'陶瓷');assert.deepEqual(stoneware.materialAll,['陶瓷']);
 const plywood=data.find(x=>x.mainId==='115626');assert.equal(plywood.material,'木竹漆');assert.deepEqual(plywood.materialAll,['木竹漆','金属']);
 const painted=data.find(x=>x.mainId==='10854');assert.deepEqual(painted.techniqueAll,['烧造施釉','彩绘印刷']);
 assert.equal(data.filter(x=>x.materialAll.length>1).length,341);
 assert.equal(data.filter(x=>x.techniqueAll.length>1).length,450);
});
test('duplicate accession rows are flagged without being removed',()=>{
 const duplicates=data.filter(x=>x.duplicateGroupSize>1);
 assert.equal(duplicates.length,658);
 assert.equal(data.filter(x=>x.duplicatePrimary).length,329);
 assert.equal(data.filter(x=>x.duplicateGroupSize===1).length,3654);
 assert.ok(duplicates.every(x=>x.accessionKey.includes('|')&&x.duplicateIndex>=1));
});
test('audit counters match the regenerated model',()=>{
 const audit=JSON.parse(readFileSync(new URL('../data/normalized-audit.json',import.meta.url),'utf8'));
 assert.equal(audit.records,data.length);
 assert.equal(audit.dated,data.filter(x=>Number.isFinite(x.start)&&Number.isFinite(x.end)).length);
 assert.equal(audit.normalizedDates,data.filter(x=>x.dateRule==='ad-made').length);
 assert.equal(audit.bcNormalized,data.filter(x=>['bc-range','bc-year','bc-century'].includes(x.dateRule)).length);
 assert.equal(audit.centuryExpanded,data.filter(x=>x.dateRule==='bc-century').length);
 assert.equal(audit.motifTagged,data.filter(x=>x.motifs.length).length);
 assert.equal(audit.materialAllMulti,data.filter(x=>x.materialAll.length>1).length);
 assert.equal(audit.techniqueAllMulti,data.filter(x=>x.techniqueAll.length>1).length);
});
