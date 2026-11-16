(function (root, factory) {
  var rules = factory();
  if (typeof module === 'object' && module.exports) module.exports = rules;
  else root.CarromDiscRules = rules;
})(typeof window === 'undefined' ? globalThis : window, function () {
  'use strict';
  function isSixDiscDelhi(mode, table) { return mode === 0 && table === 0; }
  function target(mode, table) { return isSixDiscDelhi(mode, table) ? 6 : 9; }
  function turnTicks(mode, table, originalTicks, timeBonus) {
    return (isSixDiscDelhi(mode, table) ? 20 * 60 : originalTicks) + timeBonus * 2;
  }
  function hasWon(mode, table, count) { return count === target(mode, table); }
  function layout(mode, table) {
    if (!isSixDiscDelhi(mode, table)) return null;
    var player = [], opponent = [];
    // Two interleaved rings, calibrated from the competitor screenshot, with
    // clearance for the existing project's 16-unit physics radius.
    for (var i = 0; i < 6; i++) {
      var inner = (-67 + i * 60) * Math.PI / 180;
      var outer = (-97 + i * 60) * Math.PI / 180;
      var inPoint = {x: 317 + 34 * Math.cos(inner), y: 317 + 34 * Math.sin(inner)};
      var outPoint = {x: 317 + 68 * Math.cos(outer), y: 317 + 68 * Math.sin(outer)};
      (i % 2 === 0 ? opponent : player).push(inPoint);
      (i % 2 === 0 ? player : opponent).push(outPoint);
    }
    return {player: player, opponent: opponent};
  }
  return {target: target, hasWon: hasWon, layout: layout, turnTicks: turnTicks};
});
