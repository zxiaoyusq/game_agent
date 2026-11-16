// 冻结运动段，持久化elapsed即可在任意帧恢复。
export const ROLL_MS=833.3333333333334;
export function movementSegments(game,plan) {
  const segments=[]; let from={p:plan.p,i:plan.index,pos:plan.from};
  for(const pos of plan.path) { const to={p:plan.p,i:plan.index,pos}; segments.push({kind:'walk',who:[plan.p,plan.index],from,to,ms:110}); from=to; }
  if(plan.capture) {
    const {p,i}=plan.capture; let pos=game.tokens[p][i].pos;
    const still={p,i,pos}; segments.push({kind:'capture',who:[p,i],from:still,to:still,ms:120});
    // 逆向逐格回到所属起点，最后回原槽，不一帧消失。
    while(pos!==13*p) {const before={p,i,pos}; pos=(pos+51)%52; segments.push({kind:'return',who:[p,i],from:before,to:{p,i,pos},ms:30});}
    segments.push({kind:'return',who:[p,i],from:{p,i,pos},to:{p,i,pos:-1},ms:180});
  }
  if(plan.home) segments.push({kind:'home',who:[plan.p,plan.index],from,to:{p:plan.p,i:plan.index,pos:from.pos,parked:true},ms:400});
  return segments;
}
export function segmentAt(segments,elapsed) {
  let offset=0;
  for(let i=0;i<segments.length;i++) {const s=segments[i]; if(elapsed<offset+s.ms) return {segment:s,index:i,t:Math.max(0,(elapsed-offset)/s.ms),offset}; offset+=s.ms;}
  return null;
}
export function duration(segments) {return segments.reduce((sum,s)=>sum+s.ms,0);}
