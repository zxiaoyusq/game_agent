const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{constructor(){this.children=[];this.style={};this.attrs={};this.listeners={}}setAttribute(k,v){this.attrs[k]=v}append(...x){this.children.push(...x)}appendChild(x){this.children.push(x)}addEventListener(n,f){this.listeners[n]=f}}
const document={body:new El(),createElement:()=>new El()},frames=[];
const runtime={running_layout:{name:'menu'},canvas:{getBoundingClientRect:()=>({left:0,top:0,right:400,bottom:800})},all_global_vars:[{name:'score',data:1234}]};
const window={innerWidth:400,innerHeight:800,cr_getC2Runtime:()=>runtime};
vm.runInNewContext(fs.readFileSync('tools/home_star_candidate.js','utf8'),{window,document,Number,Math,requestAnimationFrame:f=>frames.push(f)});window.oneConnectHomeStarCandidate.install();frames.shift()();
const badge=document.body.children[0];assert.equal(document.body.children.length,1,'no dialog is created');assert.equal(badge.children[1].textContent,' 1234');assert.equal(badge.attrs['aria-label'],'Score: 1234');assert.match(badge.style.cssText,/pointer-events:none/);assert.equal(badge.listeners.click,undefined);
console.log('home score is informational and has no star dialog PASS');
