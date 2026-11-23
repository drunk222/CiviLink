import {escapeHTML as h} from './lib.js';
const tip=document.createElement('div');tip.className='chart-tooltip';tip.setAttribute('role','tooltip');tip.hidden=true;document.body.append(tip);
let lastKey='',frame=0,pending=null,owner=null,width=260,height=90;
export function showTooltip(data,x,y,source='svg'){
 owner=source;pending={data,x,y};if(frame)return;frame=requestAnimationFrame(()=>{frame=0;if(!pending)return;const {data,x,y}=pending;const key=JSON.stringify(data),changed=key!==lastKey,wasHidden=tip.hidden;if(changed){lastKey=key;tip.innerHTML=`${data.image?`<img src="${h(data.image)}" alt="" width="64" height="64">`:''}<div class="tooltip-body">${data.eyebrow?`<small>${h(data.eyebrow)}</small>`:''}<strong>${h(data.title)}</strong>${data.value?`<b>${h(data.value)}</b>`:''}${data.meta?`<span>${h(data.meta)}</span>`:''}</div>`;tip.classList.toggle('has-image',Boolean(data.image));}tip.hidden=false;if(changed||wasHidden){const rect=tip.getBoundingClientRect();width=rect.width;height=rect.height;}const left=Math.max(10,Math.min(x+16,innerWidth-width-10)),top=y+height+22>innerHeight?Math.max(10,y-height-12):y+16;tip.style.transform=`translate3d(${left}px,${top}px,0)`;});
}
export function hideTooltip(source){if(source&&owner!==source)return;pending=null;tip.hidden=true;owner=null;}
document.addEventListener('pointermove',e=>{
 if(e.target.closest('canvas'))return;
 const node=e.target.closest('svg [role="button"],svg .flow-band');const desc=node?.querySelector(':scope > desc[data-hover]');
 if(!desc){hideTooltip('svg');return;}
 try{showTooltip(JSON.parse(desc.getAttribute('data-hover')),e.clientX,e.clientY);}catch{hideTooltip('svg');}
},{passive:true});
document.addEventListener('focusin',e=>{const desc=e.target.querySelector?.(':scope > desc[data-hover]');if(!desc)return;const r=e.target.getBoundingClientRect();try{showTooltip(JSON.parse(desc.getAttribute('data-hover')),r.left+r.width/2,r.top+r.height/2);}catch{}});
document.addEventListener('focusout',()=>hideTooltip());window.addEventListener('scroll',()=>hideTooltip(),{passive:true,capture:true});
document.addEventListener('pointerdown',()=>hideTooltip(),{passive:true});
export const hoverDescription=(title,value='',meta='')=>`<desc data-hover="${h(JSON.stringify({title,value,meta}))}">${h([title,value,meta].filter(Boolean).join(' · '))}</desc>`;
