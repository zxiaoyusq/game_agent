(function () {
  'use strict';
  var installed = false, pendingLevel = null;
  function level(runtime) { var v = runtime.all_global_vars.find(function (x) { return x.name === 'level'; }); return v && v.data; }
  // Respect configured tile size; portrait fitting is handled separately.
  function displaySize(size) { return size; }
  // Center the initial occupied shape, not the surrounding empty grid. Native
  // _place_item uses one-based indices and subtracts half the tile size.
  function centerOffsets(entry, values, runtime) {
    var shape=entry&&(entry.generator&&entry.generator.mask||entry.board),layout=runtime.running_layout;
    if(!Array.isArray(shape)||shape.length!==values[0]||!layout||!Number.isFinite(layout.scrollX)||!Number.isFinite(layout.scrollY))return values;
    var layer=runtime.getLayerByName&&runtime.getLayerByName('Game');
    if(!layer||layer.parallaxX!==1||layer.parallaxY!==1)return values;
    var minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
    for(var y=0;y<shape.length;y++){
      if(!Array.isArray(shape[y])||shape[y].length!==values[1])return values;
      for(var x=0;x<shape[y].length;x++)if(shape[y][x]>0){minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
    }
    if(!Number.isFinite(minX))return values;
    var pitch=values[2]+values[3],next=values.slice();
    next[4]=layout.scrollX-pitch*(minX+maxX+2)/2+values[2]/2;
    next[5]=layout.scrollY-pitch*(minY+maxY+2)/2+values[2]/2;
    return next;
  }
  function applyBoard(runtime) {
    var current = pendingLevel === null ? level(runtime) : pendingLevel;
    var entries = (window.oneConnectLevels && window.oneConnectLevels.levels) || [];
    var entry = entries.find(function (x) { return x.level === current; }) || {level:current,original:true};
    var hasBoard = !!(entry.board || entry.generator);
    var saved = window.oneConnectRoundSave && window.oneConnectRoundSave.restore(entry);
    var tutorialStep = null;
    if (saved && current===1 && window.oneConnectTutorial && window.oneConnectTutorial.needsResumeValidation()) {
      tutorialStep=window.oneConnectTutorial.resumeStep(saved.board);
      if(tutorialStep<0){window.oneConnectRoundSave.clear();saved=null;tutorialStep=null;}
    }
    if (!hasBoard && !saved) { window.oneConnectHost.emit('game.round_ready', {level:current}); window.oneConnectHost.emit('game.round_source', {level:current,resumed:false,configured:false}); return; }
    try {
      var a = runtime.types.t0.instances[0], board = saved ? saved.board : entry.board, counts = {}, generated = null;
      if (entry.generator && !saved) {
        if (!window.oneConnectBoardGenerator) throw Error('board generator unavailable');
        var seed = entry.generator.seed;
        if (seed === undefined) {
          if (window.crypto && window.crypto.getRandomValues) seed = window.crypto.getRandomValues(new Uint32Array(1))[0];
          else seed = Math.floor(Math.random() * 4294967296);
        }
        if (['gravity_down','gravity_up','gravity_left','gravity_right'].includes(entry.movement)) {
          var bounds=entry.gravity, g=entry.generator, rv=runtime.all_global_vars.find(function(v){return v.name==='ROWS_COUNT';}), cv=runtime.all_global_vars.find(function(v){return v.name==='COLUMNS_COUNT';}), gh=rv?rv.data:6,gw=cv?cv.data:12;
          if (!window.oneConnectGravityGenerator || !bounds) throw Error('gravity generator unavailable');
          var mask=Array.from({length:bounds.rows},function(_,r){return Array.from({length:bounds.cols},function(_,c){return g.mask[bounds.left+c][gw-1-(bounds.top+r)];});});
          generated=window.oneConnectGravityGenerator.generate({mask:mask,typeCount:g.typeCount,direction:entry.movement.slice(8)},seed);
          board=Array.from({length:gh},function(){return Array(gw).fill(0);});
          generated.board.forEach(function(row,r){row.forEach(function(v,c){board[bounds.left+c][gw-1-(bounds.top+r)]=v;});});
          generated.strategy=generated.strategy || 'gravity_solved';
        } else { generated=window.oneConnectBoardGenerator.generate(entry.generator, seed); board=generated.board; }
      }
      var variables = runtime.all_global_vars, rows = variables.find(function(v){return v.name === 'ROWS_COUNT';}), cols = variables.find(function(v){return v.name === 'COLUMNS_COUNT';});
      rows = rows ? rows.data : 6; cols = cols ? cols.data : 12;
      if (!a || a.cx !== cols + 2 || a.cy !== rows + 2 || !Array.isArray(board) || board.length !== rows) throw Error('unsupported board dimensions');
      board.forEach(function (row) { if (!Array.isArray(row) || row.length !== cols) throw Error('board dimensions do not match runtime'); row.forEach(function (v) { if (!Number.isInteger(v) || v < 0 || v > 30) throw Error('tile out of range'); if (v) counts[v] = (counts[v] || 0) + 1; }); });
      if (Object.values(counts).some(function (n) { return n % 2; })) throw Error('tiles must have even counts');
      var present = Object.values(counts).reduce(function (n, c) { return n + c; }, 0);
      if (present < 2) throw Error('board must contain at least two tiles');
      var globals = null;
      if (present < rows * cols) {
        globals = runtime.types.t32 && runtime.types.t32.instances[0];
        if (!globals || !Array.isArray(globals.instance_vars) || !Number.isFinite(globals.instance_vars[3])) throw Error('missing board counter');
      }
      for (var y = 1; y <= rows; y++) for (var x = 1; x <= cols; x++) a.arr[x][y][0] = board[y-1][x-1];
      if (globals) globals.instance_vars[3] = rows * cols - present;
      if (saved) ['timer','score','tip','shuffle'].forEach(function(name){var v=variables.find(function(x){return x.name===name;});if(v)v.data=saved[name];});
      if (generated) {
        var generatedEvent={level:current,seed:generated.seed,strategy:generated.strategy};
        if (Number.isInteger(generated.attempt)) generatedEvent.searchAttempts=generated.strategy==='adjacent_lane_fallback'?generated.attempt:generated.attempt+1;
        window.oneConnectHost.emit('game.board_generated', generatedEvent);
      }
      var boardEvent={level:current};if(tutorialStep!==null)boardEvent.tutorialStep=tutorialStep;
      window.oneConnectHost.emit(hasBoard ? 'game.board_configured' : 'game.round_ready', boardEvent);
      window.oneConnectHost.emit('game.round_source', {level:current,resumed:!!saved,configured:hasBoard});
    } catch (error) { window.oneConnectHost.emit('config.board_error', { level: current, message: String(error) }); }
  }
  function install() {
    if (installed) return;
    if (cr.action.prototype.run_system) {
      var originalSystem = cr.action.prototype.run_system, baseline = null;
      cr.action.prototype.run_system = function () {
        if (this.sid === 532162384668575) {
          var vars = this.runtime.all_global_vars;
          var keys = ['ROWS_COUNT','COLUMNS_COUNT','ITEM_SIZE','ITEM_SPACING','BOARD_OFFSET_X','BOARD_OFFSET_Y'];
          var targets = keys.map(function(key){ return vars.find(function(v){ return v.name === key; }); });
          if (targets.every(Boolean)) {
            if (!baseline) baseline = targets.map(function(v){ return v.data; });
            var current = pendingLevel === null ? level(this.runtime) : pendingLevel;
            var entries = window.oneConnectLevels && window.oneConnectLevels.levels;
            var entry = Array.isArray(entries) && entries.find(function(x){ return x.level === current; });
            var size = displaySize(entry && entry.boardSize);
            var values = size ? [size.rows,size.cols,size.itemSize,size.spacing,size.offsetX,size.offsetY] : baseline;
            values = centerOffsets(entry, values, this.runtime);
            targets.forEach(function(v,i){ v.data = values[i]; });
          }
        }
        var result=originalSystem.apply(this, arguments);
        // The original spawn tween targets 96px even when the configured cells
        // are smaller. Retarget only the verified compact eight-row presets,
        // leaving the original board untouched.
        if (this.sid === 511736629732629) {
          var currentLevel=pendingLevel===null?level(this.runtime):pendingLevel;
          var configs=window.oneConnectLevels&&window.oneConnectLevels.levels;
          var configured=Array.isArray(configs)&&configs.find(function(x){return x.level===currentLevel;});
          var compact=displaySize(configured&&configured.boardSize);
          if (compact&&compact.rows===8&&[8,10,12].indexOf(compact.cols)!==-1&&[65,75].indexOf(compact.itemSize)!==-1) {
            var tileType=this.runtime.types.t5, selected=tileType&&tileType.getCurrentSol().getObjects();
            var tile=selected&&selected[selected.length-1];
            if (tile) (tile.behavior_insts||[]).forEach(function(tween){
              if (tween.tweened===1&&tween.target==='96,96'&&tween.tween_list&&tween.tween_list.default) {
                var target=compact.itemSize;tween.target=target+','+target;tween.tween_list.default.targetparam1=target;tween.tween_list.default.targetparam2=target;
              }
            });
          }
        }
        return result;
      };
    }
    var previous = cr.action.prototype.run_object;
    cr.action.prototype.run_object = function () {
      var before = pendingLevel;
      if (this.sid === 141109058915873) pendingLevel = level(this.runtime) + 1;
      try {
        if ([155796769104064, 491047488641600, 657297107410907, 422821596409828].indexOf(this.sid) !== -1) {
          var movementRows = window.oneConnectLevels && window.oneConnectLevels.levels;
          var movementEntry = Array.isArray(movementRows) && movementRows.find(function (x) { return x.level === level(this.runtime); }, this);
          if (movementEntry && movementEntry.movement === 'static') return;
        }
        if (this.sid === 265515752420816) {
          var current = pendingLevel === null ? level(this.runtime) : pendingLevel;
          var rows = window.oneConnectLevels && window.oneConnectLevels.levels;
          var entry = Array.isArray(rows) && rows.find(function (x) { return x.level === current; });
          var theme = this.runtime.all_global_vars.find(function (v) { return v.name === 'theme'; });
          if (theme) theme.data = entry && Number.isInteger(entry.theme) && entry.theme >= 0 && entry.theme <= 2 ? entry.theme : 0;
        }
        var result = previous.apply(this, arguments);
        if (this.sid === 673515574013169) applyBoard(this.runtime);
        return result;
      } finally { if (this.sid === 141109058915873) pendingLevel = before; }
    };
    installed = true;
  }
  window.oneConnectBoard = { install: install };
}());
