const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element{constructor(){this.children=[];this.listeners={};this.hidden=false;}setAttribute(k,v){this[k]=v}appendChild(x){this.children.push(x)}append(...items){this.children.push(...items)}addEventListener(k,v){this.listeners[k]=v}focus(){focused=this}}
let focused=null;const prior={focus(){focused=this}},document={head:new Element(),body:new Element(),activeElement:prior,listeners:{},createElement:()=>new Element(),addEventListener(k,v){this.listeners[k]=v}};
const window={};vm.runInNewContext(fs.readFileSync('tools/how_to_play_candidate.js','utf8'),{window,document});
assert.equal(window.oneConnectHowToPlayCandidate.isOpen(),false);
window.oneConnectHowToPlayCandidate.open();const overlay=document.body.children[0],art=overlay.children[0];
assert.equal(window.oneConnectHowToPlayCandidate.isOpen(),true);
assert.equal(overlay.hidden,false);assert.equal(art.children[0].src,'images/tutorial-sheet0.webp');assert.equal(focused,art.children[1]);
art.children[1].listeners.click();assert.equal(overlay.hidden,true);assert.equal(window.oneConnectHowToPlayCandidate.isOpen(),false);assert.equal(focused,prior);
window.oneConnectHowToPlayCandidate.open();document.listeners.keydown({key:'Escape',stopPropagation(){}});assert.equal(overlay.hidden,true);
assert.equal(document.body.children.length,1,'reopening must reuse the same dialog');
console.log('original how-to-play art, close and focus restoration PASS');
