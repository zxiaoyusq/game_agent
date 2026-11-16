const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict'),w={};w.window=w;vm.runInNewContext(fs.readFileSync(process.env.OC_SAVE_MODEL_PATH||'game/round-save-model.js','utf8'),w);const m=w.oneConnectRoundSaveModel;
const old={level:29,seconds:180,movement:'static',boardSize:{rows:2,cols:2},generator:{mask:[[1,1],[1,1]],typeCount:2}},current={...old,autoShuffle:'free'};
const saved={version:1,level:29,config:m.fingerprint(old),rows:2,cols:2,board:[[1,2],[1,2]],timer:100,score:100,tip:2,shuffle:1};
assert.equal(m.validate(saved,current),true,'adding free automatic shuffle preserves a compatible saved board');
assert.equal(m.validate(saved,{...current,seconds:179}),false,'other config changes remain incompatible');
assert.equal(m.validate({...saved,config:'bad'},current),false,'unrelated fingerprints remain invalid');
assert.equal(m.validate({...saved,config:m.fingerprint(current)},old),true,'removing the policy preserves a compatible saved board');
assert.equal(m.validate({...saved,config:m.fingerprint(current)},{...old,autoShuffle:'original'}),true,'changing only the shuffle policy preserves a compatible saved board');
for(const level of [17,22,24]){const entry=JSON.parse(fs.readFileSync('config/levels.json','utf8')).levels.find(e=>e.level===level),prior={...entry};delete prior.autoShuffle;let h=entry.boardSize?.rows||6,width=entry.boardSize?.cols||12,board=Array.from({length:h},()=>Array(width).fill(0));board[entry.gravity.left][width-1-entry.gravity.top]=board[entry.gravity.left][width-2-entry.gravity.top]=1;let snapshot={version:1,level,config:m.fingerprint(prior),rows:h,cols:width,board,timer:100,score:1,tip:2,shuffle:1};assert.equal(m.validate(snapshot,entry),true,`level ${level} must accept old snapshot`);assert.equal(m.validate(snapshot,{...entry,seconds:entry.seconds+1}),false)}
console.log('round save migration accepts shuffle-policy changes only PASS');
