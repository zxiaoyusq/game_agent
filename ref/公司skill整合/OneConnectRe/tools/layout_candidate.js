/* Unverified portrait layout candidate; loaded only in the isolated copy. */
(function () {
  'use strict';
  var frameKey = '', boardLayer = null, baseScale = null, fittedScale = null, fittedRuntime = null, placeholder = null, notice = null, noticeTimer = null, autoShuffling = false, roundEnded = false, busyUntil = 0, toolArt = [];
  var layoutOptions = {bannerHeight: null, safeArea: {top:0, right:0, bottom:0, left:0}};
  var geometryKey = '', geometryCache = null;
  var themeKey='oneconnect.theme-tool.candidate.v1', themeMemory=2, themeLoaded=false, themeRewardSaved=true, themeExternalRevision=0;
  function themeStock(){if(themeLoaded)return themeMemory;try{var raw=localStorage.getItem(themeKey);if(raw!==null&&/^\d+$/.test(raw))themeMemory=Math.min(999,Number(raw));}catch(_){}themeLoaded=true;return themeMemory;}
  function saveThemeStock(value){themeMemory=value;try{localStorage.setItem(themeKey,String(value));return true;}catch(_){return false;}}
  function retryThemeReward(before,revision){if(revision!==themeExternalRevision)return 'conflict';var current=themeStock();try{var raw=localStorage.getItem(themeKey);if(!(raw===String(before)||(raw===null&&before===2)))return 'conflict';localStorage.setItem(themeKey,String(current));themeRewardSaved=true;return 'saved';}catch(_){return 'retry';}}
  window.oneConnectThemeInventoryCandidate={count:themeStock,credit:function(n){var old=themeStock();if(!Number.isInteger(n)||n<1||old+n>999)return false;themeRewardSaved=saveThemeStock(old+n);return true;},rewardPersisted:function(){return themeRewardSaved;},rewardRevision:function(){return themeExternalRevision;},retryRewardSave:retryThemeReward};
  function configure(options) {
    options = options || {};
    var next = {bannerHeight: options.bannerHeight === undefined ? layoutOptions.bannerHeight : options.bannerHeight,
      safeArea: Object.assign({}, layoutOptions.safeArea, options.safeArea || {})};
    ['top','right','bottom','left'].forEach(function (key) {
      if (!Number.isFinite(next.safeArea[key]) || next.safeArea[key] < 0) throw new RangeError('invalid safe-area inset');
    });
    if (next.bannerHeight !== null && (!Number.isFinite(next.bannerHeight) || next.bannerHeight < 0)) throw new RangeError('invalid banner height');
    layoutOptions = next;
    frameKey = '';
    geometryKey = ''; geometryCache = null;
  }
  function getVariable(r, name) {
    var v = r.all_global_vars.find(function (item) { return item.name === name; });
    return v && v.data;
  }
  function setTextIfChanged(element, value) {
    value = String(value);
    if (element.textContent !== value) element.textContent = value;
  }
  function setStyleIfChanged(element, property, value) {
    if (element.style[property] !== value) element.style[property] = value;
  }
  function visualPoint(r, layer, x, y) {
    var rect = r.canvas.getBoundingClientRect(), ratio = r.isRetina ? r.devicePixelRatio : 1;
    return {x: rect.left + layer.layerToCanvas(x, y, true) * ratio * rect.width / r.canvas.width,
      y: rect.top + layer.layerToCanvas(x, y, false) * ratio * rect.height / r.canvas.height};
  }
  function fitBoard(r, area) {
    var tiles = r.types.t5 && r.types.t5.instances;
    if (!tiles || !tiles.length || !tiles[0].layer) return false;
    var layer = tiles[0].layer;
    if (boardLayer !== layer) { boardLayer = layer; baseScale = layer.scale; }
    layer.scale = baseScale;
    var tile = tiles[0], vars = tile.instance_vars;
    var columns = getVariable(r, 'COLUMNS_COUNT'), rows = getVariable(r, 'ROWS_COUNT');
    var size = getVariable(r, 'ITEM_SIZE'), spacing = getVariable(r, 'ITEM_SPACING');
    if (!vars || !Number.isInteger(vars[1]) || vars[1] < 1 || vars[1] > rows ||
        !Number.isInteger(vars[2]) || vars[2] < 1 || vars[2] > columns ||
        !Number.isFinite(size) || size <= 0 || !Number.isFinite(spacing) || spacing < 0 || !rows || !columns) return false;
    var pitch = size + spacing;
    var originX = tile.x - (vars[2] - 1) * pitch, originY = tile.y - (vars[1] - 1) * pitch;
    var minCol=0,maxCol=columns-1,minRow=0,maxRow=rows-1,level=getVariable(r,'level');
    var entries=window.oneConnectLevels&&window.oneConnectLevels.levels,entry=Array.isArray(entries)&&entries.find(function(e){return e.level===level;});
    var shape=entry&&(entry.generator&&entry.generator.mask||entry.board);
    if(Array.isArray(shape)&&shape.length===rows&&shape.every(function(row){return Array.isArray(row)&&row.length===columns;})){
      var x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;
      shape.forEach(function(row,y){row.forEach(function(value,x){if(value>0){x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);}});});
      if(Number.isFinite(x0)){minCol=x0;maxCol=x1;minRow=y0;maxRow=y1;}
    }
    var minBoardX = originX + minCol * pitch - size / 2, maxBoardX = originX + maxCol * pitch + size / 2;
    var minBoardY = originY + minRow * pitch - size / 2, maxBoardY = originY + maxRow * pitch + size / 2;
    var points = [[minBoardX,minBoardY],[minBoardX,maxBoardY],[maxBoardX,minBoardY],[maxBoardX,maxBoardY]].map(function (p) {
      return visualPoint(r, layer, p[0], p[1]);
    });
    var rect = r.canvas.getBoundingClientRect(), cx = rect.left + rect.width / 2, cy = rect.top + rect.height / 2;
    var minX = Math.min.apply(null, points.map(function (p) { return p.x; }));
    var maxX = Math.max.apply(null, points.map(function (p) { return p.x; }));
    var minY = Math.min.apply(null, points.map(function (p) { return p.y; }));
    var maxY = Math.max.apply(null, points.map(function (p) { return p.y; }));
    // Fit in both directions: a small configured board may use the available
    // area instead of being permanently capped at its original layer scale.
    var factors = [];
    if (minX < cx) factors.push((cx - area.left) / (cx - minX));
    if (maxX > cx) factors.push((area.left + area.width - cx) / (maxX - cx));
    if (minY < cy) factors.push((cy - area.top) / (cy - minY));
    if (maxY > cy) factors.push((area.top + area.height - cy) / (maxY - cy));
    var scale = Math.min.apply(null, factors);
    if (!Number.isFinite(scale) || scale <= 0) return false;
    layer.scale = baseScale * scale;
    fittedScale = layer.scale; fittedRuntime = r;
    r.redraw = true;
    return true;
  }
  function install() {
    if(window.oneConnectThemeSwitchCandidate&&window.oneConnectThemeSwitchCandidate.install)window.oneConnectThemeSwitchCandidate.install();
    // The native portrait event reapplies the Game layer scale after the
    // initial fit. Preserve the computed scale at that exact action boundary.
    var action=window.cr&&window.cr.action&&window.cr.action.prototype;
    if(action&&typeof action.run_system==='function'){
      var prior=action.run_system;action.run_system=function(){var result=prior.apply(this,arguments);if(this.sid===913642290917496&&this.runtime===fittedRuntime&&boardLayer&&fittedScale!==null&&this.runtime.running_layout&&this.runtime.running_layout.name==='game'){boardLayer.scale=fittedScale;this.runtime.redraw=true;}return result;};
    }
    window.addEventListener('storage',function(e){if(e.key===themeKey||e.key===null){themeExternalRevision++;themeLoaded=false;}});
    // Visual layers never receive input: the native Construct controls below
    // remain the owner of hit testing, inventory and tutorial completion.
    ['reserved','hammer','shuffle','hint'].forEach(function(id){
      var box=document.createElement('div');box.setAttribute('aria-hidden','true');
      box.style.cssText='display:none;position:fixed;z-index:20;pointer-events:none;background:url("images/ui-tool-slot.png") center/100% 100% no-repeat';
      var icon=document.createElement('img'), count=document.createElement('span');
      icon.style.cssText='position:absolute;left:8%;top:10%;width:54%;height:80%;object-fit:contain';
      count.style.cssText='position:absolute;left:65%;top:25%;color:white;font:bold clamp(12px,3.5vw,20px) sans-serif';
      if(id==='shuffle')icon.src='images/gamebuttons-sheet0.webp';
      if(id==='hint')icon.src='images/gamebuttons-sheet1.webp';
      if(id==='hammer')icon.src='images/ui-lock.png';
      box.append(icon,count);document.body.appendChild(box);toolArt.push({id:id,box:box,icon:icon,count:count});
    });
    // Only the artwork moves. The next four-second interval starts after all
    // three jumps, rather than overlapping the currently playing animation.
    var jumpTimer=null,jumpAnimation=null;
    function scheduleJump(){if(typeof window.setTimeout==='function')jumpTimer=window.setTimeout(jumpTool,4000);}
    function resetJump(){if(jumpTimer!==null&&typeof window.clearTimeout==='function')window.clearTimeout(jumpTimer);jumpTimer=null;if(jumpAnimation){var a=jumpAnimation;jumpAnimation=null;a.onfinish=null;a.oncancel=null;if(typeof a.cancel==='function')a.cancel();}scheduleJump();}
    function jumpTool(){
      jumpTimer=null;
      var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),guides=['oneConnectTutorial','oneConnectSecondGuide','oneConnectThirdGuide','oneConnectFifthGuide','oneConnectSeventhGuide','oneConnectTenthGuide'];
      if(Date.now()<busyUntil||!r||!Array.isArray(r.all_global_vars)||!r.running_layout||r.running_layout.name!=='game'||getVariable(r,'pause')||roundEnded||autoShuffling||document.hidden||(window.oneConnectThemeSwitchCandidate&&window.oneConnectThemeSwitchCandidate.isAnimating&&window.oneConnectThemeSwitchCandidate.isAnimating())||(window.oneConnectGravityRuntime&&window.oneConnectGravityRuntime.state().moving)||(window.oneConnectShuffleMotionCandidate&&window.oneConnectShuffleMotionCandidate.state().moving)||guides.some(function(n){var g=window[n];return g&&g.state&&g.state().active;})||['oc-tool-reward','oc-home-settings','oc-how-to-play'].some(function(id){var el=document.getElementById(id);return el&&!el.hidden;})||(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)){scheduleJump();return;}
      var hammer=document.getElementById('oc-hammer'),level=getVariable(r,'level');
      var choices=[placeholder&&{box:placeholder,icon:placeholder.querySelector('img')},Number.isInteger(level)&&level>=7&&hammer&&{box:hammer,icon:hammer.querySelector('img')},toolArt[2],toolArt[3]].filter(function(item){return item&&item.box&&item.box.style.display!=='none'&&item.icon&&typeof item.icon.animate==='function';});
      if(!choices.length){scheduleJump();return;}
      var choice=choices[Math.floor(Math.random()*choices.length)],animation;
      try{animation=choice.icon.animate([{transform:'translateY(0)',easing:'cubic-bezier(0,0,.4,1)'},{transform:'translateY(-18%)',offset:.5,easing:'cubic-bezier(.6,0,1,1)'},{transform:'translateY(0)'}],{duration:420,iterations:3});}catch(_){scheduleJump();return;}
      jumpAnimation=animation;var finished=false;function complete(){if(finished)return;finished=true;if(jumpAnimation===animation)jumpAnimation=null;scheduleJump();}
      animation.onfinish=complete;animation.oncancel=complete;
    }
    scheduleJump();
    notice = document.createElement('div');
    notice.setAttribute('role','status'); notice.setAttribute('aria-live','polite');
    notice.style.cssText = 'display:none;position:fixed;z-index:23;left:50%;bottom:15%;transform:translateX(-50%);padding:8px 14px;border-radius:16px;background:rgba(5,20,54,.9);color:white;font:600 14px sans-serif;pointer-events:none';
    document.body.appendChild(notice);
    function showNotice(message) {
      notice.textContent=message; notice.style.display='block';
      var r=window.cr_getC2Runtime && window.cr_getC2Runtime(), rect=r && r.canvas && r.canvas.getBoundingClientRect();
      if (rect) { notice.style.left=(rect.left+rect.width/2)+'px'; notice.style.top=Math.max(rect.top+8,placeholder.getBoundingClientRect().top-42)+'px'; notice.style.bottom='auto'; }
      if (noticeTimer) clearTimeout(noticeTimer);
      var motion=window.oneConnectTutorialMotion,quiet=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if(motion)motion.open(notice);
      noticeTimer=setTimeout(function(){noticeTimer=null;if(motion&&!quiet)motion.close(notice,{durationMs:160},function(){notice.style.display='none';});else notice.style.display='none';},motion&&!quiet?1640:1800);
    }
    placeholder = document.createElement('button');
    placeholder.type = 'button';
    placeholder.setAttribute('aria-label', 'Change tile theme (local candidate)');
    placeholder.title = 'Change tile theme';
    placeholder.style.cssText = 'display:none;position:fixed;z-index:21;box-sizing:border-box;align-items:center;justify-content:center;border:0;background:transparent;touch-action:manipulation';
    var icon = document.createElement('img');
    icon.src = 'images/replace-theme-icon.png'; icon.alt = '';
    icon.style.cssText = 'position:absolute;left:8%;top:10%;width:54%;height:80%;object-fit:contain';
    placeholder.appendChild(icon);
    var themeCount=document.createElement('span');themeCount.style.cssText='position:absolute;left:65%;top:25%;color:white;font:bold clamp(12px,3.5vw,20px) sans-serif';placeholder.appendChild(themeCount);
    if(window.oneConnectToolPressCandidate)window.oneConnectToolPressCandidate.install(function(){
      var hammer=document.getElementById('oc-hammer');return [{box:placeholder,icon:icon},hammer&&{box:hammer,icon:hammer.querySelector('img')},toolArt[2],toolArt[3]];
    },function(){var r=window.cr_getC2Runtime&&window.cr_getC2Runtime();if(!r||!r.running_layout||r.running_layout.name!=='game'||!Array.isArray(r.all_global_vars)||getVariable(r,'pause')||roundEnded||autoShuffling||(window.oneConnectThemeSwitchCandidate&&window.oneConnectThemeSwitchCandidate.isAnimating&&window.oneConnectThemeSwitchCandidate.isAnimating())||(window.oneConnectGravityRuntime&&window.oneConnectGravityRuntime.state().moving)||(window.oneConnectShuffleMotionCandidate&&window.oneConnectShuffleMotionCandidate.state().moving))return false;
      return !['oc-tool-reward','oc-home-settings','oc-star-dialog','oc-how-to-play'].some(function(id){var el=document.getElementById(id);return el&&!el.hidden;});});
    ['pointerdown','pointerup','touchstart','touchend','mousedown','mouseup','click'].forEach(function(name){placeholder.addEventListener(name,function(e){e.stopPropagation();});});
    placeholder.addEventListener('click', function () {
      var r = window.cr_getC2Runtime && window.cr_getC2Runtime();
      if(!r||!r.running_layout||r.running_layout.name!=='game'||!Array.isArray(r.all_global_vars)||getVariable(r,'pause')||roundEnded)return;
      var guides = ['oneConnectTutorial','oneConnectSecondGuide','oneConnectThirdGuide','oneConnectFifthGuide','oneConnectSeventhGuide','oneConnectTenthGuide'];
      if (autoShuffling || (window.oneConnectThemeSwitchCandidate&&window.oneConnectThemeSwitchCandidate.isAnimating&&window.oneConnectThemeSwitchCandidate.isAnimating()) || (window.oneConnectGravityRuntime && window.oneConnectGravityRuntime.state().moving) || (window.oneConnectShuffleMotionCandidate && window.oneConnectShuffleMotionCandidate.state().moving) || Date.now() < busyUntil || guides.some(function(name){var g=window[name];return g && typeof g.state==='function' && g.state().active;})) { showNotice('Please wait'); return; }
      if(themeStock()<=0){if(window.oneConnectToolRewardCandidate)window.oneConnectToolRewardCandidate.open('theme');return;}
      var current = r && getVariable(r, 'theme');
      var actions = window.cr && cr.plugins_ && cr.plugins_.Sprite && cr.plugins_.Sprite.prototype.acts;
      if (!Number.isInteger(current) || current < 0 || current > 3 || !window.oneConnectThemeSwitchCandidate) { showNotice('Theme change unavailable'); return; }
      var target=(current+1)%4;
      function switched(result){
        if(result.status==='switched'){
          saveThemeStock(themeStock()-1);
          if(window.oneConnectHost)window.oneConnectHost.emit('candidate.theme_switch',{theme:result.theme,tiles:result.tiles});
          if(window.oneConnectRoundSave)window.oneConnectRoundSave.capture();
        }else if(result.status!=='cancelled')showNotice(result.status==='busy'?'Please wait':'Theme change unavailable');
      }
      var result=window.oneConnectThemeSwitchCandidate.animateSwitch(r,target,actions,switched,target===3?0:null);
      if(result.status!=='started')switched(result);
    });
    window.addEventListener('oneconnect:event', function(e){
      var type=e.detail && e.detail.type;
      if(type==='game.board_configured'||type==='game.round_ready'||type==='game.level_win'||type==='game.level_fail'||type==='screen.SCREEN_BONUS')resetJump();
      if(type==='game.level_win'||type==='game.level_fail'||type==='screen.SCREEN_BONUS')roundEnded=true;
      if(type==='game.board_configured'||type==='game.round_ready')roundEnded=false;
      if (type === 'game.auto_shuffle_start') autoShuffling = true;
      if (type === 'game.auto_shuffle_complete' || type === 'game.auto_shuffle_exhausted' || type === 'game.auto_shuffle_expired' || type === 'game.level_fail' || type === 'game.level_win' || type === 'game.board_configured') autoShuffling = false;
      if (type === 'game.match' || type === 'game.shuffle' || type === 'game.hammer' || type === 'game.auto_shuffle_complete') busyUntil = Date.now() + 1000;
    });
    document.body.appendChild(placeholder);
    requestAnimationFrame(update);
  }
  function update() {
    var r = window.cr_getC2Runtime && window.cr_getC2Runtime();
    var show = r && r.running_layout && r.running_layout.name === 'game';
    if (!show) {
      if(window.oneConnectNativePauseMotion)window.oneConnectNativePauseMotion.tick(r,false);
      if(window.oneConnectBoardProgressCandidate)window.oneConnectBoardProgressCandidate.update(null,null);
      autoShuffling = false; busyUntil = 0;
      if (notice) setStyleIfChanged(notice,'display','none');
      if (boardLayer && baseScale !== null) boardLayer.scale = baseScale;
      if (r && window.oneConnectLayoutAdapter) window.oneConnectLayoutAdapter.restore(r);
      boardLayer = null; baseScale = null; fittedScale = null; fittedRuntime = null; frameKey = '';
      if (placeholder) setStyleIfChanged(placeholder,'display','none');
      toolArt.forEach(function(item){setStyleIfChanged(item.box,'display','none');});
      requestAnimationFrame(update); return;
    }
    var rect = r.canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) { requestAnimationFrame(update); return; }
    if (rect.width >= rect.height) {
      if(window.oneConnectNativePauseMotion)window.oneConnectNativePauseMotion.tick(r,false);
      if(window.oneConnectBoardProgressCandidate)window.oneConnectBoardProgressCandidate.update(null,null);
      if (boardLayer && baseScale !== null) { boardLayer.scale = baseScale; r.redraw = true; }
      boardLayer = null; baseScale = null; fittedScale = null; fittedRuntime = null; frameKey = '';
      window.oneConnectLayoutAdapter.restore(r);
      if (placeholder) setStyleIfChanged(placeholder,'display','none');
      toolArt.forEach(function(item){setStyleIfChanged(item.box,'display','none');});
      var landscapeHammer = document.getElementById('oc-hammer');
      if (landscapeHammer) {
        setStyleIfChanged(landscapeHammer,'left','auto'); setStyleIfChanged(landscapeHammer,'right','8px');
        setStyleIfChanged(landscapeHammer,'top','auto'); setStyleIfChanged(landscapeHammer,'bottom','8px');
        setStyleIfChanged(landscapeHammer,'width','76px'); setStyleIfChanged(landscapeHammer,'height','56px');
      }
      requestAnimationFrame(update); return;
    }
    var rows = getVariable(r, 'COLUMNS_COUNT'), cols = getVariable(r, 'ROWS_COUNT');
    if (!rows || !cols) { requestAnimationFrame(update); return; }
    var safe=layoutOptions.safeArea, nextGeometryKey=[rect.left,rect.top,rect.width,rect.height,r.canvas.width,r.canvas.height,r.isRetina,r.devicePixelRatio,rows,cols,layoutOptions.bannerHeight,safe.top,safe.right,safe.bottom,safe.left].join(':');
    if(!geometryCache||geometryKey!==nextGeometryKey){
      var nextLayout;
      try {
        nextLayout = window.oneConnectLayoutGeometry.calculate({width: rect.width, height: rect.height, rows: rows, cols: cols,
          bannerHeight: layoutOptions.bannerHeight, safeArea: layoutOptions.safeArea});
      } catch (_) { requestAnimationFrame(update); return; }
      ['header', 'progress', 'board', 'banner'].forEach(function (name) { nextLayout[name].left += rect.left; nextLayout[name].top += rect.top; });
      if (nextLayout.fitArea) { nextLayout.fitArea.left += rect.left; nextLayout.fitArea.top += rect.top; }
      nextLayout.tools.forEach(function (slot) { slot.left += rect.left; slot.top += rect.top; });
      geometryCache=nextLayout;geometryKey=nextGeometryKey;
    }
    var layout=geometryCache;
    var key = [getVariable(r, 'level'), rect.width, rect.height, r.canvas.width, r.canvas.height, r.isRetina, r.devicePixelRatio, rows, cols].join(':');
    var currentTiles = r.types.t5 && r.types.t5.instances;
    var currentLayer = currentTiles && currentTiles.length && currentTiles[0].layer;
    if ((key !== frameKey || (currentLayer && currentLayer !== boardLayer)) && fitBoard(r, layout.fitArea || layout.board)) frameKey = key;
    window.oneConnectLayoutAdapter.moveHud(r, layout.header);
    window.oneConnectLayoutAdapter.moveTools(r, layout);
    var pauseLaidOut=window.oneConnectLayoutAdapter.movePause(r);
    if(window.oneConnectNativePauseMotion)window.oneConnectNativePauseMotion.tick(r,pauseLaidOut);
    if(window.oneConnectBoardProgressCandidate)window.oneConnectBoardProgressCandidate.update(r,layout.progress);
    var paused=!!getVariable(r,'pause')||roundEnded, level=getVariable(r,'level');
    window.oneConnectLayoutAdapter.setToolsHidden(r,paused);
    toolArt.forEach(function(item,index){
      var area=layout.tools[index], box=item.box;
      setStyleIfChanged(box,'left',area.left+'px');setStyleIfChanged(box,'top',area.top+'px');setStyleIfChanged(box,'width',area.width+'px');setStyleIfChanged(box,'height',area.height+'px');
      setStyleIfChanged(box,'display',paused?'none':'block');
      if(item.id==='hammer')setStyleIfChanged(item.icon,'display',Number.isInteger(level)&&level<7?'block':'none');
      if(item.id==='reserved')setStyleIfChanged(item.icon,'display','none');
      if(item.id==='shuffle'||item.id==='hint'){
        var uid=item.id==='shuffle'?2:46,role=item.id==='shuffle'?3:4,fonts=r.types.t25 && r.types.t25.instances || [];
        var counter=fonts.find(function(obj){return obj.instance_vars&&obj.instance_vars[0]===role;})||fonts.find(function(obj){return obj.uid===uid&&(!obj.instance_vars||obj.instance_vars.length===0||obj.instance_vars[0]===role);});
        setTextIfChanged(item.count,counter && counter.text!==undefined?counter.text:'');
      }
    });
    var hammer = document.getElementById('oc-hammer'), slot = layout.tools[1];
    if (hammer) {
      setStyleIfChanged(hammer,'left',slot.left + 'px'); setStyleIfChanged(hammer,'top',slot.top + 'px');
      setStyleIfChanged(hammer,'right','auto'); setStyleIfChanged(hammer,'bottom','auto');
      setStyleIfChanged(hammer,'width',slot.width + 'px'); setStyleIfChanged(hammer,'height',slot.height + 'px');
    }
    slot = layout.tools[0]; setStyleIfChanged(placeholder,'left',slot.left + 'px'); setStyleIfChanged(placeholder,'top',slot.top + 'px');
    setTextIfChanged(placeholder.lastElementChild,themeStock());
    setStyleIfChanged(placeholder,'width',slot.width + 'px'); setStyleIfChanged(placeholder,'height',slot.height + 'px');
    setStyleIfChanged(placeholder,'display',paused ? 'none' : 'flex');
    requestAnimationFrame(update);
  }
  window.oneConnectLayoutCandidate = {install: install, configure: configure};
})();
