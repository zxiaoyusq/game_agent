// 球数组统一按管底到管口排列；一次移动连续同色球，直到目标管满。
export const cloneBoard = board => board.map(tube => [...tube]);
export const isComplete = (board, capacity) => board.every(tube => !tube.length || (tube.length === capacity && tube.every(color => color === tube[0])));
export function moveCount(board, from, to, capacity) {
  if (from === to || !board[from]?.length || !board[to] || board[to].length >= capacity) return 0;
  const color = board[from].at(-1);
  if (board[to].length && board[to].at(-1) !== color) return 0;
  let count = 0;
  for (let index = board[from].length - 1; index >= 0 && board[from][index] === color; index--) count++;
  return Math.min(count, capacity - board[to].length);
}
export function applyMove(board, from, to, capacity) {
  const count = moveCount(board, from, to, capacity);
  if (!count) return null;
  const next = cloneBoard(board);
  next[to].push(...next[from].splice(-count));
  return { board: next, count, color: board[from].at(-1) };
}
// 以管内容排序消除同构局面，优先合并同色堆，跳过把完整单色管移进空管的循环。
export function solve(board, capacity, maxStates = 180000) {
  const visited = new Set(); let expanded = 0;
  const path = [];
  function visit(state, lastFrom = -1, lastTo = -1, depth = 0) {
    if (isComplete(state, capacity)) return [...path];
    if (expanded++ >= maxStates || depth > 180) return null;
    const key = state.map(tube => tube.join('.')).sort().join('|');
    if (visited.has(key)) return null;
    visited.add(key);
    const candidates = [];
    for (let from = 0; from < state.length; from++) {
      if (!state[from].length || (state[from].length === capacity && new Set(state[from]).size === 1)) continue;
      let usedEmpty = false;
      for (let to = 0; to < state.length; to++) {
        if (from === lastTo && to === lastFrom) continue;
        const count = moveCount(state, from, to, capacity);
        if (!count) continue;
        if (!state[to].length) {
          if (usedEmpty || new Set(state[from]).size === 1) continue;
          usedEmpty = true;
        }
        const score = (state[to].length ? 20 : 0) + count * 3 + (state[to].length + count === capacity ? 30 : 0) + (count === state[from].length ? 5 : 0);
        candidates.push({ from, to, score });
      }
    }
    candidates.sort((a, b) => b.score - a.score);
    for (const { from, to } of candidates) {
      path.push([from, to]);
      const result = visit(applyMove(state, from, to, capacity).board, from, to, depth + 1);
      if (result) return result;
      path.pop();
      if (expanded >= maxStates) break;
    }
    return null;
  }
  return { solution: visit(cloneBoard(board)), expanded };
}
