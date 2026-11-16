const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class El{constructor(){this.style={};this.children=[];this.listeners={};}setAttribute(){}appendChild(x){this.children.push(x);return x}append(...x){this.children.push(...x)}addEventListener(n,f){(this.listeners[n]??=[]).push(f)}getBoundingClientRect(){return {top:100}}get lastElementChild(){return this.children.at(-1)}}
const body=new El(),document={body,createElement:()=>new El(),getElementById:()=>null},listeners={};let switches=0;
const runtime={running_layout:{name:'game'},all_global_vars:[{name:'theme',data:0}]};
const cr={plugins_:{Sprite:function(){}}};cr.plugins_.Sprite.prototype.acts={};
const window={cr,addEventListener(n,f){(listeners[n]??=[]).push(f)},cr_getC2Runtime:()=>runtime,oneConnectThemeSwitchCandidate:{animateSwitch(_r,_t,_a,done){switches++;done({status:'switched',theme:1,tiles:2});return {status:'started'}}}};
const localStorage={getItem:()=>null,setItem(){}};
vm.runInNewContext(fs.readFileSync('tools/layout_candidate.js','utf8'),{window,document,localStorage,cr,Number,Array,Object,Date,Math,RangeError,setTimeout(){},clearTimeout(){},requestAnimationFrame(){}});
window.oneConnectLayoutCandidate.install();const placeholder=body.children.at(-1),click=()=>placeholder.listeners.click.at(-1)(),emit=t=>listeners['oneconnect:event'].forEach(f=>f({detail:{type:t}}));
emit('game.auto_shuffle_start');click();assert.equal(switches,0);
emit('game.board_configured');click();assert.equal(switches,1,'new board releases previous auto-shuffle input lock');
console.log('new board clears stale layout shuffle lock PASS');
