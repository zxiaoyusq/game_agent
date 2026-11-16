const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{execFileSync}=require('node:child_process');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'oc-worker-version-'));
try{
 const game=path.join(dir,'game');fs.mkdirSync(game);fs.writeFileSync(path.join(game,'game.html'),'<!doctype html>');
 const script=path.join(dir,'builder.py');let source=fs.readFileSync('tools/build_offline_worker.py','utf8');fs.writeFileSync(script,source);
 const build=()=>{execFileSync('C:/Program Files/Python312/python.exe',[script,'--game-dir',game]);return fs.readFileSync(path.join(game,'offline-worker.js'),'utf8').match(/const NAME=PREFIX\+"([^"]+)"/)[1]};
 const original=build();assert.equal(build(),original,'unchanged worker and files keep their version');
 assert(source.includes('const allowed='));source=source.replace('const allowed=','// changed worker logic\nconst allowed=');fs.writeFileSync(script,source);
 assert.notEqual(build(),original,'worker changes must produce a different cache version');
 console.log('worker code participates in cache version PASS');
}finally{fs.rmSync(dir,{recursive:true,force:true});}
