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
 assert.equal(data.filter(x=>x.motifs.length).length,794);
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
 for(const item of data){for(const basis of [...item.materialBasis,...item.techniqueBasis]){assert.ok(basis.field);assert.ok(String(raw[item.rawIndex][basis.field]).includes(basis.text));}}
});
test('explicit original date ranges are normalized with original numeric provenance',()=>{
 const x=data.find(x=>x.mainId==='7054');assert.equal(x.rawStart,-1279);assert.equal(x.start,960);assert.equal(x.end,1279);assert.match(x.dateNote,/规范化/);
 assert.equal(data.filter(x=>x.dateNote.startsWith('按原文')).length,202);
 const pending=data.find(x=>x.mainId==='4132');assert.equal(pending.start,null);assert.equal(pending.rawStart,-1000);
});
