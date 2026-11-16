/* Reference formula from DSH's ShapeData.SetShapeWithHeight disassembly.
 * This is a pure calculation, not yet connected to the Construct viewport.
 * Width/height parameter pairing and the original cap remain unverified. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory();
  else root.oneConnectBoardFitCandidate=factory();
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  function cellSize(width,height,columns,rows,cap){
    if(!Number.isFinite(width)||width<=0||!Number.isFinite(height)||height<=0||
       !Number.isInteger(columns)||columns<=0||!Number.isInteger(rows)||rows<=0||
       !Number.isFinite(cap)||cap<=0)throw new RangeError('invalid board fit parameters');
    return Math.min(cap,Math.floor(width/columns),Math.floor(height/rows));
  }
  return {cellSize:cellSize};
});
