const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El { constructor(){this.children=[];this.listeners={};this.style={};this.dataset={};this.hidden=false;this.classList={toggle(){}};} setAttribute(){} appendChild(x){this.children.push(x);return x} append(...x){this.children.push(...x)} querySelector(s){return this.children.find(x=>'.'+x.className===s)} addEventListener(k,f){(this.listeners[k]??=[]).push(f)} focus(){document.activeElement=this} }
const document={head:new El(),body:new El(),listeners:{},createElement(){return new El()},addEventListener(k,f){(this.listeners[k]??=[]).push(f)}};
const window={cr_getC2Runtime:()=>({running_layout:{name:'menu'}}),GAMESNACKS:{isAudioEnabled:()=>true,handleAudioUpdates(){}}};
const context={window,document,requestAnimationFrame(){}};
for(const name of ['home_settings_candidate','how_to_play_candidate']) vm.runInNewContext(fs.readFileSync(`tools/${name}.js`,'utf8'),context);
window.oneConnectHomeSettingsCandidate.install();
const [launcher,settings]=document.body.children; launcher.listeners.click.at(-1)();
window.oneConnectHowToPlayCandidate.open();
function escape(){for(const fn of document.listeners.keydown)fn({key:'Escape',stopPropagation(){}})}
escape();assert.equal(window.oneConnectHowToPlayCandidate.isOpen(),false);assert.equal(settings.hidden,false,'Escape closes the topmost dialog only');
escape();assert.equal(settings.hidden,true,'a second Escape closes settings');
console.log('nested settings and help Escape behavior PASS');
