const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');const context={module:{exports:{}},setTimeout:(...args)=>global.setTimeout(...args),clearTimeout};vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/result_panel_candidate.js','utf8'),context);const api=context.module.exports;
class El{constructor(){this.children=[];this.style={setProperty(){}};this.classList={toggle(){}};this.clientWidth=100;this.clientHeight=30;}setAttribute(){}appendChild(x){this.children.push(x);return x}append(...x){this.children.push(...x)}prepend(x){this.children.unshift(x)}replaceChildren(...x){this.children=x}addEventListener(){}remove(){}}
let timer,resize;const doc={body:new El(),head:new El(),createElement(tag){if(tag==='canvas')return {getContext(){return {measureText(text){return {width:text.length*12}}}}};return new El()},defaultView:{innerWidth:400,innerHeight:800,addEventListener(name,fn){if(name==='resize')resize=fn},removeEventListener(){},getComputedStyle(){return {fontSize:'20px',fontWeight:'700',fontFamily:'sans-serif',paddingLeft:'5',paddingRight:'5'}},cr_getC2Runtime(){return {canvas:{getBoundingClientRect(){return {left:0,top:0,right:400,bottom:800}}}}}}};
const oldTimer=global.setTimeout;global.setTimeout=fn=>{timer=fn;return 1};try{
 const panel=api.create(doc,{}),level=doc.body.children[0].children[0].children[1],css=doc.head.children[0].textContent;
 assert.match(css,/white-space:nowrap/);assert.match(css,/\.stars\{display:none!important\}/,'removed three-star row stays hidden');panel.show({kind:'win',level:10});timer();assert.equal(level.textContent,'LEVEL 10');assert.equal(parseFloat(level.style.fontSize),18.75);
 panel.show({kind:'fail',level:1000});assert.equal(level.textContent,'LEVEL 1000');assert.equal(parseFloat(level.style.fontSize),15);
 level.clientWidth=160;resize();assert.equal(parseFloat(level.style.fontSize),20,'text returns to its normal size when space permits');
 panel.destroy();
}finally{global.setTimeout=oldTimer}
console.log('result level remains one line and shrinks to available width PASS');
