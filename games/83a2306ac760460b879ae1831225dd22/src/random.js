// 规则随机流与AI随机流分离；拒绝采样避免取余偏差。
export function nextWord(stream) {
  let x = stream.value >>> 0;
  x ^= x << 13; x ^= x >>> 17; x ^= x << 5;
  stream.value = x >>> 0;
  return stream.value;
}
export function uniform(stream, count) {
  // xorshift32的非零周期含2^32-1个值，先映射到0起始范围。
  const limit = Math.floor(4294967295 / count) * count;
  let x;
  do { x = nextWord(stream)-1; } while (x >= limit);
  return x % count;
}
export function entropy() { return crypto.getRandomValues(new Uint32Array(1))[0] || 1; }
export function streams(seed) {
  return {dice: {value:(seed >>> 0) || 1}, ai:{value:((seed ^ 0x9e3779b9) >>> 0) || 1}};
}
