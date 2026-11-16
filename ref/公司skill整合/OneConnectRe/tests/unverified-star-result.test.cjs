const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');if(!process.argv[2])throw Error('Pass candidate game directory');const dir=process.argv[2];
let listener,shown,records=0;const cr={plugins_:{Famobi:function(){}}},actions=Object.create({callback(){}});cr.plugins_.Famobi.prototype.acts=actions;
const runtime={running_layout:{name:'game'},all_global_vars:[{name:'level',data:2},{name:'score',data:500}],types:{t5:{instances:[]}}};
const window={cr,localStorage:{},cr_getC2Runtime:()=>runtime,addEventListener:(_,f)=>listener=f,oneConnectProgress:{get:()=>3},oneConnectStarProgressCandidate:{record(){records++}},oneConnectResultPanelCandidate:{create:()=>({show(s){shown=s},hide(){}})}};window.window=window;
const ctx={window,cr,document:{},Number,Array,Object,console};for(const name of ['competitor-star-reference.js','fly-star-score-candidate.js','result-bridge-candidate.js'])vm.runInNewContext(fs.readFileSync(dir+'/'+name,'utf8'),ctx);
window.oneConnectFlyStarScoreCandidate.begin(2);window.oneConnectResultBridgeCandidate.install();actions.callback('levelSuccess');assert.equal(shown.kind,'win');assert.equal(shown.stars,null,'unverified proxy cannot create an earned rating');assert.equal(records,0,'unverified proxy cannot write best stars');
console.log('unverified star base does not persist a win rating PASS');
