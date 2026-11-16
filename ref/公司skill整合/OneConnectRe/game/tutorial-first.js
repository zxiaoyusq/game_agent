(function () {
  'use strict';
  var pairs = [[11,13],[8,14],[10,4],[3,7],[1,16]];
  var reference = [0,5,0,8,3,0,7,8,2,6,3,1,0,1,2,4,5,0,0,7,6,4,0,0,0];
  var key = 'oneconnect.tutorial1.v1', active = false, step = 0, installed = false, panel, skipButton, cursor, promptLabel, rings = [], dims = [], demoRemaining = 0, demoAttempted = false, lastFrame = Date.now();
  function done() { try { return window.localStorage.getItem(key) === 'done'; } catch (_) { return false; } }
  function complete() { active = false; try { window.localStorage.setItem(key, 'done'); } catch (_) {} if (window.oneConnectHost) window.oneConnectHost.emit('tutorial.complete', {level:1}); }
  function matchesReference() {
    var rows = window.oneConnectLevels && window.oneConnectLevels.levels;
    var entry = Array.isArray(rows) && rows.find(function (x) { return x.level === 1; });
    if (!entry || !Array.isArray(entry.board) || entry.board.length !== 6 || entry.board.some(function(r){return !Array.isArray(r) || r.length !== 12;})) return false;
    for (var y=0;y<12;y++) for (var x=0;x<6;x++) {
      var expected = y>=4 && y<9 && x>=1 ? reference[(y-4)*5+(x-1)] : 0;
      if (entry.board[x][11-y] !== expected) return false;
    }
    return true;
  }
  function resumeStep(board) {
    if (!Array.isArray(board) || board.length!==6 || board.some(function(r){return !Array.isArray(r)||r.length!==12;})) return -1;
    for (var n=0;n<pairs.length;n++) {
      var removed=[];for(var i=0;i<n;i++)removed=removed.concat(pairs[i]);
      var valid=true;
      for(var y=0;y<12&&valid;y++)for(var x=0;x<6;x++){
        var idx=(y-4)*5+(x-1),expected=y>=4&&y<9&&x>=1?(removed.indexOf(idx)>=0?0:reference[idx]):0;
        if(board[x][11-y]!==expected){valid=false;break;}
      }
      if(valid)return n;
    }
    return -1;
  }
  function needsResumeValidation(){return (!window.oneConnectTutorialConfig || window.oneConnectTutorialConfig.enabled!==false) && !done() && matchesReference();}
  function current() { return demoRemaining > 0 ? [15,21] : (pairs[step] || []); }
  function slot(tile) {
    var row = Math.round((tile.y-133)/101), col = Math.round((tile.x-89)/101);
    var x = row-1, y = 7-col;
    return x>=0 && x<5 && y>=0 && y<5 ? y*5+x : -1;
  }
  function setupUI() {
    panel=document.createElement('div'); panel.id='oc-tutorial'; panel.style.cssText='display:none;position:fixed;inset:0;z-index:30;pointer-events:none';
    var prompt=document.createElement('div');prompt.style.cssText='position:absolute;top:18%;left:50%;transform:translateX(-50%);padding:8px 18px;border-radius:20px;background:#183b82;color:white;font:bold 18px sans-serif;box-shadow:0 2px 8px #081331;white-space:nowrap';prompt.textContent='Tap matching tiles';prompt.id='oc-tutorial-prompt';promptLabel=prompt;panel.appendChild(prompt);
    for(var j=0;j<16;j++){var shade=document.createElement('div');shade.setAttribute('data-tutorial-dim','');shade.style.cssText='display:none;position:absolute;box-sizing:border-box;background:rgba(5,12,35,.64);border-radius:12px;transform:translate(-50%,-50%);pointer-events:none';panel.appendChild(shade);dims.push(shade)}
    var skip=document.createElement('button');skip.id='oc-tutorial-skip';skip.textContent='Skip';skip.style.cssText='position:absolute;right:4%;bottom:8%;padding:8px 18px;border:2px solid #90cfff;border-radius:18px;background:#20549d;color:white;font:bold 16px sans-serif;pointer-events:auto';skip.onclick=complete;skipButton=skip;panel.appendChild(skip);
    cursor=document.createElement('div');cursor.textContent='☝';cursor.style.cssText='position:absolute;pointer-events:none;font-size:42px;filter:drop-shadow(0 2px 3px #11244a);transform:translate(-15%,-15%);transition:left .45s ease-in-out,top .45s ease-in-out';panel.appendChild(cursor);
    for(var i=0;i<2;i++){var ring=document.createElement('div');ring.style.cssText='display:none;position:absolute;box-sizing:border-box;border:4px solid #ffde58;border-radius:16px;box-shadow:0 0 14px #fff391;transform:translate(-50%,-50%);pointer-events:none';panel.appendChild(ring);rings.push(ring)}document.body.appendChild(panel);
  }
  function draw() {
    var r=window.cr_getC2Runtime && window.cr_getC2Runtime(), pause=r&&r.all_global_vars&&r.all_global_vars.find(function(v){return v.name==='pause'});
    var visible=active && r && r.running_layout && r.running_layout.name==='game' && !(pause && pause.data);
    var now=Date.now(),dt=Math.min(Math.max(now-lastFrame,0),100);lastFrame=now;if(visible && !document.hidden && demoRemaining>0 && demoAttempted)demoRemaining=Math.max(0,demoRemaining-dt);if(promptLabel)promptLabel.textContent=demoRemaining>0?'These tiles cannot connect yet':'Tap matching tiles';if(panel)panel.style.display=visible?'block':'none';if(skipButton)skipButton.style.display=step>=4?'block':'none';
    if(visible){var rect=r.canvas.getBoundingClientRect(),targets=current(),tiles=r.types.t5.instances,nonTargets=tiles.filter(function(t){return targets.indexOf(slot(t))<0});for(var k=0;k<dims.length;k++){var dim=dims[k],dtile=nonTargets[k];if(!dtile){dim.style.display='none';continue}var dx=dtile.layer.layerToCanvas(dtile.x,dtile.y,true),dy=dtile.layer.layerToCanvas(dtile.x,dtile.y,false),du=Math.hypot(dtile.layer.layerToCanvas(dtile.x+101,dtile.y,true)-dx,dtile.layer.layerToCanvas(dtile.x+101,dtile.y,false)-dy);dim.style.left=(rect.left+dx)+'px';dim.style.top=(rect.top+dy)+'px';dim.style.width=(du*.98)+'px';dim.style.height=(du*.98)+'px';dim.style.display='block'}for(var i=0;i<2;i++){var tile=tiles.find(function(t){return slot(t)===targets[i]});var el=rings[i];if(!tile){el.style.display='none';continue}var x=tile.layer.layerToCanvas(tile.x,tile.y,true),y=tile.layer.layerToCanvas(tile.x,tile.y,false),unit=Math.hypot(tile.layer.layerToCanvas(tile.x+101,tile.y,true)-x,tile.layer.layerToCanvas(tile.x+101,tile.y,false)-y);el.style.left=(rect.left+x)+'px';el.style.top=(rect.top+y)+'px';el.style.width=(unit*.98)+'px';el.style.height=(unit*.98)+'px';el.style.display='block'}var target=tiles.find(function(t){return slot(t)===targets[Math.floor(Date.now()/900)%2]});if(target && demoRemaining<=0){cursor.style.left=(rect.left+target.layer.layerToCanvas(target.x,target.y,true))+'px';cursor.style.top=(rect.top+target.layer.layerToCanvas(target.x,target.y,false))+'px';cursor.style.display='block'}else cursor.style.display='none'}
    requestAnimationFrame(draw);
  }
  function install() {
    if(installed)return;installed=true;setupUI();requestAnimationFrame(draw);
    var touch=cr.plugins_.Touch.prototype.cnds,oldTouch=touch.OnTouchObject;
    touch.OnTouchObject=function(type){var ok=oldTouch.apply(this,arguments);if(!ok || !active || !type)return ok;if(type.name==='t26')return false;if(type.name!=='t5')return ok;var picked=type.getCurrentSol().getObjects();return picked.some(function(t){return current().indexOf(slot(t))>=0})};
    var oldAction=cr.action.prototype.run_system;
    cr.action.prototype.run_system=function(){if(active && this.sid===367702696840255)return;return oldAction.apply(this,arguments)};
    window.addEventListener('oneconnect:event',function(e){var event=e&&e.detail;if(!event)return;
      if(event.type==='game.board_configured' && event.detail.level===1 && needsResumeValidation()){active=true;step=Number.isInteger(event.detail.tutorialStep)?event.detail.tutorialStep:0;demoRemaining=step===3?1800:0;demoAttempted=false;window.oneConnectHost.emit('tutorial.start',{level:1})}
      else if(event.type==='game.match' && active){step++;if(step===3)demoRemaining=1800;demoAttempted=false;if(step>=pairs.length)complete()}
      else if(event.type==='candidate.invalid_link' && active && demoRemaining>0){demoAttempted=true;}
      else if(event.type==='game.level_fail')active=false;
    });
  }
  window.oneConnectTutorial={install:install,resumeStep:resumeStep,needsResumeValidation:needsResumeValidation,state:function(){return {active:active,step:step,demonstrating:demoRemaining>0,targets:current().slice()}}};
}());
