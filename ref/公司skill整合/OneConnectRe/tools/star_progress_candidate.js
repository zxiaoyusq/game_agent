/* Candidate per-level best-star storage. No game or reward hooks are installed.
 * Kept separate from production until the source rules and save flow are reviewed. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.oneConnectStarProgressCandidate = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  var key = 'oneconnect.star-progress.candidate.v1';
  function validate(data) {
    if (!data || data.version !== 1 || !data.levels || typeof data.levels !== 'object' || Array.isArray(data.levels)) return false;
    return Object.keys(data.levels).every(function (id) {
      var level = Number(id), stars = data.levels[id];
      return String(level) === id && Number.isInteger(level) && level >= 1 && level <= 100000 &&
        Number.isInteger(stars) && stars >= 0 && stars <= 3;
    });
  }
  function load(storage) {
    var raw = storage.getItem(key);
    if (raw === null) return {version:1, levels:{}};
    var data = JSON.parse(raw);
    if (!validate(data)) throw new Error('invalid star progress; refusing to overwrite');
    return data;
  }
  function record(storage, level, stars) {
    if (!Number.isInteger(level) || level < 1 || level > 100000 || !Number.isInteger(stars) || stars < 0 || stars > 3) throw new RangeError('invalid level or stars');
    var data = load(storage), recorded = Object.prototype.hasOwnProperty.call(data.levels, level), previous = recorded ? data.levels[level] : 0;
    // This delta describes best-star history only. It is not a chest reward.
    if (recorded && stars <= previous) return {previous:previous, best:previous, bestIncrease:0};
    data.levels[level] = stars;
    storage.setItem(key, JSON.stringify(data));
    return {previous:previous, best:stars, bestIncrease:stars - previous};
  }
  function total(storage) {
    var levels = load(storage).levels;
    return Object.keys(levels).reduce(function (sum, id) { return sum + levels[id]; }, 0);
  }
  // The competitor counts thresholds reached. The caller must supply a
  // project-calibrated base and a score with the same unit; no default is inferred.
  function rate(score, base) {
    if (!Number.isSafeInteger(score) || score < 0 || !Number.isSafeInteger(base) || base < 1 || base > Math.floor(Number.MAX_SAFE_INTEGER / 2)) throw new RangeError('invalid score or threshold base');
    var thresholds = [base, base + Math.floor(base / 2), base * 2];
    return {thresholds:thresholds, stars:thresholds.filter(function (threshold) { return score >= threshold; }).length};
  }
  return {load:load, record:record, total:total, rate:rate};
});
