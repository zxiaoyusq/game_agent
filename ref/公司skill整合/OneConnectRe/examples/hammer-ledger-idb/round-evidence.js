(function(){
 'use strict';
 // Experimental only. A marker must be written by a trusted game integration
 // into the same stable snapshot as the board; this module does not write it.
 function context(snapshot,entry){if(!window.oneConnectRoundSaveModel.validate(snapshot,entry))throw Error('invalid stable snapshot');return JSON.stringify({version:1,level:snapshot.level,config:snapshot.config,rows:snapshot.rows,cols:snapshot.cols,board:snapshot.board,timer:snapshot.timer,score:snapshot.score,tip:snapshot.tip,shuffle:snapshot.shuffle});}
 function sameBoard(a,b){return a.level===b.level&&a.config===b.config&&a.rows===b.rows&&a.cols===b.cols&&JSON.stringify(a.board)===JSON.stringify(b.board);}
 function validRemoval(a,b){var counts={},changed=0;for(var row of a.board)for(var v of row)if(v)counts[v]=(counts[v]||0)+1;for(var row of b.board)for(var v of row)if(v)counts[v]=(counts[v]||0)-1;for(var k of Object.keys(counts)){if(counts[k]===2)changed++;else if(counts[k]!==0)return false;}return changed===1;}
 function classify(op,snapshot,entry,restored){try{if(!op||op.status!=='pending'||typeof op.id!=='string'||typeof op.context!=='string'||!snapshot||!window.oneConnectRoundSaveModel.validate(snapshot,entry))return 'unknown';var before=JSON.parse(op.context);if(!window.oneConnectRoundSaveModel.validate(before,entry)||before.level!==snapshot.level||before.config!==snapshot.config||before.rows!==snapshot.rows||before.cols!==snapshot.cols)return 'unknown';if(snapshot.hammerOperationId===op.id&&validRemoval(before,snapshot))return 'commit';if(restored===true&&snapshot.hammerOperationId===undefined&&sameBoard(before,snapshot))return 'refund';return 'unknown';}catch(_){return 'unknown';}}
 window.oneConnectHammerRoundEvidence={context:context,classify:classify};
}());
