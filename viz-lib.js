export const MUSEUMS=['the V&A','卢浮宫博物馆','北京故宫博物院（故宫专题）','大都会艺术博物馆','京都国立博物馆','台北故宫博物馆','澳大利亚国家博物馆','正仓院'];
export const SHORT={'the V&A':'V&A','卢浮宫博物馆':'卢浮宫','北京故宫博物院（故宫专题）':'北京故宫专题','大都会艺术博物馆':'The Met','京都国立博物馆':'京都国立','台北故宫博物馆':'台北故宫','澳大利亚国家博物馆':'澳洲国博','正仓院':'正仓院'};
export const PALETTE=['#426477','#b18a5d','#6f8976','#a56459','#8a819b','#7b9b9c','#b8a064','#a8a486'];
export const museumColor=m=>PALETTE[MUSEUMS.indexOf(m)]||'#899283';
export const MATERIALS=['陶瓷','纺织','纸本','金属','玻璃','木竹漆','玉石骨角','复合及其他','未标注'];
export const MAT_COLORS=['#527c91','#bb8c78','#b8a874','#738e80','#93b8b8','#94785d','#a0ab80','#91879b','#b7bdb0'];
export const TECHNIQUES=['织绣','烧造施釉','彩绘印刷','雕刻镶嵌','铸锻','其他工艺','未标注'];
export const TAGS=['莲花','花卉','鸟禽','龙凤','几何','人物','葡萄','海浪'];
export const DOMAIN=[-3500,2050];
export const dateKnown=x=>Number.isFinite(x.start)&&Number.isFinite(x.end);
export const yearLabel=y=>y<0?`前${Math.abs(y)}`:`${y}`;
export const countBy=(items,key,order)=> (order||[...new Set(items.map(x=>x[key]))]).map(name=>({name,count:items.filter(x=>x[key]===name).length}));
export function temporalBins(items,step=100){const bins=Array.from({length:Math.ceil((DOMAIN[1]-DOMAIN[0])/step)},(_,i)=>({year:DOMAIN[0]+i*step,total:0,counts:Object.fromEntries(MUSEUMS.map(m=>[m,0]))}));for(const x of items){if(!dateKnown(x))continue;const mid=(x.start+x.end)/2;const b=bins[Math.min(bins.length-1,Math.max(0,Math.floor((mid-DOMAIN[0])/step)))];b.total++;b.counts[x.museum]=(b.counts[x.museum]||0)+1;}return bins;}
export function flowLinks(items,source,target){const counts=new Map();for(const x of items){const key=JSON.stringify([x[source],x[target]]);counts.set(key,(counts.get(key)||0)+1);}return [...counts].map(([key,count])=>({source:JSON.parse(key)[0],target:JSON.parse(key)[1],count}));}
export function motifCells(items){return TAGS.flatMap(motif=>MUSEUMS.map(museum=>{const group=items.filter(x=>x.museum===museum),count=group.filter(x=>x.motifs.includes(motif)).length;return {motif,museum,count,denominator:group.length,ratio:group.length?count/group.length:0};}));}
