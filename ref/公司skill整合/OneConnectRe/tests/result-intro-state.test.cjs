const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
class Element {
  constructor(){this.children=[];this.listeners={};this.style={setProperty(name,value){this[name]=value;}};this.hidden=false;this.classList={toggle(){}};}
  setAttribute(){} appendChild(child){this.children.push(child);return child;} append(...items){this.children.push(...items);}
  replaceChildren(...items){this.children=[...items];} prepend(child){this.children.unshift(child);}
  addEventListener(name,fn){this.listeners[name]=fn} remove(){} set textContent(value){this._text=value;this.children=[];} get textContent(){return this._text||'';}
}
let timer=null,id=0;
const context={module:{exports:{}},globalThis:{},Number,Math,Error,setTimeout:fn=>{timer=fn;return ++id;},clearTimeout:()=>{timer=null;}};
vm.runInNewContext(fs.readFileSync('tools/result_panel_candidate.js','utf8'),context);
const doc={body:new Element(),head:new Element(),createElement:()=>new Element(),defaultView:null};
const panel=context.module.exports.create(doc,{next(){},home(){},retry(){}});
const root=doc.body.children[0],card=root.children[0],intro=root.children[1];
for(const name of ['mousedown','mouseup']){let stopped=false;root.listeners[name]({stopPropagation(){stopped=true}});assert(stopped,`${name} must not reach game input`)}
panel.show({kind:'win',level:3,score:900,levelScore:400,stars:2});
assert.equal(intro.hidden,false);assert.equal(card.hidden,true);assert.equal(typeof timer,'function');
assert.equal(intro.children[1].children[1].textContent,'GREAT JOB!','message is anchored to banner container');
assert.equal(intro.children[0].children.length,32,'four emitters each create eight particles');
assert.equal(card.children[2].children.length,0,'star slots are removed even if a legacy rating is supplied');
timer();assert.equal(intro.hidden,true);assert.equal(card.hidden,false);assert.equal(intro.children[0].children.length,0,'particles are removed after the intro');
panel.show({kind:'win',level:4,score:1000});assert.equal(card.children[2].children.length,0,'unknown rating does not create placeholders');panel.hide();assert.equal(timer,null);assert.equal(root.hidden,true);
panel.show({kind:'fail',level:4,score:1000});assert.equal(intro.hidden,true);assert.equal(card.hidden,false);
console.log('victory intro and failure state transitions PASS');
