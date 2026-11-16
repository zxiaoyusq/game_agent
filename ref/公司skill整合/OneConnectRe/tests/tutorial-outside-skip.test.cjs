const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const listeners={};const document={hidden:false,addEventListener:(name,fn)=>listeners[name]=fn};
const w={document};vm.runInNewContext(fs.readFileSync(process.argv[2],'utf8'),{window:w,document});
let active=true,phase=1,skipped=0;const box={style:{display:'block'},getBoundingClientRect:()=>({left:10,top:10,right:30,bottom:30,width:20,height:20})};
w.oneConnectGuideOutsideSkip.register({active:()=>active,targets:()=>[box],token:()=>phase,skip:()=>{skipped++;active=false}});
function click(x,y){let stopped=false;listeners.click({clientX:x,clientY:y,button:0,preventDefault(){},stopPropagation(){stopped=true},stopImmediatePropagation(){stopped=true}});return stopped}
click(50,50);assert.equal(skipped,0);click(15,15);click(50,50);assert.equal(skipped,0,'highlight resets consecutive misses');phase++;click(50,50);assert.equal(skipped,0,'new step resets misses');assert.equal(click(50,50),true);assert.equal(skipped,1);click(50,50);assert.equal(skipped,1);console.log('outside skip semantics PASS');
