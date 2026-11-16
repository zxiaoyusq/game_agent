import {uniform, streams} from './random.js';
export const SAFE = [0,13,26,39,8,21,34,47];
export const COLORS = ['blue','red','green','yellow'];
export const NAMES = ['蓝','红','绿','黄'];
export const clone = value => JSON.parse(JSON.stringify(value));
export function createGame(mode, seats, seed) {
  if (!['classic','quick'].includes(mode) || seats.length !== 4 || seats.some(x=>!['human','ai','off'].includes(x)) || seats.filter(x=>x!=='off').length<2 || !seats.includes('human')) throw Error('席位或模式无效');
  const rng = streams(seed), active = seats.flatMap((x,i)=>x==='off'?[]:[i]);
  return {version:1, mode, seats:[...seats], tokens:seats.map((s,p)=>s==='off'?[]:Array.from({length:4},(_,i)=>({pos:mode==='quick'&&i<2?13*p:-1, finished:false}))), unlocked:seats.map(()=>mode==='classic'), current:active[uniform(rng.dice,active.length)], dice:null, winner:null, turn:0, action:0, rng, last:null};
}
export function nextPos(p,pos,unlocked) {
  const home = 52+6*p;
  if(pos>=home && pos<home+5) return pos+1;
  if(pos===home+5) return null;
  if(pos===((13*p+50)%52) && unlocked) return home;
  return (pos+1)%52;
}
export function remaining(p,pos) {
  if(pos<0) return 57;
  let distance=0;
  while(pos!==57+6*p && distance<58) {pos=nextPos(p,pos,true); distance++;}
  return distance;
}
export function route(game,p,index,dice=game.dice) {
  const token=game.tokens[p]?.[index];
  if(!token || token.finished || !Number.isInteger(dice) || dice<1 || dice>6) return null;
  if(token.pos===-1) return dice===6?[13*p]:null;
  const path=[]; let pos=token.pos;
  for(let i=0;i<dice;i++) { pos=nextPos(p,pos,game.unlocked[p]); if(pos===null) return null; path.push(pos); }
  return path;
}
export function legalMoves(game) {
  if(game.winner!==null || !game.dice) return [];
  return game.tokens[game.current].flatMap((_,i)=>route(game,game.current,i)?[i]:[]);
}
export function captureAt(game,p,pos) {
  if(pos>=52 || SAFE.includes(pos)) return null;
  const occupants=[];
  game.tokens.forEach((list,q)=>list.forEach((token,i)=>{if(!token.finished && token.pos===pos) occupants.push({p:q,i});}));
  return occupants.length===1 && occupants[0].p!==p ? occupants[0]:null;
}
export function roll(game) {
  if(game.dice!==null || game.winner!==null) throw Error('当前不可掷骰');
  game.dice=1+uniform(game.rng.dice,6); return game.dice;
}
export function planMove(game,index) {
  if(!legalMoves(game).includes(index)) throw Error('非法棋子选择');
  const p=game.current, path=route(game,p,index), end=path.at(-1);
  return {id:game.action+1,p,index,path,from:game.tokens[p][index].pos,capture:captureAt(game,p,end),home:end===57+6*p};
}
export function endTurn(game, extra) {
  if(!extra) { do {game.current=(game.current+1)%4;} while(game.seats[game.current]==='off'); }
  game.turn++; game.dice=null;
}
export function skip(game) {
  if(legalMoves(game).length || !game.dice || game.winner!==null) throw Error('不能跳过合法动作');
  game.last={skip:true,extra:game.dice===6}; endTurn(game,game.dice===6);
}
// 一次动作一次提交，动画只读取计划，不提前修改棋子。
export function commitMove(game,plan) {
  if(plan.id===game.action) return false;
  if(JSON.stringify(plan)!==JSON.stringify(planMove(game,plan.index))) throw Error('动作事务不匹配');
  const {p,index,path,capture,home}=plan;
  const token=game.tokens[p][index]; token.pos=path.at(-1); token.finished=home;
  if(capture) {game.tokens[capture.p][capture.i]={pos:-1,finished:false}; game.unlocked[p]=true;}
  game.action=plan.id;
  const count=game.tokens[p].filter(t=>t.finished).length;
  const win=game.mode==='quick'?count>=1:count===4;
  const extra=game.dice===6 || !!capture || home;
  game.last={p,index,capture,home,extra};
  if(win) game.winner=p; else endTurn(game,extra);
  return true;
}
export function chooseAI(game) {
  const moves=legalMoves(game); if(!moves.length) return null;
  const scores=moves.map(i=>{
    const plan=planMove(game,i), end=plan.path.at(-1);
    const progress=game.unlocked[game.current]?57-remaining(game.current,end):((end-13*game.current+52)%52);
    return (plan.home?10000:0)+(plan.capture?(game.unlocked[game.current]?900:3000):0)+(SAFE.includes(end)?90:0)+progress*3+(plan.from<0?10:0);
  });
  const max=Math.max(...scores), best=moves.filter((_,i)=>scores[i]===max);
  return best[uniform(game.rng.ai,best.length)];
}
export function assertGame(game) {
  if(!game || game.version!==1 || !['classic','quick'].includes(game.mode)) throw Error('存档版本或模式不支持');
  if(!Array.isArray(game.seats) || game.seats.length!==4 || game.seats.some(s=>!['human','ai','off'].includes(s)) || game.seats.filter(s=>s!=='off').length<2 || !game.seats.includes('human')) throw Error('存档席位损坏');
  if(!Number.isInteger(game.current) || game.current<0 || game.current>3 || game.seats[game.current]==='off') throw Error('存档当前玩家损坏');
  if(game.dice!==null && (!Number.isInteger(game.dice)||game.dice<1||game.dice>6)) throw Error('存档骰子损坏');
  if(!Array.isArray(game.tokens)||game.tokens.length!==4||!Array.isArray(game.unlocked)||game.unlocked.length!==4) throw Error('存档棋子结构损坏');
  game.tokens.forEach((list,p)=>{
    if(!Array.isArray(list)||list.length!==(game.seats[p]==='off'?0:4)||typeof game.unlocked[p]!=='boolean'||(game.mode==='classic'&&!game.unlocked[p])) throw Error('存档营地损坏');
    list.forEach(t=>{if(!Number.isInteger(t.pos)||t.pos< -1||t.pos>75||typeof t.finished!=='boolean'||(t.pos>=52&&(t.pos<52+6*p||t.pos>57+6*p||!game.unlocked[p]))||t.finished!==(t.pos===57+6*p)) throw Error('存档位置损坏');});
  });
  if(game.winner!==null && (!Number.isInteger(game.winner)||!game.tokens[game.winner]?.length || (game.mode==='classic'?game.tokens[game.winner].filter(t=>t.finished).length!==4:!game.tokens[game.winner].some(t=>t.finished)))) throw Error('存档赢家损坏');
  for(const key of ['turn','action']) if(!Number.isSafeInteger(game[key])||game[key]<0) throw Error('存档计数损坏');
  for(const key of ['dice','ai']) if(!Number.isInteger(game.rng?.[key]?.value)||game.rng[key].value<=0||game.rng[key].value>4294967295) throw Error('存档随机状态损坏');
  return true;
}
