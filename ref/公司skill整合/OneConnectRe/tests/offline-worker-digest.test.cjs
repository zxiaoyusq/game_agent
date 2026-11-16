const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process'),{webcrypto,createHash}=require('node:crypto');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'oc-worker-'));
try{
 fs.writeFileSync(path.join(dir,'game.html'),'known content');
 execFileSync('C:/Program Files/Python312/python.exe',['tools/build_offline_worker.py','--game-dir',dir]);
 const source=fs.readFileSync(path.join(dir,'offline-worker.js'),'utf8');
 async function run(responses,corruptOldManifest=false,validOlderCache=false){
  let digestCount=0,fetchCount=0,install,deleted=false;
  const cache={async match(){return undefined},async put(){}};
  const oldName='oneconnect-offline-'+encodeURIComponent('https://example.test/game/')+'-old';
  const validName='oneconnect-offline-'+encodeURIComponent('https://example.test/game/')+'-older';
  const oldCache={async match(){return {async json(){throw Error('corrupt manifest')}}}};
  const manifest={'./game.html':createHash('sha256').update('known content').digest('hex')};
  const validCache={async match(url){return url.endsWith('__oneconnect_manifest__')?{async json(){return manifest}}:new Response('known content')}};
  const caches={async open(name){return name===oldName?oldCache:name===validName?validCache:cache},async keys(){return validOlderCache?[validName,oldName]:corruptOldManifest?[oldName]:[]},async delete(){deleted=true}};
  const self={registration:{scope:'https://example.test/game/'},clients:{async claim(){}},addEventListener(type,fn){if(type==='install')install=fn}};
  const crypto={subtle:{async digest(...args){digestCount++;return webcrypto.subtle.digest(...args)}}};
  const fetch=async()=>{const text=responses[Math.min(fetchCount++,responses.length-1)];return new Response(text,{status:200})};
  vm.runInNewContext(source,{self,caches,crypto,fetch,Request,Response,URL,Set,Uint8Array,Array,Object,JSON,encodeURIComponent,Error});
  let task;install({waitUntil(value){task=value}});let failed=false;try{await task}catch(_){failed=true}
  return {digestCount,fetchCount,failed,deleted};
 }
 (async()=>{
  assert.deepEqual(await run(['known content']),{digestCount:1,fetchCount:1,failed:false,deleted:false});
  assert.deepEqual(await run(['corrupt','known content']),{digestCount:2,fetchCount:2,failed:false,deleted:false});
  assert.deepEqual(await run(['corrupt']),{digestCount:2,fetchCount:2,failed:true,deleted:true});
  assert.deepEqual(await run(['known content'],true),{digestCount:1,fetchCount:1,failed:false,deleted:false},'corrupt old metadata must not block a fresh install');
  assert.deepEqual(await run([],true,true),{digestCount:1,fetchCount:0,failed:false,deleted:false},'a corrupt newer cache must not prevent reuse of an older valid cache');
  console.log('offline cache validates once, retries corruption and rejects invalid content PASS');
 })().catch(error=>{console.error(error);process.exitCode=1});
}finally{for(const name of ['game.html','offline-worker.js'])fs.rmSync(path.join(dir,name),{force:true});fs.rmdirSync(dir);}
