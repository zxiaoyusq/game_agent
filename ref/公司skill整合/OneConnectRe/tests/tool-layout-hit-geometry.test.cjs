const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const dir=process.argv[2],load=(source,built)=>{const ctx={module:{exports:{}},Map,Set,Math,Number,Object,Array};vm.runInNewContext(fs.readFileSync(dir?path.join(dir,built):source,'utf8'),ctx);return ctx.module.exports};
const geometry=load('tools/in_game_layout.js','layout-geometry.js'),adapter=load('tools/in_game_layout_adapter.js','layout-adapter.js');
for(const [width,height] of [[320,640],[390,844],[414,896],[768,1024],[1280,1800]]){
 const layer={canvasToLayer:(x,y,axis)=>axis?x:y,layerToCanvas:(x,y,axis)=>axis?x:y};
 const make=(cur_frame,w,h,hx,hy)=>({cur_frame,x:0,y:0,width:w,height:h,hotspotX:hx,hotspotY:hy,layer,set_bbox_changed(){}});
 const shuffle=make(0,108.8816,90.7347,.56666666,.48),hint=make(1,95.5131,95.5131,.5,.5);
 const rect={left:0,top:0,width,height},runtime={running_layout:{name:'game'},canvas:{width,height,getBoundingClientRect:()=>rect},types:{t26:{instances:[shuffle,hint]},t25:{instances:[]}}};
 const layout=geometry.calculate({width,height,rows:12,cols:6});assert.equal(adapter.moveTools(runtime,layout),true);
 const bounds=t=>({left:t.x-t.width*t.hotspotX,right:t.x+t.width*(1-t.hotspotX),top:t.y-t.height*t.hotspotY,bottom:t.y+t.height*(1-t.hotspotY)});
 const a=bounds(shuffle),b=bounds(hint);assert(a.right<b.left||b.right<a.left||a.bottom<b.top||b.bottom<a.top,`tool bounds overlap at ${width}x${height}`);
 adapter.restore(runtime);
}
console.log('tool hit bounds stay separate at representative screen sizes PASS');
