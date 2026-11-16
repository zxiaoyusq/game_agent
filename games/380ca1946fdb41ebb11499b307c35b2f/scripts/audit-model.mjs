// 中文：从已读参考函数逐句转写的独立几何模型；不是原游戏、Planck 或运行态提取。
// 仅将混淆全局改为 context 参数，before/after 切换矩形求交分支；保留比较符和退化行为。
export function startPathBlocked(context, origin, angle, length, intendedTarget, fullFallbackPath) {
  if (!origin || !Number.isFinite(origin.x) || !Number.isFinite(origin.y) ||
      !Number.isFinite(angle) || !Number.isFinite(length) || length < 0) return true;
  if (length === 0) return false;
  var dx = Math.cos(angle), dy = Math.sin(angle), end = fullFallbackPath ? Math.max(0, length - (context.strikerRadius + 16)) : Math.min(length, context.strikerRadius * 2),
    radius = context.strikerRadius + 16, discs = context.groups[1].concat(context.groups[0], context.groups[2]);
  for (var disc of discs) {
    if (disc === intendedTarget) continue;
    if (!disc || !Number.isFinite(disc.x) || !Number.isFinite(disc.y)) return true;
    var x = disc.x - origin.x, y = disc.y - origin.y,
      along = Math.max(0, Math.min(end, x * dx + y * dy)),
      ex = x - along * dx, ey = y - along * dy;
    if (ex * ex + ey * ey < radius * radius) return true;
  }
  return false;
}
export function trajectoryBlocked(context, shot, angle, version = 'after', trace = {}) {
  var target = shot && shot._carromFallbackTarget;
  if (!target || !shot.pos || !Number.isFinite(target.x) || !Number.isFinite(target.y) ||
      !Number.isFinite(shot.pos.x) || !Number.isFinite(shot.pos.y) || !Number.isFinite(angle)) return null;
  var discs = context.groups[0].concat(context.groups[1], context.groups[2]);
  if (discs.indexOf(target) < 0) return null;
  var x = target.x - shot.pos.x, y = target.y - shot.pos.y,
    radius = context.strikerRadius + 16, distance = Math.sqrt(x * x + y * y);
  if (!Number.isFinite(distance) || distance <= radius) return null;
  var ux = Math.cos(angle), uy = Math.sin(angle), projection = x * ux + y * uy,
    crossSquared = Math.max(0, distance * distance - projection * projection),
    targetEntry = projection - Math.sqrt(Math.max(0, radius * radius - crossSquared)),
    travel = crossSquared <= radius * radius && targetEntry >= 0 ? targetEntry : distance;
  var board = context.board;
  if (version === 'after' && !(crossSquared <= radius * radius && targetEntry >= 0) && board &&
      Number.isFinite(board.x) && Number.isFinite(board.y) &&
      Number.isFinite(board.width) && Number.isFinite(board.height)) {
    var inset = 26 + context.strikerRadius,
      left = board.x + inset, right = board.x + board.width - inset,
      top = board.y + inset, bottom = board.y + board.height - inset;
    if (right > left && bottom > top && shot.pos.x >= left && shot.pos.x <= right && shot.pos.y >= top && shot.pos.y <= bottom) {
      var tx = ux > 0 ? (right - shot.pos.x) / ux : ux < 0 ? (left - shot.pos.x) / ux : Infinity,
        ty = uy > 0 ? (bottom - shot.pos.y) / uy : uy < 0 ? (top - shot.pos.y) / uy : Infinity,
        wallDistance = Math.min(tx, ty);
      if (Number.isFinite(wallDistance) && wallDistance >= 0) travel = wallDistance;
    }
  }
  // 中文：额外 trace 只观察结果，不参与函数判断。
  Object.assign(trace, {travel, radius, distance, targetEntry, targetHit: crossSquared <= radius * radius && targetEntry >= 0, passedLength: travel + radius});
  return startPathBlocked(context, shot.pos, angle, travel + radius, target, true);
}
export function safeDeviation(context, shot, deviation, version = 'after') {
  if (!shot || !Number.isFinite(deviation) || deviation === 0) return deviation;
  return trajectoryBlocked(context, shot, shot.dir - deviation, version) === true &&
    trajectoryBlocked(context, shot, shot.dir, version) === false ? 0 : deviation;
}
// 中文：按参考转写快照模型；保持 group 顺序、对象身份、每轴 >1 的阈值。
export function captureBoard(context) {
  var result=[];
  [context.groups[1],context.groups[0],context.groups[2]].forEach(function(group,groupIndex){group.forEach(function(disc){result.push({disc:disc,group:groupIndex,x:disc&&disc.x,y:disc&&disc.y});});});
  return result;
}
export function boardChanged(context,snapshot) {
  if(!snapshot)return true;
  var savedByDisc=new Map();
  for(var i=0;i<snapshot.length;i++){var saved=snapshot[i];if(!saved||!saved.disc||savedByDisc.has(saved.disc))return true;savedByDisc.set(saved.disc,saved);}
  var groups=[context.groups[1],context.groups[0],context.groups[2]],count=0;
  for(var groupIndex=0;groupIndex<groups.length;groupIndex++){for(var j=0;j<groups[groupIndex].length;j++){var disc=groups[groupIndex][j],entry=savedByDisc.get(disc);if(!disc||!entry||entry.group!==groupIndex||!Number.isFinite(disc.x)||!Number.isFinite(disc.y)||!Number.isFinite(entry.x)||!Number.isFinite(entry.y)||Math.abs(disc.x-entry.x)>1||Math.abs(disc.y-entry.y)>1)return true;savedByDisc.delete(disc);count++;}}
  return count!==snapshot.length;
}
// 中文：独立解析首入圆时间，仅用于反例事件排序，不模拟动力学。
export function circleEntry(origin, angle, center, radius, includeTangent = true) {
  const ux = Math.cos(angle), uy = Math.sin(angle);
  const x = center.x - origin.x, y = center.y - origin.y;
  const p = x * ux + y * uy, c = x * uy - y * ux;
  if (includeTangent ? Math.abs(c) > radius : Math.abs(c) >= radius) return Infinity;
  const d = Math.sqrt(Math.max(0, radius * radius - c * c));
  if (p + d < 0) return Infinity;
  return Math.max(0, p - d);
}
