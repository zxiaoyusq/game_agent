/* Candidate fly-star score. Runtime path coordinates remain subject to review. */
(function(){
 'use strict';
 var state=null,installed=false;
 function valid(s){return !!s&&s.version===1&&Number.isInteger(s.level)&&s.level>0&&Number.isSafeInteger(s.count)&&s.count>=0&&Number.isSafeInteger(s.paths)&&s.paths>=0&&Number.isSafeInteger(s.matches)&&s.matches>=0&&typeof s.known==='boolean';}
 function begin(level){state=Number.isInteger(level)&&level>0?{version:1,level:level,count:0,paths:0,matches:0,known:true}:null;}
 function restore(save){var s=save&&save.flyStars;state=valid(s)&&s.level===save.level?Object.assign({},s):null;}
 function snapshot(level){return state&&state.level===level?Object.assign({},state):null;}
 function rating(level){
  if(!state||!state.known||state.level!==level||state.paths!==state.matches)return null;
  // Thresholds and the unit feeding them must both be verified. A numeric
  // match alone cannot prove our estimated fly-star count equals nScore.
  var ref=window.oneConnectCompetitorStarReference;if(!ref||ref.baseVerified!==true||ref.countVerified!==true)return null;
  var thresholds=ref.levels&&ref.levels[level];
  if(!Array.isArray(thresholds)||thresholds.length!==3||thresholds.some(function(n){return !Number.isSafeInteger(n)||n<1;})||thresholds[0]>thresholds[1]||thresholds[1]>thresholds[2])return null;
  return {count:state.count,stars:thresholds.filter(function(n){return state.count>=n;}).length};
 }
 function progress(level){
  var rated=rating(level);if(!rated)return null;
  var thresholds=window.oneConnectCompetitorStarReference.levels[level],earned=rated.stars;
  if(earned===3)return {count:rated.count,stars:earned,fraction:1};
  var previous=earned?thresholds[earned-1]:0,next=thresholds[earned];
  return {count:rated.count,stars:earned,fraction:(earned+(rated.count-previous)/(next-previous))/3};
 }
 function event(e){var d=e&&e.detail;if(!d||!state)return;var detail=d.detail||{};
  if(d.type==='candidate.link_points'){
   var hammer=window.oneConnectHammer&&window.oneConnectHammer.state().busy;
   if(hammer)return;
   if(detail.level!==state.level||!Number.isSafeInteger(detail.starCountEstimate)||detail.starCountEstimate<2||
      !Array.isArray(detail.pathScreenPoints)||detail.pathScreenPoints.length!==detail.starCountEstimate||
      !Number.isSafeInteger(state.count+detail.starCountEstimate)){state.known=false;return;}
   state.count+=detail.starCountEstimate;state.paths++;
  }else if(d.type==='game.match'){
   if(detail.level!==state.level){state.known=false;return;}
   if(detail.source==='hammer')state.count+=2;else if(detail.source==='normal')state.matches++;else state.known=false;
  }
 }
 function install(){if(installed)return;installed=true;window.addEventListener('oneconnect:event',event);}
 window.oneConnectFlyStarScoreCandidate={install:install,begin:begin,restore:restore,snapshot:snapshot,rating:rating,progress:progress};
}());
