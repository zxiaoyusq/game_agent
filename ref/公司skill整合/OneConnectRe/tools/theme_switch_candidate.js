/* Candidate theme switching; the layout adapter owns inventory and input.
 * No competitor unlock conditions or persistence rules are assumed here. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.oneConnectThemeSwitchCandidate = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  var active=null,installed=false;
  function switchTheme(runtime, target, actions) {
    if (!runtime || !runtime.running_layout || runtime.running_layout.name !== 'game') return {status:'unavailable'};
    if (!Number.isInteger(target) || target < 0 || target > 3) return {status:'invalid_theme'};
    var vars = runtime.all_global_vars || [], theme = vars.find(function (v) { return v.name === 'theme'; });
    var pause = vars.find(function (v) { return v.name === 'pause'; });
    var tileType = runtime.types && runtime.types.t5, tiles = tileType && tileType.instances;
    if (!theme || !Array.isArray(tiles) || !tiles.length || !actions || typeof actions.SetAnim !== 'function') return {status:'unavailable'};
    var gravity = globalThis.oneConnectGravityRuntime, hammer = globalThis.oneConnectHammer;
    if ((pause && pause.data) || (gravity && gravity.state().moving) || (hammer && hammer.state().busy) || (globalThis.oneConnectShuffleMotionCandidate && globalThis.oneConnectShuffleMotionCandidate.state().moving) ||
        tiles.some(function (tile) { return tile.inAnimTrigger || (tile.instance_vars && tile.instance_vars[3]); })) return {status:'busy'};
    var requested = 't' + target;
    var previous;
    try {
      previous = tiles.map(function (tile) {
        if (!tile.cur_animation || !tile.getAnimationByName) throw new Error('tile animation unavailable');
        var next = tile.getAnimationByName(requested);
        if (!next || !next.frames || tile.cur_frame < 0 || tile.cur_frame >= next.frames.length) throw new Error('theme lacks tile frame');
        return {tile:tile, name:tile.cur_animation.name, frame:tile.cur_frame};
      });
    } catch (error) { return {status:'unavailable', message:String(error)}; }
    var oldTheme = theme.data;
    if (oldTheme === target && previous.every(function (item) { return item.name.toLowerCase() === requested; })) {
      return {status:'unchanged', theme:target};
    }
    try {
      previous.forEach(function (item) { actions.SetAnim.call(item.tile, requested, 0); });
      if (previous.some(function (item) {
        return !item.tile.cur_animation || item.tile.cur_animation.name.toLowerCase() !== requested || item.tile.cur_frame !== item.frame;
      })) throw new Error('theme switch did not preserve every tile frame');
      theme.data = target;
      if (globalThis.oneConnectBoard && typeof globalThis.oneConnectBoard.markCandidateTheme === 'function') {
        globalThis.oneConnectBoard.markCandidateTheme();
      }
      runtime.redraw = true;
      return {status:'switched', theme:target, tiles:previous.length};
    } catch (error) {
      var rollbackFailed = false;
      previous.forEach(function (item) {
        try {
          actions.SetAnim.call(item.tile, item.name, 0);
          if (!item.tile.cur_animation || item.tile.cur_animation.name !== item.name || item.tile.cur_frame !== item.frame) rollbackFailed = true;
        } catch (_) { rollbackFailed = true; }
      });
      theme.data = oldTheme;
      return {status:rollbackFailed?'rollback_failed':'error', message:String(error)};
    }
  }
  function install(){
    if(installed)return;var touch=globalThis.cr&&globalThis.cr.plugins_&&globalThis.cr.plugins_.Touch&&globalThis.cr.plugins_.Touch.prototype.cnds;
    if(!touch||typeof touch.OnTouchObject!=='function')return;
    var original=touch.OnTouchObject;touch.OnTouchObject=function(type){var result=original.apply(this,arguments);return result&&active&&type&&(type.name==='t5'||type.name==='t26')?false:result;};
    if(globalThis.document&&typeof globalThis.document.addEventListener==='function')globalThis.document.addEventListener('visibilitychange',function(){if(globalThis.document.hidden&&active&&active.cancel)active.cancel();});
    if(typeof globalThis.addEventListener==='function')globalThis.addEventListener('oneconnect:event',function(e){var type=e.detail&&e.detail.type;if(active&&active.cancel&&['game.level_fail','game.level_win','game.board_configured','game.round_ready','screen.SCREEN_HOME'].indexOf(type)>=0)active.cancel();});
    installed=true;
  }
  function animateSwitch(runtime,target,actions,done,fallback){
    if(active)return {status:'busy'};
    if(!installed)return {status:'unavailable'};
    var tiles=runtime&&runtime.types&&runtime.types.t5&&runtime.types.t5.instances;
    if(!runtime||!runtime.running_layout||runtime.running_layout.name!=='game'||!Array.isArray(tiles)||!tiles.length||typeof globalThis.requestAnimationFrame!=='function')return {status:'unavailable'};
    var saved=tiles.map(function(tile){return {tile:tile,width:tile.width,height:tile.height};});
    if(saved.some(function(x){return !Number.isFinite(x.width)||!Number.isFinite(x.height)||typeof x.tile.set_bbox_changed!=='function';}))return {status:'unavailable'};
    var token={runtime:runtime,saved:saved,start:null,result:null},duration=600;active=token;
    function finish(result){if(active!==token)return;saved.forEach(function(x){x.tile.width=x.width;x.tile.height=x.height;x.tile.set_bbox_changed();});runtime.redraw=true;active=null;if(typeof done==='function')done(result);}
    token.cancel=function(){finish(token.result||{status:'cancelled'});};
    function tick(now){
      if(active!==token)return;
      var pause=(runtime.all_global_vars||[]).find(function(v){return v.name==='pause';}),live=runtime.types&&runtime.types.t5&&runtime.types.t5.instances;
      if(!runtime.running_layout||runtime.running_layout.name!=='game'||(pause&&pause.data)||(globalThis.document&&globalThis.document.hidden)||!Array.isArray(live)||live.length!==saved.length||saved.some(function(x){return live.indexOf(x.tile)<0;})){finish(token.result||{status:'cancelled'});return;}
      if(token.start===null)token.start=now;var p=Math.min(1,Math.max(0,(now-token.start)/duration));
      if(p>=.5&&!token.result){token.result=switchTheme(runtime,target,actions);if(token.result.status==='unavailable'&&Number.isInteger(fallback))token.result=switchTheme(runtime,fallback,actions);if(token.result.status!=='switched'){finish(token.result);return;}}
      var scale=p<.5?1-p*2:(p-.5)*2;scale=Math.max(.001,scale);
      saved.forEach(function(x){x.tile.width=x.width*scale;x.tile.height=x.height*scale;x.tile.set_bbox_changed();});runtime.redraw=true;
      if(p>=1)finish(token.result);else globalThis.requestAnimationFrame(tick);
    }
    globalThis.requestAnimationFrame(tick);return {status:'started'};
  }
  return {switchTheme:switchTheme,animateSwitch:animateSwitch,install:install,isAnimating:function(){return !!active;}};
});
