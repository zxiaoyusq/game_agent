(function () {
  'use strict';
  var key='oneconnect.tutorial3.v1',active=false,installed=false,overlay,highlight;
  function done(){try{return localStorage.getItem(key)==='done';}catch(_){return false;}}
  function finish(){if(!active)return;active=false;overlay.style.display='none';try{localStorage.setItem(key,'done');}catch(_){}if(window.oneConnectHost)oneConnectHost.emit('tutorial.complete',{level:3});}
  function frame(){
    var r=window.cr_getC2Runtime&&window.cr_getC2Runtime();
    var pause=r&&r.all_global_vars.find(function(v){return v.name==='pause';});
    if(active&&r&&r.running_layout&&r.running_layout.name==='game'&&!(pause&&pause.data)){
      var text=r.types.t25.instances.find(function(t){return t.instance_vars&&t.instance_vars[0]===1;}),clock=r.types.t24.instances.find(function(t){return t.cur_frame===1;});
      if(text&&clock){var rect=r.canvas.getBoundingClientRect(),layer=text.layer,points=[[clock.x-34,clock.y-35],[text.x+Math.abs(text.width)+5,text.y-35],[clock.x-34,clock.y+35],[text.x+Math.abs(text.width)+5,text.y+35]].map(function(p){return [rect.left+layer.layerToCanvas(p[0],p[1],true),rect.top+layer.layerToCanvas(p[0],p[1],false)];}),xs=points.map(function(p){return p[0];}),ys=points.map(function(p){return p[1];});highlight.style.left=Math.min.apply(null,xs)+'px';highlight.style.top=Math.min.apply(null,ys)+'px';highlight.style.width=(Math.max.apply(null,xs)-Math.min.apply(null,xs))+'px';highlight.style.height=(Math.max.apply(null,ys)-Math.min.apply(null,ys))+'px';}
      overlay.style.display='block';
    }else if(overlay)overlay.style.display='none';
    requestAnimationFrame(frame);
  }
  function install(){if(installed)return;installed=true;
    overlay=document.createElement('div');overlay.id='oc-third-guide';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-label','Time limit tutorial');overlay.style.cssText='display:none;position:fixed;inset:0;z-index:32;overflow:hidden;cursor:pointer;touch-action:manipulation';
    highlight=document.createElement('div');highlight.style.cssText='position:absolute;border:3px solid #ffe46e;border-radius:18px;box-shadow:0 0 0 200vmax rgba(4,10,30,.72),0 0 18px #ffe47a;pointer-events:none;box-sizing:border-box';overlay.appendChild(highlight);
    var label=document.createElement('div');label.textContent='Clear all tiles before time runs out!';label.style.cssText='position:absolute;top:23%;left:8%;width:84%;text-align:center;color:white;font:bold clamp(19px,5vw,34px) sans-serif;text-shadow:0 3px 5px #10182f;pointer-events:none';overlay.appendChild(label);
    var hint=document.createElement('div');hint.textContent='Tap to continue';hint.style.cssText='position:absolute;top:33%;left:0;width:100%;text-align:center;color:#dce9ff;font:bold clamp(14px,3vw,20px) sans-serif;pointer-events:none';overlay.appendChild(hint);overlay.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();finish();});document.body.appendChild(overlay);
    var previous=cr.action.prototype.run_system;cr.action.prototype.run_system=function(){if(active&&this.sid===367702696840255){var v=this.runtime.all_global_vars.find(function(v){return v.name==='level';});if(v&&v.data===3)return;}return previous.apply(this,arguments)};
    window.addEventListener('oneconnect:event',function(e){var x=e.detail;if(!x)return;if(x.type==='game.board_configured'&&x.detail.level===3&&!done()){active=true;window.oneConnectHost.emit('tutorial.start',{level:3});}else if(x.type==='game.level_fail'){active=false;}});requestAnimationFrame(frame);
  }
  window.oneConnectThirdGuide={install:install,state:function(){return {active:active};}};
}());
