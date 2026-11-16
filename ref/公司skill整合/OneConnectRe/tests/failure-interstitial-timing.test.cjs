const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 let options,shown=0,hidden=0,requests=0,resolveAd,navigation=[];
 const actions=Object.create({callback(){throw Error('failure should use candidate dialog')}}),cr={plugins_:{Famobi:function(){}}};cr.plugins_.Famobi.prototype.acts=actions;
 const runtime={running_layout:{name:'game'},all_global_vars:[{name:'level',data:9}],types:{t5:{instances:[]}}};
 let listener;const window={cr,cr_getC2Runtime:()=>runtime,c2_callFunction:n=>navigation.push(n),addEventListener(_type,fn){listener=fn},oneConnectResultPanelCandidate:{create(_d,o){options=o;return{show(){shown++},hide(){hidden++}}}},oneConnectHost:{showInterstitialFor(t){assert.equal(t,'fail');requests++;return new Promise(r=>{resolveAd=r})}}};
 let frames=[];vm.runInNewContext(fs.readFileSync('tools/result_bridge_candidate.js','utf8'),{window,cr,document:{addEventListener(){}},requestAnimationFrame:f=>frames.push(f),Promise,Number,Array,Object,Date,console});
 window.oneConnectResultBridgeCandidate.install();actions.callback('levelFail');assert.equal(shown,1);assert.equal(requests,0,'opening failure panel must not request ad');
 options.home();options.home();assert.equal(requests,1,'double click must not request twice');assert.deepEqual(navigation,[]);resolveAd({status:'unavailable'});await Promise.resolve();
 assert.deepEqual(navigation,['levelFailQuit'],'unavailable ad must continue navigation');assert.equal(hidden,1);
 actions.callback('levelFail');options.retry();options.retry();assert.equal(requests,2);resolveAd({status:'skipped'});await Promise.resolve();assert.deepEqual(navigation,['levelFailQuit','levelFailQuit']);runtime.running_layout.name='menu';frames.shift()();assert.deepEqual(navigation,['levelFailQuit','levelFailQuit','levelStart']);
 runtime.running_layout.name='game';actions.callback('levelFail');options.home();assert.equal(requests,3);listener({detail:{type:'game.board_configured'}});resolveAd({status:'returned'});await Promise.resolve();assert.deepEqual(navigation,['levelFailQuit','levelFailQuit','levelStart'],'late callback cannot navigate a new round');
 console.log('failure ad begins on action, avoids duplicates, and resumes on return PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
