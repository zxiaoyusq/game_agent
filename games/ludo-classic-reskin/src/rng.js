// 随机源不接收棋盘或玩家类型；MOVE与AI均不消耗它。
export const ALGORITHM = "mulberry32-v1";
export const uint32 = (n) => Number.isInteger(n) && n >= 0 && n <= 0xffffffff;
export function createRng(seed) {
  if (!uint32(seed)) throw new Error("种子必须是uint32");
  return {
    algorithm: ALGORITHM,
    initialSeed: seed,
    state: seed,
    rawDrawCount: 0,
  };
}
export function raw(rng) {
  const state = (rng.state + 0x6d2b79f5) >>> 0;
  let t = Math.imul(state ^ (state >>> 15), state | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return {
    value: (t ^ (t >>> 14)) >>> 0,
    rng: { ...rng, state, rawDrawCount: rng.rawDrawCount + 1 },
  };
}
export function bounded(rng, bound, draw = raw) {
  if (!Number.isInteger(bound) || bound < 1 || bound > 0x100000000)
    throw new Error("随机界限错误");
  const ceiling = Math.floor(0x100000000 / bound) * bound;
  let next;
  do {
    next = draw(rng);
    rng = next.rng;
  } while (next.value >= ceiling);
  return { value: next.value % bound, rng };
}
export function freshSeed() {
  return crypto.getRandomValues(new Uint32Array(1))[0];
}
export function seedFromSearch(search) {
  const value = new URLSearchParams(search).get("seed");
  if (value === null) return { seed: null, error: null };
  if (!/^\d+$/.test(value) || !uint32(Number(value)))
    return { seed: null, error: "种子参数无效，使用公平随机新局" };
  return { seed: Number(value), error: null };
}
