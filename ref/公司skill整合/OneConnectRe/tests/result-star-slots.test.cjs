const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),vm=require('node:vm');
if(!process.argv[2])throw Error('candidate game directory required');
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.attributes={};this.style={setProperty(){}};this.className='';this.classList={toggle(){}};}
  appendChild(node){this.children.push(node);return node;}
  append(...nodes){this.children.push(...nodes);}
  prepend(node){this.children.unshift(node);}
  replaceChildren(...nodes){this.children=[...nodes];}
  setAttribute(name,value){this.attributes[name]=value;}
  addEventListener(){}
  remove(){}
}
const document={body:new Element('body'),head:new Element('head'),createElement:tag=>new Element(tag)};
const sandbox={setTimeout,clearTimeout};vm.runInNewContext(fs.readFileSync(path.resolve(process.argv[2],'result-panel-candidate.js'),'utf8'),sandbox);
const panel=sandbox.oneConnectResultPanelCandidate.create(document,{});
const root=document.body.children[0],card=root.children[0],stars=card.children[2];
for(const rating of [null,0,1,2,3]){
 panel.show({kind:'win',level:3,stars:rating});
 assert.equal(card.children[1].textContent,'LEVEL 3');
 assert.equal(card.children[4].children[1].textContent,'NEXT');
 assert.equal(stars.children.length,0);
 assert.equal(stars.attributes['aria-label'],'');
}
panel.show({kind:'fail',level:3,stars:null});assert.equal(stars.children.length,0);
assert.equal(card.children[1].textContent,'LEVEL 3');assert.equal(card.children[4].children[0].textContent,'');assert.equal(card.children[4].children[1].textContent,'RETRY');
assert.equal(card.children[5].src,'images/timeout-clock.webp');
panel.destroy();
console.log('candidate result panel omits star slots for both outcomes PASS');
