/* Capture only the original same-type pick branch after its path test. */
(function () {
  'use strict';
  var installed=false;
  function install() {
    if(installed)return;
    var proto=window.cr&&cr.action&&cr.action.prototype;
    if(!proto||typeof proto.run_system!=='function')return;
    var original=proto.run_system;
    proto.run_system=function(){
      var returned=original.apply(this,arguments);
      if(this.sid!==564412399746352)return returned;
      try {
        var r=this.runtime,vars=r&&r.all_local_vars||[];
        // Construct stores non-static event locals on the current event stack;
        // .data is only their initial value and can incorrectly signal failure.
        function local(sid){var item=vars.find(function(v){return v.sid===sid;});return item&&(typeof item.getValue==='function'?item.getValue():item.data);}
        var pathLocal=vars.find(function(v){return v.sid===230773463274312;});
        // Never infer a failed path from the stale initial value when the
        // runtime cannot provide the active event-stack value.
        if(!pathLocal||typeof pathLocal.getValue!=='function'||pathLocal.getValue()!=='')return returned;
        var ids=[local(549914461589189),local(205709254634256)];
        if(!ids.every(Number.isInteger)||ids[0]===ids[1])return returned;
        var tiles=r.types.t5&&r.types.t5.instances||[],selected=ids.map(function(id){return tiles.find(function(t){return t.uid===id;});});
        if(selected.some(function(t){return !t||!t.layer||!t.instance_vars;})||selected[0].instance_vars[0]!==selected[1].instance_vars[0])return returned;
        var rect=r.canvas.getBoundingClientRect(),ratio=r.isRetina?r.devicePixelRatio:1;
        if(!rect.width||!rect.height||!r.canvas.width||!r.canvas.height)return returned;
        var points=selected.map(function(t){return {x:rect.left+t.layer.layerToCanvas(t.x,t.y,true)*ratio*rect.width/r.canvas.width,y:rect.top+t.layer.layerToCanvas(t.x,t.y,false)*ratio*rect.height/r.canvas.height};});
        if(points.some(function(p){return !Number.isFinite(p.x)||!Number.isFinite(p.y);}))return returned;
        if(window.oneConnectHost)window.oneConnectHost.emit('candidate.invalid_link',{points:points,uids:ids});
        // Provisional tactile feedback; duration is not a recovered competitor parameter.
        if(window.oneConnectHapticsCandidate)window.oneConnectHapticsCandidate.pulse(25);
      } catch(error) { console.warn('Invalid-link capture failed',error); }
      return returned;
    };
    installed=true;
  }
  window.oneConnectInvalidLinkCaptureCandidate={install:install};
}());
