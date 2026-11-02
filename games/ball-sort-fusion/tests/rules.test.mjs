import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { applyMove, moveCount, isComplete, solve, cloneBoard } from '../src/rules.mjs';
const allLevels=JSON.parse(fs.readFileSync(new URL('../public/assets/levels.json',import.meta.url),'utf8'));

test('132 个交付关卡的完整解法均合法，最终每个非空管都满管同色',()=>{
  let total=0;
  for(const [mode,levels] of Object.entries(allLevels)){
    for(const level of levels){
      let state=cloneBoard(level.board);const before=state.flat().sort().join(',');
      for(const [from,to] of level.solution){const next=applyMove(state,from,to,level.capacity);assert.ok(next,`${mode}:${level.id} 非法步骤 ${from}→${to}`);state=next.board;}
      assert.equal(isComplete(state,level.capacity),true,level.id);
      assert.equal(state.flat().sort().join(','),before,'球数与颜色必须守恒');total++;
    }
  }
  assert.equal(total,132);
});
test('连续同色球受剩余容量约束，非法移动不会改变局面',()=>{
  const board=[[1,2,2,2],[2,2],[],[3,3,3,3]];const before=cloneBoard(board);
  assert.equal(moveCount(board,0,1,4),2);
  assert.deepEqual(applyMove(board,0,1,4).board,[[1,2],[2,2,2,2],[],[3,3,3,3]]);
  assert.equal(applyMove(board,0,3,4),null);
  assert.equal(applyMove(board,2,0,4),null);
  assert.equal(applyMove(board,0,0,4),null);
  assert.deepEqual(board,before);
});
test('完成检测拒绝未满的同色管，求解器能从偏离预置解法的局面继续通关',()=>{
  assert.equal(isComplete([[1,1],[1,1],[]],4),false);
  const level=allLevels.classic[0];let board=applyMove(level.board,1,3,4).board;
  const result=solve(board,4);assert.ok(result.solution?.length);
  for(const step of result.solution)board=applyMove(board,...step,4).board;
  assert.equal(isComplete(board,4),true);
});

const { freshSave, normalizeSave } = await import('../src/storage.mjs');
test('未知版本不解释会话，只保留独立验证的进度与偏好',()=>{
  const level=allLevels.classic[0];
  const raw={...freshSave(),version:999,sound:false,completed:{[level.id]:{moves:4,best:4}},session:{mode:'classic',index:0,board:applyMove(level.board,0,3,4).board,moves:1,extra:false,history:[]}};
  const result=normalizeSave(raw,allLevels);assert.equal(result.recovered,true);assert.equal(result.save.session,null);assert.equal(result.save.sound,false);assert.deepEqual(result.save.completed,raw.completed);
});
test('历史必须由合法批量移动和加管串联，拒绝守恒篡改与错误步数',()=>{
  const level=allLevels.classic[0];
  const initial={board:cloneBoard(level.board),moves:0,extra:false};
  const first={board:applyMove(initial.board,0,3,4).board,moves:1,extra:false};
  const second={board:applyMove(first.board,2,0,4).board,moves:2,extra:false};
  const session={...second,mode:'classic',index:0,history:[initial,first]};
  assert.ok(normalizeSave({...freshSave(),session},allLevels).save.session);
  for(const mutate of [s=>s.history[1].board=cloneBoard(initial.board),s=>s.moves++,s=>s.history.reverse(),s=>s.extra=true,s=>s.board=null]){
    const bad=structuredClone(session);mutate(bad);const result=normalizeSave({...freshSave(),session:bad},allLevels);assert.equal(result.recovered,true);assert.equal(result.save.session,null);
  }
  const added={...session,board:[...cloneBoard(second.board),[]],extra:true,history:[initial,first,second]};
  assert.ok(normalizeSave({...freshSave(),session:added},allLevels).save.session);
});
test('500条截断历史仍逐笔校验，允许合法中间局作为起点',()=>{
  const level=allLevels.classic[0];let snapshot={board:[...applyMove(level.board,0,3,4).board,[]],moves:1,extra:true};const history=[];
  for(let i=0;i<500;i++){history.push(structuredClone(snapshot));const step=i%2===0?[3,4]:[4,3];const result=applyMove(snapshot.board,...step,4);assert.ok(result,'测试历史的每一步必须合法');snapshot={board:result.board,moves:snapshot.moves+1,extra:true};}
  const session={...snapshot,mode:'classic',index:0,history};assert.ok(normalizeSave({...freshSave(),session},allLevels).save.session);
  session.history[250].moves++;assert.equal(normalizeSave({...freshSave(),session},allLevels).save.session,null);
});
test('截断边界经撤销、保存恢复及后续移动保留，拒绝边界与相邻事务篡改',()=>{
  const level=allLevels.classic[0];let snapshot={board:[...applyMove(level.board,0,3,4).board,[]],moves:1,extra:true};const history=[];
  for(let i=0;i<500;i++){history.push(structuredClone(snapshot));snapshot={board:applyMove(snapshot.board,...(i%2===0?[3,4]:[4,3]),4).board,moves:snapshot.moves+1,extra:true};}
  let session=normalizeSave({...freshSave(),session:{...snapshot,mode:'classic',index:0,history}},allLevels).save.session;
  assert.deepEqual(session.historyBoundary,history[0]);
  const reload=()=>{const result=normalizeSave(JSON.parse(JSON.stringify({...freshSave(),session})),allLevels);assert.equal(result.recovered,false);assert.ok(result.save.session);session=result.save.session;};
  for(let i=0;i<3;i++){Object.assign(session,session.history.pop());reload();assert.equal(session.history.length,499-i);}
  const before=structuredClone(session);session.history.push({board:cloneBoard(session.board),moves:session.moves,extra:session.extra});
  session.board=applyMove(session.board,4,3,4).board;session.moves++;reload();
  assert.equal(session.moves,before.moves+1);
  for(const mutate of [s=>s.historyBoundary='错误',s=>s.historyBoundary.moves++,s=>s.historyBoundary.board=null,s=>s.history[100].moves++,s=>s.historyBoundary=null]){
    const bad=structuredClone(session);mutate(bad);assert.equal(normalizeSave({...freshSave(),session:bad},allLevels).save.session,null);
  }
  while(session.history.length)Object.assign(session,session.history.pop());reload();
  assert.deepEqual(session.board,session.historyBoundary.board);
  assert.equal(session.moves,session.historyBoundary.moves);
});
test('损坏的合法JSON不会导致索引、进度或本局恢复崩溃',()=>{
  for(const bad of [null,[],"异常",{indices:null,completed:null},{...freshSave(),indices:'错误',completed:'错误'},{...freshSave(),session:{board:[[]]}}]){
    const result=normalizeSave(bad,allLevels);assert.equal(result.recovered,true);assert.equal(result.save.indices.classic,0);assert.deepEqual(result.save.completed,{});assert.equal(result.save.session,null);
  }
});
test('缺球、超容量与损坏历史快照会废弃本局，合法偏好仍能保留',()=>{
  const level=allLevels.classic[0];const snapshot={board:cloneBoard(level.board),moves:0,extra:false};
  const session={...snapshot,mode:'classic',index:0,won:false,history:[]};
  assert.ok(normalizeSave({...freshSave(),session},allLevels).save.session);
  for(const mutate of [s=>s.board[0].pop(),s=>s.board[0].push(...[1,1,1,1]),s=>s.history.push({...snapshot,board:null}),s=>s.extra=true]){
    const bad=structuredClone(session);mutate(bad);const result=normalizeSave({...freshSave(),sound:false,session:bad},allLevels);assert.equal(result.recovered,true);assert.equal(result.save.session,null);assert.equal(result.save.sound,false);
  }
});
