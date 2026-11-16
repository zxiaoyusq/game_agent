/* Geometry for the proposed portrait gameplay layout, in CSS pixels.
 * This module does not mutate the Construct runtime or existing saves. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.oneConnectLayoutGeometry = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function number(value, name, min) {
    if (!Number.isFinite(value) || value < min) throw new RangeError('invalid ' + name);
    return value;
  }
  function calculate(options) {
    options = options || {};
    var width = number(options.width, 'width', 1);
    var height = number(options.height, 'height', 1);
    var rows = number(options.rows, 'rows', 1);
    var cols = number(options.cols, 'cols', 1);
    if (!Number.isInteger(rows) || !Number.isInteger(cols)) throw new RangeError('board dimensions must be integers');
    var safe = options.safeArea || {};
    var left = number(safe.left || 0, 'safeArea.left', 0);
    var right = number(safe.right || 0, 'safeArea.right', 0);
    var top = number(safe.top || 0, 'safeArea.top', 0);
    var bottom = number(safe.bottom || 0, 'safeArea.bottom', 0);
    var usableWidth = width - left - right;
    // 720 x 1600 reference: the bottom ad region is about 110 px high.
    var banner = options.bannerHeight === undefined || options.bannerHeight === null ? Math.min(usableWidth * 110 / 720, height * 0.11) : number(options.bannerHeight, 'bannerHeight', 0);
    var usableHeight = height - top - bottom - banner;
    if (usableWidth <= 0 || usableHeight <= 0) throw new RangeError('safe area exceeds viewport');

    var margin = Math.max(4, Math.min(12, usableWidth * 0.025));
    var headerHeight = Math.max(44, Math.min(82, usableWidth * 0.105));
    var progressHeight = Math.max(22, Math.min(44, usableWidth * 0.052));
    // Reference HUD uses 140 x 70 controls on a 720-wide canvas.
    var slotWidth = usableWidth * 148 / 720;
    var toolbarHeight = Math.min(usableWidth * 94 / 720, usableHeight * 0.10);
    var gap = Math.max(4, Math.min(10, usableHeight * 0.012));
    var boardTop = top + headerHeight + progressHeight + gap;
    var toolbarTop = top + usableHeight - toolbarHeight - usableWidth * 22 / 720;
    var boardHeight = toolbarTop - gap - boardTop;
    var boardWidth = usableWidth - 2 * margin;
    if (boardHeight <= 0 || boardWidth <= 0) throw new RangeError('viewport too small for gameplay');
    var pitch = Math.min(boardWidth / cols, boardHeight / rows);
    var board = {left: left + (usableWidth - cols * pitch) / 2,
      top: boardTop + (boardHeight - rows * pitch) / 2,
      width: cols * pitch, height: rows * pitch, pitch: pitch};
    if (slotWidth <= 0) throw new RangeError('viewport too narrow for tools');
    var centers = [-223, -73, 75, 225];
    var slots = ['reserved', 'hammer', 'shuffle', 'hint'].map(function (id, index) {
      return {id: id, left: left + usableWidth * (0.5 + centers[index] / 720) - slotWidth / 2, top: toolbarTop,
        width: slotWidth, height: toolbarHeight};
    });
    return {header: {left: left, top: top, width: usableWidth, height: headerHeight},
      progress: {left:left + usableWidth * .28, top:top + headerHeight, width:usableWidth * .44, height:progressHeight},
      board: board, fitArea: {left:left + margin, top:boardTop, width:boardWidth, height:boardHeight}, tools: slots,
      banner: {left: left, top: top + usableHeight, width: usableWidth, height: banner}};
  }
  return {calculate: calculate};
});
