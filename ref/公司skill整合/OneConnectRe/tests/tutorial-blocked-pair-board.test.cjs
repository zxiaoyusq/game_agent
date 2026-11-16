// Independently check the board shown at the first tutorial's blocked example.
const assert = require('node:assert/strict');
const { levels } = require('../config/levels.json');
const source = levels.find(level => level.level === 1).board;
const grid = Array.from({ length: 5 }, (_, row) =>
  Array.from({ length: 5 }, (_, col) => source[col + 1][11 - (row + 4)]));
for (const index of [11, 13, 8, 14, 10, 4]) grid[Math.floor(index / 5)][index % 5] = 0;
const start = [3, 0], end = [4, 1];
assert.equal(grid[start[0]][start[1]], grid[end[0]][end[1]], 'the demonstration tiles must match');
assert.notEqual(grid[start[0]][start[1]], 0);

// Search orthogonal paths with at most two turns, including the outside lane.
function canConnect(board) {
  const directions = [[-1, 0], [0, 1], [1, 0], [0, -1]];
  const queue = directions.map((_, direction) => ({ row: start[0], col: start[1], direction, turns: 0 }));
  const seen = new Set();
  for (let i = 0; i < queue.length; i++) {
    const { row, col, direction, turns } = queue[i];
    const key = [row, col, direction, turns].join(',');
    if (seen.has(key)) continue;
    seen.add(key);
    for (let next = 0; next < 4; next++) {
      const nt = turns + (next === direction ? 0 : 1);
      if (nt > 2) continue;
      const r = row + directions[next][0], c = col + directions[next][1];
      if (r < -1 || r > 5 || c < -1 || c > 5) continue;
      if (r === end[0] && c === end[1]) return true;
      if (r >= 0 && r < 5 && c >= 0 && c < 5 && board[r][c]) continue;
      queue.push({ row: r, col: c, direction: next, turns: nt });
    }
  }
  return false;
}
assert.equal(canConnect(grid), false, 'the two tutorial tiles must not be connectable');
const cleared = grid.map(row => row.slice());
cleared[3][1] = 0;
assert.equal(canConnect(cleared), true, 'clearing the neighboring obstruction makes the pair connectable');
console.log('tutorial blocked pair and later unblock match the board: PASS');
