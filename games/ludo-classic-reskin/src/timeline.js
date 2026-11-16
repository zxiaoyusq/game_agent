import { movementPath, cellSize, seats } from './map.js';
export function buildTimeline(before, after, geo) {
  const event = after.lastEvent;
  if (event.type === 'ROLL')
    return [{ kind: 'dice', duration: 25000 / 30, actor: event.actor, dice: event.dice }];
  const piece = before.pieces.find((p) => p.id === event.pieceId);
  const path = movementPath(piece, event.from, event.to, geo);
  const clips = [
    { kind: 'walk', duration: (path.length - 1) * 110, pieceId: piece.id, path },
  ];
  if (event.capturedIds.length) {
    clips.push({ kind: 'impact', duration: 100, point: geo.point(piece, event.to) });
    const paths = event.capturedIds.map((id) => {
      const victim = before.pieces.find((p) => p.id === id);
      const points = Array.from({ length: victim.progress + 1 }, (_, i) => ({
        ...geo.point(victim, victim.progress - i),
        progress: victim.progress - i,
      }));
      points.push({ ...geo.point(victim, -1), progress: -1 });
      return { pieceId: id, points, duration: victim.progress * 30 + 100 };
    });
    clips.push({
      kind: 'capture',
      duration: Math.max(...paths.map((p) => p.duration)),
      paths,
    });
  }
  if (event.to === 56)
    clips.push({
      kind: 'home',
      duration: 375,
      point: geo.point(piece, 56),
      owner: piece.owner,
    });
  if (after.phase === 'finished')
    clips.push({ kind: 'victory', duration: 1000, owner: after.winner });
  return clips;
}
export function sampleClip(clip, elapsed) {
  const fraction = Math.min(1, elapsed / clip.duration);
  const result = { kind: clip.kind, fraction, positions: [] };
  if (clip.kind === 'dice') {
    const seat = seats[clip.actor];
    return {
      ...result,
      frameId: Math.min(24, Math.floor(elapsed * 0.03)),
      x: seat.diceX,
      y: seat.y - Math.abs(Math.sin(fraction * Math.PI * 3)) * 6,
    };
  }
  const interpolate = (id, points, time, duration, arc) => {
    const segment = Math.min(points.length - 2, Math.floor(time / duration));
    const u = Math.min(1, Math.max(0, (time - segment * duration) / duration));
    const a = points[segment],
      b = points[segment + 1];
    return {
      pieceId: id,
      x: a.x + (b.x - a.x) * u,
      y: a.y + (b.y - a.y) * u - Math.sin(Math.PI * u) * arc,
      scale: 1 + (arc ? 0.15 * Math.sin(Math.PI * u) : 0),
      stepIndex: segment,
      progress: a.progress + (b.progress - a.progress) * u,
      u,
    };
  };
  if (clip.kind === 'walk')
    result.positions.push(
      interpolate(clip.pieceId, clip.path, elapsed, 110, cellSize * 0.3),
    );
  if (clip.kind === 'capture') {
    for (const path of clip.paths) {
      const reverseTime = (path.points.length - 2) * 30;
      if (elapsed < reverseTime)
        result.positions.push(
          interpolate(path.pieceId, path.points.slice(0, -1), elapsed, 30, 0),
        );
      else {
        // 最后100ms使用cubic easeOut，逆路每格30ms保持原样。
        const u = Math.min(1, Math.max(0, (elapsed - reverseTime) / 100));
        const eased = 1 - (1 - u) ** 3;
        result.positions.push(
          interpolate(path.pieceId, path.points.slice(-2), eased * 100, 100, 0),
        );
      }
    }
  }
  return result;
}
// 单一rAF时间轴：取消后旧动画绝不触发end，不负责提交规则。
export function createTimeline() {
  let active = null;
  let epoch = 0;
  return {
    get active() {
      return active;
    },
    get epoch() {
      return epoch;
    },
    start(before, after, geo, now) {
      epoch++;
      active = {
        before: structuredClone(before),
        after: structuredClone(after),
        clips: buildTimeline(before, after, geo),
        index: 0,
        start: now,
        epoch,
        started: false,
      };
    },
    cancel() {
      const old = active;
      active = null;
      epoch++;
      return old;
    },
    sample(now) {
      if (!active) return null;
      const clip = active.clips[active.index];
      const elapsed = Math.max(0, now - active.start);
      return {
        ...sampleClip(clip, Math.min(elapsed, clip.duration)),
        clip,
        elapsed,
        done: elapsed >= clip.duration,
      };
    },
    advance(now) {
      if (!active) return false;
      active.index++;
      if (active.index >= active.clips.length) {
        active = null;
        return false;
      }
      active.start = now;
      active.started = false;
      return true;
    },
  };
}
