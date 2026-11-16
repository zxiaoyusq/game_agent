export const GOAL = 5;
export const STORAGE_KEY = 'star-collection-v1';
export function newState(roundId = 0) {
  return { phase: 'playing', count: 0, targetIndex: 0, roundId };
}
// 规则提交不依赖动画、DOM或异步回调，胜利后不再计数。
export function collect(state) {
  if (state.phase !== 'playing') return state;
  const count = state.count + 1;
  return { ...state, count, targetIndex: Math.min(count, 4), phase: count === GOAL ? 'won' : 'playing' };
}
export function restart(state) { return newState(state.roundId + 1); }
export function saveData(state) {
  return { version: 1, count: state.count, targetIndex: state.targetIndex, phase: state.phase };
}
export function restore(raw) {
  if (raw === null) return { state: newState(), invalid: false };
  try {
    const data = JSON.parse(raw);
    if (!data || data.version !== 1 || !Number.isInteger(data.count) || data.count < 0 || data.count > GOAL ||
        data.targetIndex !== Math.min(data.count, 4) || data.phase !== (data.count === GOAL ? 'won' : 'playing')) throw Error('无效存档');
    return { state: { ...newState(), count: data.count, targetIndex: data.targetIndex, phase: data.phase }, invalid: false };
  } catch { return { state: newState(), invalid: true }; }
}
export function targetPoint(state, width, height, config) {
  const [x, y] = config.positions[state.targetIndex];
  const inset = config.star.safeInsetCss;
  return { x: inset + x * Math.max(0, width - inset * 2), y: inset + y * Math.max(0, height - inset * 2) };
}
export function isHit(point, target, radius = 32) {
  return Math.hypot(point.x - target.x, point.y - target.y) <= radius;
}
export function animationScale(progress) {
  const t = Math.min(1, Math.max(0, progress));
  const ease = value => 1 - (1 - value) ** 3;
  return t < 0.6 ? 0.9 + 0.16 * ease(t / 0.6) : 1.06 - 0.06 * ease((t - 0.6) / 0.4);
}
