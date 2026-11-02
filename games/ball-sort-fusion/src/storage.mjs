import { isComplete, applyMove } from './rules.mjs';
const sameBoard=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
// 相邻快照必须对应一次完整批量移动或一次加空管。
function validTransition(before,after,capacity){
  if(!before.extra&&after.extra&&after.moves===before.moves)return sameBoard([...before.board,[]],after.board);
  if(before.extra!==after.extra||after.moves!==before.moves+1||before.board.length!==after.board.length)return false;
  for(let from=0;from<before.board.length;from++)for(let to=0;to<before.board.length;to++){
    const result=applyMove(before.board,from,to,capacity);
    if(result&&sameBoard(result.board,after.board))return true;
  }
  return false;
}
export const freshSave = () => ({ version:1, mode:'classic', theme:0, sound:true, symbols:false, fast:false, indices:{classic:0,challenge:0,mystery:0}, completed:{}, session:null });
const isRecord=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const isCount=value=>Number.isInteger(value)&&value>=0&&value<=1000000;
const signature=board=>board.flat().sort((a,b)=>a-b).join(',');
// 浏览器存储属于不可信输入。逐字段校验偏好与进度，局面或历史有损坏时只丢弃本局。
export function normalizeSave(raw, levels) {
  const value=freshSave();let recovered=false;
  if(!isRecord(raw))return { save:value,recovered:true };
  if(raw.version!==1)recovered=true;
  if(Object.hasOwn(levels,raw.mode))value.mode=raw.mode;else recovered=true;
  for(const key of ['sound','symbols','fast']){if(typeof raw[key]==='boolean')value[key]=raw[key];else recovered=true;}
  for(const key of Object.keys(value.indices)){
    const index=isRecord(raw.indices)?raw.indices[key]:undefined;
    if(Number.isInteger(index)&&index>=0&&index<levels[key].length)value.indices[key]=index;else recovered=true;
  }
  const ids=new Set(Object.values(levels).flat().map(level=>level.id));
  if(isRecord(raw.completed)){
    for(const [id,entry]of Object.entries(raw.completed)){
      if(ids.has(id)&&isRecord(entry)&&isCount(entry.moves)&&isCount(entry.best))value.completed[id]={moves:entry.moves,best:entry.best};else recovered=true;
    }
  }else recovered=true;
  if(Number.isInteger(raw.theme)&&raw.theme>=0&&raw.theme<3&&Object.keys(value.completed).length>=raw.theme*3)value.theme=raw.theme;
  else if(raw.theme!==0)recovered=true;
  // 未知版本仅保留逐字段验证的进度与设置，不解释版本未知的会话及导航。
  if(raw.version!==1){value.mode='classic';value.indices={classic:0,challenge:0,mystery:0};return {save:value,recovered:true};}
  const session=raw.session;
  if(session!==null&&session!==undefined){
    const level=levels[value.mode][value.indices[value.mode]];
    function validSnapshot(snapshot){
      return isRecord(snapshot)&&typeof snapshot.extra==='boolean'&&isCount(snapshot.moves)&&Array.isArray(snapshot.board)&&
        snapshot.board.length===level.board.length+(snapshot.extra?1:0)&&
        snapshot.board.every(tube=>Array.isArray(tube)&&tube.length<=level.capacity&&tube.every(color=>Number.isInteger(color)&&color>=1&&color<=12))&&
        signature(snapshot.board)===signature(level.board);
    }
    const historyValid=isRecord(session)&&Array.isArray(session.history)&&session.history.length<=500&&session.history.every(validSnapshot);
    const chain=historyValid?[...session.history,session]:[];
    const initial={board:level.board,moves:0,extra:false};
    // 边界随截断历史持久保存，撤销缩短历史后仍逐笔验证；旧版满额历史只在此迁移。
    const hasBoundary=isRecord(session)&&Object.hasOwn(session,'historyBoundary');
    const boundary=hasBoundary?session.historyBoundary:(historyValid&&session.history.length===500?chain[0]:null);
    const boundaryValid=boundary===null||(validSnapshot(boundary)&&
      boundary.moves===chain[0]?.moves&&boundary.extra===chain[0]?.extra&&sameBoard(boundary.board,chain[0]?.board));
    const anchored=historyValid&&boundaryValid&&(boundary!==null||
      (chain[0].moves===0&&!chain[0].extra&&sameBoard(chain[0].board,initial.board)));
    const reversible=validSnapshot(session)&&anchored&&chain.slice(1).every((snapshot,i)=>validTransition(chain[i],snapshot,level.capacity));
    if(validSnapshot(session)&&session.mode===value.mode&&session.index===value.indices[value.mode]&&reversible){
      value.session={mode:session.mode,index:session.index,board:session.board.map(tube=>[...tube]),moves:session.moves,extra:session.extra,won:isComplete(session.board,level.capacity),historyBoundary:boundary===null?null:{board:boundary.board.map(tube=>[...tube]),moves:boundary.moves,extra:boundary.extra},history:session.history.map(snapshot=>({board:snapshot.board.map(tube=>[...tube]),moves:snapshot.moves,extra:snapshot.extra}))};
    }else recovered=true;
  }
  return {save:value,recovered};
}
