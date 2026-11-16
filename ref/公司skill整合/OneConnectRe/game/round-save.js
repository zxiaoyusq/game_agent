(function(){
 'use strict';
 var key='oneconnect.round.v1',installed=false,allowResume=true,active=false,tutorial=false,shuffling=false,unstableUntil=0,pendingDisplay=null,lastCaptured=null;
 function variable(r,name){return r.all_global_vars.find(function(v){return v.name===name;});}
 function entryFor(level){var a=window.oneConnectLevels&&window.oneConnectLevels.levels,entry=Array.isArray(a)&&a.find(function(x){return x.level===level;});return entry||(Number.isInteger(level)&&level>=1&&level<=100000?{level:level,original:true}:null);}
 function clear(){pendingDisplay=null;lastCaptured=null;try{localStorage.removeItem(key)}catch(_){}}
 function restore(entry){
  if(!allowResume){clear();return null;}allowResume=false;
  var s;try{s=JSON.parse(localStorage.getItem(key)||'null');}catch(_){s=null;}
  if(!window.oneConnectRoundSaveModel.validate(s,entry)){clear();return null;}
  pendingDisplay=s;return s;
 }
 function capture(){
  var r=window.cr_getC2Runtime&&window.cr_getC2Runtime();
  if(!active||shuffling||Date.now()<unstableUntil||!r||!r.running_layout||r.running_layout.name!=='game'||(window.oneConnectGravityRuntime&&window.oneConnectGravityRuntime.state().moving))return false;
  var lev=variable(r,'level'),rows=variable(r,'ROWS_COUNT'),cols=variable(r,'COLUMNS_COUNT'),timer=variable(r,'timer'),score=variable(r,'score'),tip=variable(r,'tip'),shuffle=variable(r,'shuffle');
  var entry=lev&&entryFor(lev.data),a=r.types.t0&&r.types.t0.instances[0],t=r.types.t5&&r.types.t5.instances,state=r.types.t32&&r.types.t32.instances[0];
  if(!entry||!a||!t||!state||!rows||!cols||!timer||!score||!tip||!shuffle||a.cx!==cols.data+2||a.cy!==rows.data+2||t.some(function(tile){return tile.instance_vars[3];}))return false;
  var index=new Map(t.map(function(tile){return [tile.uid,tile];})),count=0,board=[];
  for(var y=1;y<=rows.data;y++){var row=[];for(var x=1;x<=cols.data;x++){var id=a.arr[x][y][0];if(!id){row.push(0);continue;}var tile=index.get(id);if(!tile||tile.instance_vars[1]!==y||tile.instance_vars[2]!==x)return false;row.push(tile.instance_vars[0]);count++;}board.push(row);}
  if(count!==t.length||state.instance_vars[3]!==rows.data*cols.data-count)return false;
  if(tutorial){
   if(lev.data===1){var tutor=window.oneConnectTutorial,tutorState=tutor&&tutor.state();if(!tutorState||!tutorState.active||tutor.resumeStep(board)!==tutorState.step)return false;}
   else {var guides={3:'oneConnectThirdGuide',5:'oneConnectFifthGuide',7:'oneConnectSeventhGuide',10:'oneConnectTenthGuide'},guide=window[guides[lev.data]];if(!guide||!guide.state().active)return false;}
  }
  var s={version:1,level:lev.data,config:window.oneConnectRoundSaveModel.fingerprint(entry),rows:rows.data,cols:cols.data,board:board,timer:timer.data,score:score.data,tip:tip.data,shuffle:shuffle.data};
  if(!window.oneConnectRoundSaveModel.validate(s,entry))return false;
  try{var encoded=JSON.stringify(s);if(localStorage.getItem(key)!==encoded)localStorage.setItem(key,encoded);lastCaptured=encoded;return true;}catch(_){return false;}
 }
 // Preserve a reward in the last stable snapshot when the current board is
 // mid-animation. Never rewrite a snapshot from another round or writer.
 function checkpointRewardCounter(kind,level,before){
  if(!active||!lastCaptured||(kind!=='tip'&&kind!=='shuffle')||!Number.isInteger(before)||before<0||before>997)return false;
  var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),lev=r&&variable(r,'level'),counter=r&&variable(r,kind),entry=entryFor(level);
  if(!r||!r.running_layout||r.running_layout.name!=='game'||!lev||lev.data!==level||!counter||counter.data!==before+2)return false;
  try{var stored=localStorage.getItem(key);if(stored!==lastCaptured)return false;var s=JSON.parse(stored);
   if(!window.oneConnectRoundSaveModel.validate(s,entry)||s[kind]!==before)return false;
   s[kind]=before+2;var encoded=JSON.stringify(s);localStorage.setItem(key,encoded);lastCaptured=encoded;return true;
  }catch(_){return false;}
 }
 function install(){if(installed)return;installed=true;
  window.addEventListener('oneconnect:event',function(e){var d=e.detail;if(!d)return;
   if(d.type==='game.board_configured'||d.type==='game.round_ready'){
    active=true;lastCaptured=null;shuffling=false;unstableUntil=Date.now()+500;
    var saved=pendingDisplay;pendingDisplay=null;
    if(saved)window.setTimeout(function(){
     var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),level=r&&variable(r,'level');
     if(!r||!r.running_layout||r.running_layout.name!=='game'||!level||level.data!==saved.level||!window.cr||!cr.plugins_||!cr.plugins_.Spritefont2)return;
     var fonts=r.types.t25&&r.types.t25.instances||[];
     [[2,'score'],[3,'shuffle'],[4,'tip']].forEach(function(pair){var font=fonts.find(function(t){return t.instance_vars&&t.instance_vars[0]===pair[0];});if(font)cr.plugins_.Spritefont2.prototype.acts.SetText.call(font,String(saved[pair[1]]));});
    },0);
   }
   if(d.type==='game.auto_shuffle_start')shuffling=true;
   if(d.type==='game.auto_shuffle_complete')shuffling=false;
   if(d.type==='tutorial.start')tutorial=true;
   if(d.type==='tutorial.complete')tutorial=false;
   if(d.type==='game.match'||d.type==='game.hammer'||d.type==='game.shuffle'||d.type==='game.auto_shuffle_start'||d.type==='game.auto_shuffle_complete')unstableUntil=Date.now()+1000;
   if(d.type==='game.level_fail'||d.type==='game.level_win'||d.type==='screen.SCREEN_BONUS'){active=false;tutorial=false;clear();}
  });
  window.addEventListener('pagehide',capture);document.addEventListener('visibilitychange',function(){if(document.hidden)capture();});window.setInterval(capture,500);
 }
 window.oneConnectRoundSave={install:install,restore:restore,capture:capture,clear:clear,checkpointRewardCounter:checkpointRewardCounter};
}());
