const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const dir=process.argv[2];assert(dir,'candidate game directory required');
const data=JSON.parse(fs.readFileSync(path.join(dir,'data.js'),'utf8'));
const runtime=fs.readFileSync(path.join(dir,'c2runtime.js'),'utf8');
const refs=runtime.split('cr.getObjectRefTable=function(){return[')[1].split(']')[0].split(',');
assert.equal(refs[153],'cr.plugins_.Sprite.prototype.cnds.OnDestroyed','no-match chain waits for the fade object to be destroyed');
let fade=null,wait=null;
function visit(x){if(Array.isArray(x)){if(x.length===6&&Array.isArray(x[0])&&x[1]===50&&Number.isInteger(x[2]))fade=x[4][0];if(x.length>5&&x[3]===730435901061908)wait=x[5];for(const v of x)visit(v)}else if(x&&typeof x==='object')Object.values(x).forEach(visit)}
visit(data.project[5]);visit(data.project[6]);assert(fade&&wait);assert.deepEqual(fade.slice(1,4),[.05,.05,.05],'fade-in, hidden wait and fade-out are all short');assert.deepEqual(wait,[[0,[1,.05]]],'post-tween native wait is short');
console.log('native no-match fade and hidden wait are bounded PASS');
