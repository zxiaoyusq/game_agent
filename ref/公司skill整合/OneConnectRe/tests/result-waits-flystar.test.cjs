const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function setup(kind){let shown=[],jobs=[],count=2,now=0,listener,visibility;const actions=Object.create({callback(){}}),cr={plugins_:{Famobi:function(){}}};cr.plugins_.Famobi.prototype.acts=actions;
 const runtime={running_layout:{name:'game'},all_global_vars:[{name:'level',data:3},{name:'score',data:100}],types:{t5:{instances:[]}}};
 const window={cr,cr_getC2Runtime:()=>runtime,oneConnectProgress:{get:()=>4},oneConnectFlyStarCandidate:{state:()=>({active:count})},oneConnectResultPanelCandidate:{create:()=>({show:s=>shown.push(s),hide(){}})},setTimeout:fn=>jobs.push(fn),addEventListener:(name,fn)=>{if(name==='oneconnect:event')listener=fn}};
 const document={hidden:false,addEventListener(name,fn){if(name==='visibilitychange')visibility=fn}};vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/result_bridge_candidate.js','utf8'),{window,cr,document,console,Number,Array,Object,Math,Date:{now:()=>now}});window.oneConnectResultBridgeCandidate.install();actions.callback(kind);
 return {shown,jobs,runtime,setCount:n=>count=n,advance:n=>now+=n,setHidden:v=>{document.hidden=v;visibility()},send:type=>listener({detail:{type}}),run:()=>{assert(jobs.length);jobs.shift()()}};}
const win=setup('levelSuccess');assert.equal(win.shown.length,0,'victory panel waits for final stars');win.setCount(0);win.run();assert.equal(win.shown[0].kind,'win');
const timeout=setup('levelSuccess');timeout.advance(3000);timeout.run();assert.equal(timeout.shown[0].kind,'win','stuck stars have bounded wait');
const leave=setup('levelSuccess');leave.send('screen.SCREEN_HOME');leave.run();assert.equal(leave.shown.length,0,'old win cannot appear after returning home');
const hidden=setup('levelSuccess');hidden.setHidden(true);hidden.advance(6000);hidden.run();assert.equal(hidden.shown.length,0,'background time does not consume the visual wait');hidden.setHidden(false);hidden.run();hidden.setCount(0);hidden.run();assert.equal(hidden.shown[0].kind,'win');
const fail=setup('levelFail');assert.equal(fail.shown[0].kind,'fail','failure remains immediate');
console.log('victory panel waits for flying stars without blocking failure PASS');
