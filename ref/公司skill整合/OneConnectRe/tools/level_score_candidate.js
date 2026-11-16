/* Independent round-score experiment. Values are unknown unless the start
 * score was captured for this same round; this is not a star-rating rule. */
(function () {
  'use strict';
  var level = null, start = null, matches = null;
  function validLevel(value) { return Number.isInteger(value) && value > 0; }
  function validScore(value) { return Number.isFinite(value) && value >= 0; }
  function begin(id, total) {
    level = validLevel(id) ? id : null;
    start = level !== null && validScore(total) ? total : null;
    matches = start === null ? null : 0;
  }
  function restore(saved) {
    level = saved && validLevel(saved.level) ? saved.level : null;
    start = level !== null && validScore(saved.scoreBase) && validScore(saved.score) &&
      saved.scoreBase <= saved.score ? saved.scoreBase : null;
    matches = start !== null && Number.isSafeInteger(saved.matchScore) && saved.matchScore >= 0 &&
      saved.matchScore <= saved.score - start ? saved.matchScore : null;
  }
  function baseline(id, total) {
    return level === id && start !== null && validScore(total) && total >= start ? start : null;
  }
  function earned(id, total) {
    var base = baseline(id, total);
    return base === null ? null : total - base;
  }
  function match(id) {
    if (id !== level || matches === null) return;
    var next = matches + 100 + (id - 1) * 10;
    matches = Number.isSafeInteger(next) ? next : null;
  }
  function matchScore(id, total) {
    var gain = earned(id, total);
    return gain !== null && matches !== null && matches <= gain ? matches : null;
  }
  window.oneConnectLevelScoreCandidate = {begin:begin, restore:restore, baseline:baseline, earned:earned, match:match, matchScore:matchScore};
}());
