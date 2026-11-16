/* Optional project-side mapping experiment; not a decoded competitor rule.
 * This file is not loaded by the production game or editor. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.oneConnectTilePoolCandidate = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function apply(generated, pool, seed) {
    if (!generated || !Array.isArray(generated.board) || !generated.board.length ||
        !Array.isArray(generated.board[0]) || !generated.board[0].length) throw Error('invalid generated board');
    var width = generated.board[0].length;
    if (generated.board.some(function (row) { return !Array.isArray(row) || row.length !== width ||
        row.some(function (value) { return !Number.isInteger(value) || value < 0 || value > 30; }); })) throw Error('invalid tile ids');
    if (!Array.isArray(pool) || !pool.length || pool.length > 30 ||
        pool.some(function (id) { return !Number.isInteger(id) || id < 1 || id > 30; }) ||
        new Set(pool).size !== pool.length) throw Error('pool must contain distinct tile ids from 1 to 30');
    if (!Number.isInteger(seed) || seed < 0 || seed > 4294967295) throw Error('invalid seed');
    var kinds = Array.from(new Set(generated.board.flat().filter(function (v) { return v > 0; }))).sort(function (a,b) { return a-b; });
    if (!kinds.length || kinds.length > pool.length) throw Error('pool cannot satisfy board kinds');
    // Separate mapping RNG, so choosing appearances does not advance the
    // generator's random stream or change its board shape or solution path.
    var state = ((seed >>> 0) ^ 0x9e3779b9) >>> 0;
    if (!state) state = 0x6d2b79f5;
    function random() { state ^= state << 13; state ^= state >>> 17; state ^= state << 5; return (state >>> 0) / 4294967296; }
    var choices = pool.slice();
    for (var i = choices.length - 1; i > 0; i--) { var j = Math.floor(random() * (i+1)), temp = choices[i]; choices[i] = choices[j]; choices[j] = temp; }
    var mapping = new Map(kinds.map(function (kind, i) { return [kind, choices[i]]; }));
    return Object.assign({}, generated, {board:generated.board.map(function (row) {
      return row.map(function (value) { return value ? mapping.get(value) : 0; });
    }), selectedTileIds:kinds.map(function (kind) { return mapping.get(kind); })});
  }
  return {apply:apply};
});
