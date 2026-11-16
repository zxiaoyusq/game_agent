const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{constructor(){this.children=[];this.listeners={};this.style={};this.attrs={};this.hidden=false}append(...x){this.children.push(...x)}appendChild(x){this.children.push(x)}replaceChildren(){this.children=[]}setAttribute(k,v){this.attrs[k]=v}addEventListener(k,f){this.listeners[k]=f}focus(){}}
const body=new El(),document={body,head:new El(),createElement:()=>new El()};
const window={localStorage:{},oneConnectStarProgressCandidate:{load:()=>({levels:{'5':0,'6':2}})}};
vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/home_star_candidate.js','utf8'),{window,document,requestAnimationFrame(){},Date,Math});
window.oneConnectHomeStarCandidate.install();const [badge,overlay]=body.children;badge.listeners.click();
const rows=overlay.children[0].children[1].children;assert.equal(rows.length,2,'confirmed zero-star levels appear alongside recorded results');
assert.equal(rows[0].children[0].textContent,'Level 5');assert.equal(rows[0].children[1].attrs['aria-label'],'0 of 3 stars');assert.equal(rows[0].children[1].children.length,3);
console.log('confirmed zero-star level displays three empty star slots PASS');
