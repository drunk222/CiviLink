import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
const root=new URL('../',import.meta.url),read=p=>JSON.parse(readFileSync(new URL(p,root),'utf8'));
const manifest=read('data/image-manifest.json'),items=read('data/official-collection.json');
test('the complete official image package is linked without gaps or ambiguities',()=>{
 const audit=read('data/image-audit.json');assert.equal(audit.validImages,4312);assert.equal(audit.recordsMapped,4312);assert.equal(audit.recordsWithoutImages,0);assert.deepEqual(audit.errors,[]);assert.deepEqual(audit.ambiguous,[]);assert.deepEqual(audit.unmatched,[]);assert.equal(Object.keys(manifest).length,4312);
 const download=read('data/official-download.json');assert.equal(download.bytes,1288822982);assert.equal(download.rangeValidation,true);assert.match(download.sha256,/^[a-f0-9]{64}$/);
});
test('mapped images and thumbnails exist under safe local asset paths',()=>{
 const seen=new Set();for(const [id,entry] of Object.entries(manifest)){
  assert.ok(items.some(x=>x.mainId===id));assert.ok(entry.images.length);
  for(const photo of entry.images){for(const key of ['image','thumbnail','original']){assert.match(photo[key],/^assets\/official\/(views|thumbs|images)\/[a-f0-9]{20}\.(jpg|jpeg|png|gif|bmp|tiff?|webp)$/);assert.ok(existsSync(new URL(photo[key],root)));}assert.ok(photo.width>0&&photo.height>0);assert.ok(!seen.has(photo.originalName));seen.add(photo.originalName);}
  const item=items.find(x=>x.mainId===id);assert.equal(item.image,entry.image);assert.equal(item.thumbnail,entry.thumbnail);
 }
});
test('duplicate numeric image IDs are resolved by image title instead of blindly shared',()=>{
 const robe=items.find(x=>x.mainId==='100'),vase=items.find(x=>x.mainId==='130981');
 if(robe.image&&vase.image){assert.notEqual(robe.image,vase.image);assert.ok(robe.images[0].originalName.includes('Robe'));assert.ok(vase.images[0].originalName.includes('青釉莲花尊'));}
});
test('charts use immediate custom tooltips and no native SVG title fallback',()=>{
 const source=readFileSync(new URL('charts.js',root),'utf8');assert.ok(!source.includes('<title>'));assert.ok(source.includes('hoverDescription'));
 const canvas=readFileSync(new URL('constellation.js',root),'utf8');assert.ok(canvas.includes('this.cells'));assert.ok(canvas.includes('drawImage(this.base'));
});
