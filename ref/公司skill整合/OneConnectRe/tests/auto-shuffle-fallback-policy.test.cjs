const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
function triggered(config,level=13){function Action(){}function Condition(){}Action.prototype.run_object=function(){};Action.prototype.run_system=function(){};Condition.prototype.run_system=function(){};let events=[],rt={all_global_vars:[{name:'level',data:level},{name:'shuffle',data:0}]},w={cr:{action:Action,condition:Condition},oneConnectLevels:config,oneConnectHost:{emit:t=>events.push(t)},c2_callFunction(){},setTimeout(){}};w.window=w;vm.runInNewContext(fs.readFileSync(process.env.OC_SHUFFLE_PATH||'game/auto-shuffle.js','utf8'),w);w.oneConnectAutoShuffle.install();let action=new Action();Object.assign(action,{sid:484278472184714,runtime:rt});action.run_object();return events.includes('game.auto_shuffle_start')}
assert.equal(triggered({levels:[]}),false,'absent default keeps original behavior');
assert.equal(triggered({levels:[],fallbackAutoShuffle:'free'}),true,'unconfigured level uses explicitly selected fallback');
assert.equal(triggered({levels:[{level:13,seconds:180}],fallbackAutoShuffle:'free'}),true,'timer-only level uses fallback');
assert.equal(triggered({levels:[{level:13,seconds:180,autoShuffle:'original'}],fallbackAutoShuffle:'free'}),false,'explicit per-level original overrides fallback');
assert.equal(triggered({levels:[{level:13,board:[[1,1]]}],fallbackAutoShuffle:'free'}),false,'custom board does not inherit fallback policy');
assert.equal(triggered({levels:[{level:13,board:[[1,1]],autoShuffle:'free'}]}),true,'explicit custom-board policy still works');
assert.equal(triggered({levels:[],fallbackAutoShuffle:'bad'}),false,'invalid default cannot silently enable policy');
console.log('fallback shuffle policy explicit default, scope and per-level override PASS');
