const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync('game/c2runtime.js','utf8'),start=src.indexOf('cr.behaviors.Fade=function'),end=src.indexOf('cr.behaviors.Pin=function',start);
assert(start>=0&&end>start,'native fade behavior must be present');
const cr={behaviors:{},KahanAdder:function(){this.sum=0;this.add=n=>this.sum+=n;this.reset=()=>this.sum=0}},destroyed=[];
vm.runInNewContext(src.slice(start,end).replace(/,\s*$/,';'),{cr});
const runtime={getDt:()=>.1,trigger(){},DestroyInstance(x){destroyed.push(x)}},fade=new cr.behaviors.Fade(runtime),type=new cr.behaviors.Fade.prototype.Type(fade,{}),sprite={opacity:1},instance=new cr.behaviors.Fade.prototype.Instance(type,sprite);
instance.properties=[1,0,0,.25,1];instance.onCreate();instance.tick();assert(sprite.opacity<1&&sprite.opacity>0,'native sprite fades after being spawned');
instance.tick();instance.tick();assert.equal(sprite.opacity,0);assert.equal(destroyed.length,1,'native sprite is destroyed at fade end');
console.log('native removal dot fades and self-destructs PASS');
