const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function Anchor(){};const anchor={type:{behavior:new Anchor()},enabled:true};
const tile={uid:63,x:0,y:0,width:1280,height:720,behavior_insts:[anchor],texture_img:{width:300,height:300},layer:{canvasToLayer:(x,y,isX)=>isX?x:y},set_bbox_changed(){}};
const handlers={},r={running_layout:{name:'menu'},types:{t46:{instances:[tile]}},redraw:false},window={cr:{behaviors:{Anchor}},addEventListener:(name,fn)=>handlers[name]=fn};
vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/menu_starfield_experiment.js','utf8'),{window,Math,Number});
const effect=window.oneConnectMenuStarfieldExperiment;
assert.equal(effect.update(r,.1,false),false);assert.deepEqual([tile.x,tile.y,tile.width,tile.height],[0,0,1280,720]);
for(let n=0;n<1200;n++){assert(effect.update(r,.1,true));assert.equal(anchor.enabled,false,'native Anchor must not undo scrolling on its next tick');if(anchor.enabled){tile.x=0;tile.y=0;tile.width=1280;tile.height=720;}assert(tile.x<=0&&tile.y<=0&&tile.x+tile.width>=1280&&tile.y+tile.height>=720,'background covers original viewport throughout wrap');}
assert(r.redraw,'moving texture requires a redraw');r.running_layout.name='game';effect.update(r,.1,true);assert.deepEqual([tile.x,tile.y,tile.width,tile.height],[0,0,1280,720]);assert.equal(anchor.enabled,true,'leaving the menu restores original anchoring');
tile.layer.canvasToLayer=(x,y,isX)=>isX?-y:x;r.running_layout.name='menu';effect.update(r,.1,true);
const localDx=tile.x+300,localDy=tile.y+300;const screenDx=localDy,screenDy=-localDx;
assert(screenDx>0&&screenDy<0,'rotated layer still moves toward the screen upper right');
effect.restore();assert.deepEqual([tile.x,tile.y,tile.width,tile.height],[0,0,1280,720]);
tile.layer.canvasToLayer=(x,y,isX)=>isX?x:y;effect.update(r,.1,true);assert.equal(anchor.enabled,false);handlers.resize();assert.equal(anchor.enabled,true,'resize temporarily restores native anchoring');assert.equal(effect.update(r,.1,true),false,'give the native anchor a frame to adjust');tile.width=1440;effect.update(r,.1,true);assert.equal(anchor.enabled,false);assert.equal(tile.width,2040,'scroll coverage is recomputed from the resized background');effect.restore();assert.equal(tile.width,1440);assert.equal(anchor.enabled,true);
console.log('experimental starfield covers viewport and restores original geometry PASS');
