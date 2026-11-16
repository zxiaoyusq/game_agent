import {assertGame,planMove} from './rules.js';
import {movementSegments,duration} from './animation.js';
export const SAVE_KEY='ludo-original-session-v1';
export function validateSession(s) {
  if(s?.schema!==1 || !['ready','rolling','choosing','moving','skip','celebrating','result'].includes(s.phase) || !Number.isFinite(s.elapsed)||s.elapsed<0 || !Number.isFinite(s.wait)||s.wait<0 || typeof s.id!=='string') throw Error('存档阶段损坏');
  assertGame(s.game);
  if(['rolling','choosing','moving','skip'].includes(s.phase) && s.game.dice===null) throw Error('存档丢失骰子');
  if(s.phase==='ready' && (s.game.dice!==null || s.game.winner!==null)) throw Error('存档回合损坏');
  if(['celebrating','result'].includes(s.phase)!==(s.game.winner!==null)) throw Error('存档结算损坏');
  if(s.phase==='moving') {
    if(JSON.stringify(planMove(s.game,s.plan?.index))!==JSON.stringify(s.plan) || JSON.stringify(movementSegments(s.game,s.plan))!==JSON.stringify(s.segments) || s.elapsed>duration(s.segments)+100) throw Error('存档运动事务损坏');
  }
  return s;
}
export function load(storage) {
  const text=storage.getItem(SAVE_KEY); return text?validateSession(JSON.parse(text)):null;
}
export function persist(storage,session) { validateSession(session); storage.setItem(SAVE_KEY,JSON.stringify(session)); }
