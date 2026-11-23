import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {defaults,filterItems,matrixCount,csv,parseFilters,filterQuery} from '../lib.js';
const items=JSON.parse(readFileSync(new URL('../data/collection.json',import.meta.url),'utf8'));
test('curated dataset identities, intervals and local assets are valid',()=>{
 assert.equal(items.length,10);assert.equal(new Set(items.map(x=>x.id)).size,10);
 for(const x of items){assert.ok(x.start<=x.end);assert.match(x.source,/^https:\/\/www.metmuseum.org\/art\/collection\/search\/\d+$/);if(x.image){assert.equal(x.rights,'Public Domain');assert.ok(existsSync(new URL('../'+x.image,import.meta.url)));}}
 assert.equal(items.filter(x=>x.image).length,9);
});
test('combined filters intersect without dropping missing images',()=>{
 const result=filterItems(items,{...defaults(),region:'中国',material:'瓷',motif:'莲花'});
 assert.equal(result.length,2);assert.ok(result.some(x=>!x.image));
 assert.equal(filterItems(items,{...defaults(),q:'66.4.10'}).length,1);
 assert.equal(filterItems(items,{...defaults(),q:'no such object'}).length,0);
});
test('date ranges use inclusive intersection, not only start dates',()=>{
 const fixture=[{...items[0],start:1500,end:1600}];
 assert.equal(filterItems(fixture,{...defaults(),from:1600,to:1600}).length,1);
 assert.equal(filterItems(fixture,{...defaults(),from:1601,to:1700}).length,0);
 assert.equal(filterItems(fixture,{...defaults(),from:1520,to:1530}).length,1);
});
test('matrix counts records once per tag and keeps multi-tag semantics',()=>{
 assert.equal(matrixCount(items,'莲花','中国'),3);assert.equal(matrixCount(items,'花卉','土耳其'),2);
 assert.equal(matrixCount(items,'葡萄','日本'),0);
});
test('URL round trip, invalid years, reversed ranges and Chinese values',()=>{
 const f={...defaults(),motif:'莲花',region:'中国',q:'花 & 盘',from:1600,to:1750};
 assert.deepEqual(parseFilters(filterQuery(f)),f);
 assert.equal(parseFilters('?from=oops').from,-3500);
 assert.deepEqual([parseFilters('?from=1800&to=1500').from,parseFilters('?from=1800&to=1500').to],[1500,1800]);
 assert.equal(parseFilters('?to=9999').to,2050);
});
test('CSV preserves quoted fields and Chinese spreadsheet encoding',()=>{
 const out=csv([{...items[0],title:'一件"盘",器'}]);assert.ok(out.startsWith('\ufeff'));assert.ok(out.includes('"一件""盘"",器"'));assert.ok(out.includes(items[0].source));
});
