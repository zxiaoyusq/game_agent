const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');const window={};vm.runInNewContext(fs.readFileSync('tools/visible_gravity_bounds.js','utf8'),{window,Number,Math});
const layer={layerToCanvas:(x,y,h)=>h?x:y},ref={x:100,y:100,width:80,height:80,layer,instance_vars:[0,1,1]},r={canvas:{width:300,height:200,getBoundingClientRect:()=>({left:0,top:0,right:300,bottom:200,width:300,height:200})}};
const bounds={top:0,left:0,rows:5,cols:2};let result=window.oneConnectVisibleGravityBounds.clip(r,bounds,[ref],2,5,100);
assert.deepEqual(JSON.parse(JSON.stringify(result)),{top:3,left:0,rows:2,cols:1},'only entirely visible destinations remain');
const offscreen={...ref,x:500,instance_vars:[0,1,5]};assert.equal(window.oneConnectVisibleGravityBounds.clip(r,bounds,[ref,offscreen],2,5,100),null,'cannot discard existing offscreen tiles');
assert.equal(window.oneConnectVisibleGravityBounds.clip({canvas:null},bounds,[ref],2,5,100),null,'unavailable geometry must not permit unbounded movement');
const shrinking={...ref,width:20,height:20,x:75,y:75},sized={...r,all_global_vars:[{name:'ITEM_SIZE',data:190}]};
assert.equal(window.oneConnectVisibleGravityBounds.clip(sized,{top:4,left:0,rows:1,cols:1},[shrinking],1,5,100),null,'temporarily small sprite must not admit a cell that clips its full size');
console.log('gravity destinations are restricted to visible complete cells without deleting tiles PASS');
