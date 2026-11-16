(function () {
  'use strict';
  var installed = false;
  var hiddenTimerObjects = new WeakMap(), hiddenBoardObjects = new WeakMap();
  function levelEntry(runtime) {
    var current = runtime.all_global_vars.find(function (v) { return v.name === 'level'; });
    var rows = window.oneConnectLevels && window.oneConnectLevels.levels;
    var entry = Array.isArray(rows) && current && rows.find(function (row) { return row.level === current.data; });
    return entry;
  }
  function isUntimed(runtime) {
    var entry = levelEntry(runtime);
    return !!entry && entry.timed === false;
  }
  function updateTimerDisplay() {
    var runtime = window.cr_getC2Runtime && window.cr_getC2Runtime();
    if (!runtime || !runtime.running_layout || runtime.running_layout.name !== 'game') return;
    var entry = levelEntry(runtime), board = runtime.types.t38;
    if (board) board.instances.forEach(function (obj) {
      if (entry && entry.boardBackground === 'hidden') {
        if (!hiddenBoardObjects.has(obj)) hiddenBoardObjects.set(obj, obj.visible);
        if (obj.visible) { obj.visible = false; runtime.redraw = true; }
      } else if (hiddenBoardObjects.has(obj)) {
        obj.visible = hiddenBoardObjects.get(obj); hiddenBoardObjects.delete(obj); runtime.redraw = true;
      }
    });
    var candidates = [];
    function add(type, predicate) {
      var t = runtime.types[type];
      if (t) t.instances.forEach(function (obj) { if (obj.layer && obj.layer.name === 'UI' && predicate(obj)) candidates.push(obj); });
    }
    add('t24', function (o) { return o.cur_frame === 1; });
    add('t25', function (o) { return o.instance_vars && o.instance_vars[0] === 1; });
    var timerText = candidates.find(function (o) { return o.instance_vars && o.instance_vars[0] === 1; });
    add('t36', function (o) { return timerText && Math.abs(o.x - timerText.x + 7) < 1 && Math.abs(o.y - timerText.y + 22) < 1; });
    var hide = isUntimed(runtime);
    candidates.forEach(function (obj) {
      if (hide && !hiddenTimerObjects.has(obj)) { hiddenTimerObjects.set(obj, obj.visible); obj.visible = false; runtime.redraw = true; }
      else if (!hide && hiddenTimerObjects.has(obj)) { obj.visible = hiddenTimerObjects.get(obj); hiddenTimerObjects.delete(obj); runtime.redraw = true; }
      else if (hide && obj.visible) { obj.visible = false; runtime.redraw = true; }
    });
  }
  function install() {
    if (installed) return;
    if (!window.cr || !cr.action || !cr.action.prototype.run_system) throw new Error('Construct action runtime unavailable');
    var original = cr.action.prototype.run_system;
    cr.action.prototype.run_system = function () {
      if (this.sid === 367702696840255 && isUntimed(this.runtime)) return;
      var result = original.apply(this, arguments);
      // Core init uses timerInit (level 1); saved progress may start at another level.
      if (this.sid === 532162384668575) {
        var vars = this.runtime.all_global_vars;
        var current = vars.find(function (v) { return v.name === 'level'; });
        var timer = vars.find(function (v) { return v.name === 'timer'; });
        var rows = window.oneConnectLevels && window.oneConnectLevels.levels;
        var entry = Array.isArray(rows) && current && rows.find(function (row) { return row.level === current.data; });
        if (timer && current && current.data > 1) timer.data = entry && Number.isInteger(entry.seconds) && entry.seconds >= 1 && entry.seconds <= 3600 ? entry.seconds : 300;
      }
      if (this.sid === 196425296963217 || this.sid === 431416332694720 || this.sid === 946296122197588) {
        try {
          var values = {};
          this.runtime.all_global_vars.forEach(function (v) { if (v.name === 'level' || v.name === 'score' || v.name === 'tip' || v.name === 'shuffle') values[v.name] = v.data; });
          if (this.sid === 196425296963217) values.source = window.oneConnectHammer && window.oneConnectHammer.state().busy ? 'hammer' : 'normal';
          window.oneConnectHost.emit(this.sid === 196425296963217 ? 'game.match' : this.sid === 946296122197588 ? 'game.hint' : 'game.level_start', values);
        } catch (error) { console.warn('One Connect event hook failed', error); }
      }
      return result;
    };
    if (cr.action.prototype.run_object) {
      var originalObject = cr.action.prototype.run_object;
      cr.action.prototype.run_object = function () {
        var result = originalObject.apply(this, arguments);
        if (this.sid === 342934048923318) {
          try { var state = {}; this.runtime.all_global_vars.forEach(function (v) { if (v.name === 'level' || v.name === 'shuffle') state[v.name] = v.data; }); window.oneConnectHost.emit('game.shuffle', state); }
          catch (error) { console.warn('One Connect event hook failed', error); }
        }
        return result;
      };
    }
    // SpriteFont is created with the original timer before level overrides apply.
    // Refresh once after board setup so the first visible value matches the actual timer.
    if (window.addEventListener) window.addEventListener('oneconnect:event', function (event) {
      if (!event.detail || event.detail.type !== 'game.board_configured' && event.detail.type !== 'game.round_ready') return;
      var expected=event.detail.detail.level;
      window.setTimeout(function () {
        var runtime=window.cr_getC2Runtime && window.cr_getC2Runtime();
        if (!runtime || !runtime.running_layout || runtime.running_layout.name !== 'game') return;
        var level=runtime.all_global_vars.find(function (v) { return v.name === 'level'; });
        var timer=runtime.all_global_vars.find(function (v) { return v.name === 'timer'; });
        var font=runtime.types.t25 && runtime.types.t25.instances.find(function (t) { return t.instance_vars && t.instance_vars[0] === 1; });
        if (!level || level.data !== expected || !timer || !font || !cr.plugins_.Spritefont2) return;
        var value=Math.max(0,Math.floor(timer.data)),formatted=Math.floor(value/60)+':'+String(value%60).padStart(2,'0');
        cr.plugins_.Spritefont2.prototype.acts.SetText.call(font,formatted);
      },0);
    });
    window.setInterval(updateTimerDisplay, 150);
    installed = true;
  }
  window.oneConnectInstrumentation = { install: install };
}());
