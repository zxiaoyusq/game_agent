/* Hide clipped internal cells from original link-path checks without deleting tiles. */
(function(){'use strict';
 var installed=false,cacheRuntime=null,cacheTick=null,cache=null,reported=false;
 function variable(r,name){var v=r.all_global_vars&&r.all_global_vars.find(function(x){return x.name===name;});return v&&v.data;}
 function bounds(r,board){
  if(Number.isInteger(r.tickcount)&&cacheRuntime===r&&cacheTick===r.tickcount)return cache;
  var rows=variable(r,'ROWS_COUNT'),cols=variable(r,'COLUMNS_COUNT'),size=variable(r,'ITEM_SIZE'),spacing=variable(r,'ITEM_SPACING'),type=r.types&&r.types.t5,clip=window.oneConnectVisibleGravityBounds;
  if(!Number.isInteger(rows)||!Number.isInteger(cols)||!Number.isFinite(size)||!Number.isFinite(spacing)||!type||!clip||!board.arr)return null;
  var live=type.instances.filter(function(t){var v=t.instance_vars,x=v&&v[2],y=v&&v[1];return Number.isInteger(x)&&Number.isInteger(y)&&board.arr[x]&&board.arr[x][y]&&board.arr[x][y][0]===t.uid;});
  if(!live.length)return null;
  var b=clip.clip(r,{top:0,left:0,rows:cols,cols:rows},live,rows,cols,size+spacing);
  cache=b?{minX:cols-(b.top+b.rows-1),maxX:cols-b.top,minY:b.left+1,maxY:b.left+b.cols,rows:rows,cols:cols}:null;cacheRuntime=r;cacheTick=r.tickcount;return cache;
 }
 function install(){if(installed)return;var plugin=window.cr&&cr.plugins_&&cr.plugins_.Arr,p=plugin&&plugin.prototype.Instance&&plugin.prototype.Instance.prototype;
  if(!p||typeof p.at!=='function'||!Array.isArray(window.oneConnectNativePathSids))return;
  if(typeof window.addEventListener==='function'){
   ['resize','orientationchange'].forEach(function(name){window.addEventListener(name,function(){cacheRuntime=null;cache=null;});});
   window.addEventListener('oneconnect:event',function(e){var t=e.detail&&e.detail.type;if(t==='game.board_configured'||t==='game.round_ready'||t==='game.auto_shuffle_complete'||t==='game.shuffle'){cacheRuntime=null;cache=null;reported=false;}});
  }
  var pathEvents=new Set(window.oneConnectNativePathSids),original=p.at;
  p.at=function(x,y,z){var r=this.runtime,frame=r&&typeof r.getCurrentEventStack==='function'&&r.getCurrentEventStack(),ev=frame&&frame.current_event;
   if(!ev||!pathEvents.has(ev.sid)||!this.type||this.type.name!=='t0'||!r.running_layout||r.running_layout.name!=='game'||z!==0)return original.apply(this,arguments);
   x=Math.floor(x);y=Math.floor(y);var rows=variable(r,'ROWS_COUNT'),cols=variable(r,'COLUMNS_COUNT');
   // The native outer perimeter remains available for legal two-turn links.
   if(x<1||x>cols||y<1||y>rows)return original.apply(this,arguments);
   var b;try{b=bounds(r,this);}catch(_){b=null;}
   if(!b){if(!reported){reported=true;try{if(window.oneConnectHost)window.oneConnectHost.emit('config.board_error',{message:'Unable to determine visible board bounds'});}catch(_){}}return -1;}
   reported=false;
   // One empty-cell lane around the visible grid is needed for the native
   // two-turn perimeter route. Keep its actual occupancy: occupied cells must
   // still block paths. Movement is bounded independently by the move guard.
   return x<b.minX-1||x>b.maxX+1||y<b.minY-1||y>b.maxY+1?-1:original.apply(this,arguments);
  };installed=true;
 }
 window.oneConnectNativeBoardMask={install:install};
}());
