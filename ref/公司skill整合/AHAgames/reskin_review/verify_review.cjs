// Data/DOM-contract checks in Node; this is not browser rendering verification.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const results=JSON.parse(fs.readFileSync(path.join(__dirname,'reskin_ranking.json'),'utf8'));
class El{
 constructor(id='',dataset={}){this.id=id;this.dataset=dataset;this.value='';this.textContent='';this.children=[];this.listeners={};this.classes=new Set();this.classList={toggle:(c,force)=>force?this.classes.add(c):this.classes.delete(c),contains:c=>this.classes.has(c)};}
 appendChild(x){this.children=this.children.filter(y=>y!==x);this.children.push(x);return x;}
 addEventListener(type,fn){this.listeners[type]=fn;}
 scrollIntoView(){this.scrolled=true;}
}
function attrs(tag){const a={};for(const m of tag.matchAll(/([\w-]+)="([^"]*)"/g))a[m[1]]=m[2];return a;}
const cards=[...html.matchAll(/<section class="card"[^>]*>/g)].map(m=>{const a=attrs(m[0]);return new El(a.id,{game:a['data-game'],cat:a['data-cat'],s:a['data-s']});});
const rows=[...html.matchAll(/<tr class="review-row"[^>]*>/g)].map(m=>new El('',{game:attrs(m[0])['data-game']}));
const links=[...html.matchAll(/<a [^>]*data-review-jump="\d+"[^>]*>/g)].map(m=>new El('',{reviewJump:attrs(m[0])['data-review-jump']}));
const ids=new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>[m[1],new El(m[1])]));
cards.forEach(c=>ids.set(c.id,c));
const original=cards.map(c=>c.dataset.game);
ids.get('sort').value='priority';
const document={querySelectorAll:s=>s==='.card'?cards:s==='.review-row'?rows:s==='[data-review-jump]'?links:[],getElementById:id=>{assert(ids.has(id),'Missing id '+id);return ids.get(id);}};
const context=vm.createContext({document,history:{replaceState(){}}});
const script=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];assert.equal(script.length,1);
vm.runInContext(script[0][1],context);
const visible=()=>ids.get('list').children.filter(c=>!c.classes.has('hidden'));
const apply=()=>vm.runInContext('apply()',context);
assert.equal(cards.length,74);assert.equal(rows.length,74);assert.equal(visible().length,74);
assert.deepEqual(visible().slice(0,6).map(c=>+c.dataset.game),results.filter(r=>r.tier==='P0').map(r=>r.id));
ids.get('priority').value='P0';apply();assert.equal(visible().length,6);
ids.get('q').value='77413';apply();assert.equal(visible().length,1);assert.equal(visible()[0].dataset.game,'77413');
ids.get('cat').value='Sports';apply();assert.equal(visible().length,0);assert(!ids.get('review-empty').classes.has('hidden'));
vm.runInContext('resetReview()',context);assert.equal(visible().length,74);
ids.get('q').value='箭头';apply();assert.equal(visible().length,3);
vm.runInContext('resetReview()',context);
const byid=new Map(results.map(r=>[r.id,r]));
for(const [sort,field] of [['score',r=>r.score],['effort',r=>r.dimensions[2]],['art',r=>r.dimensions[0]]]){
 ids.get('sort').value=sort;apply();const vals=visible().map(c=>field(byid.get(+c.dataset.game)));
 assert(vals.every((v,i)=>i===0||vals[i-1]>=v),sort+' order');
}
ids.get('sort').value='original';apply();assert.deepEqual(visible().map(c=>c.dataset.game),original);
ids.get('priority').value='P3';apply();
const jump=links.find(l=>l.dataset.reviewJump==='77413');jump.listeners.click({preventDefault(){}});assert(ids.get('game-77413').scrolled);assert.equal(visible().length,74);
for(const c of cards)assert.equal(c.classes.has('hidden'),rows.find(r=>r.dataset.game===c.dataset.game).classes.has('hidden'));
for(const r of results){assert(r.dimensions.every(v=>v>=1&&v<=5));assert.equal(r.score,r.dimensions.reduce((s,v,i)=>s+v*[6,5,5,3,1][i],0));}
assert.equal(new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1])).size,[...html.matchAll(/\bid="([^"]+)"/g)].length,'duplicate IDs');
for(const m of html.matchAll(/href="([^"]+)"/g)){
 const href=m[1];if(href.startsWith('#'))assert(ids.has(href.slice(1)),href);
 else if(!/^(https?:|data:)/.test(href))assert(fs.existsSync(path.join(root,href)),href);
}
const report=JSON.parse(fs.readFileSync(path.join(__dirname,'verification.json'),'utf8'));
report.interactionLogicChecks={environment:'Node VM with minimal DOM contract; not a real browser',checks:['74 cards and 74 rows','P0 filter = 6','ID search','combined category/priority/search and empty result','Chinese note search','all five sorting modes','reset filters','jump reveals hidden target','card/table visibility synchronization','weighted scores','unique IDs and local links'],status:'PASS'};
fs.writeFileSync(path.join(__dirname,'verification.json'),JSON.stringify(report,null,2));
console.log('PASS: static preservation and all interaction logic checks. Browser rendering remains unverified.');
