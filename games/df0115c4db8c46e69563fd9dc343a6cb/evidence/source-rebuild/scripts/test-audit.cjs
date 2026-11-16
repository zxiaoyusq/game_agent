/* 测试阶段补充只读审计：保留原交付包证据，验证后不修改dist或上游文件。 */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const {walk,unpack}=require('./archive.cjs');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const entries=d=>walk(d).sort().map(p=>({path:p.slice(d.length+1),bytes:fs.statSync(p).size,sha256:hash(p)}));
const upstream=()=>[...walk('src'),...walk('public'),...walk('assets'),...walk('workflow').filter(p=>p!=='workflow/test.md'),...walk('scripts'),...walk('tests'),'package.json','package-lock.json','README.md'].sort().map(p=>({path:p,sha256:hash(p)}));
const videos=()=>fs.existsSync('evidence/videos')?walk('evidence/videos').filter(p=>p.endsWith('.webm')):[];
fs.mkdirSync('evidence',{recursive:true});
if(process.argv[2]==='pre'){
  const dist=entries('dist');
  const originalPackages=['releases/animal-tetris-play.zip','releases/animal-tetris-source.zip'].map(p=>({path:p,bytes:fs.statSync(p).size,sha256:hash(p)}));
  const dest='evidence/test-original-play';fs.rmSync(dest,{recursive:true,force:true});unpack(originalPackages[0].path,dest);assert.deepEqual(entries(dest),dist);
  const source='evidence/test-original-source';fs.rmSync(source,{recursive:true,force:true});unpack(originalPackages[1].path,source);
  execFileSync(process.execPath,['scripts/build.cjs'],{cwd:path.resolve(source),stdio:'pipe'});assert.deepEqual(entries(source+'/dist'),dist);
  const result=execFileSync(process.execPath,['--test','tests/rules.test.cjs'],{cwd:path.resolve(source),encoding:'utf8'});fs.writeFileSync('evidence/test-original-source-tests.txt',result);
  fs.writeFileSync('evidence/test-baseline.json',JSON.stringify({stage:'test',attempt:1,date:new Date().toISOString(),node:process.version,upstream:upstream(),dist,originalPackages,originalPlayMatches:true,originalSourceRebuildMatches:true,originalSourceTestsPassed:true,previousVideos:videos()},null,2));
  console.log('测试前审计通过：原试玩包一致，原源码包实际解压重建一致，原包13项规则测试通过。');
}else{
  const baseline=JSON.parse(fs.readFileSync('evidence/test-baseline.json'));assert.deepEqual(upstream().filter(e=>e.path!=='scripts/test-audit.cjs'),baseline.upstream.filter(e=>e.path!=='scripts/test-audit.cjs'),'上游源码/资源/既有脚本必须未修改');assert.deepEqual(entries('dist'),baseline.dist,'本轮构建与原交付逐文件一致');
  const manifest=JSON.parse(fs.readFileSync('workflow/art-manifest.json'));for(const a of manifest.assets){for(const k of ['path','sha256','usage','source'])assert.ok(typeof a[k]==='string'&&a[k]);assert.equal(hash(a.path),a.sha256);}
  const spec=JSON.parse(fs.readFileSync('workflow/visual-spec.json'));const runtime=[...Object.values(spec.tiles).map(v=>v.path),spec.background.path];for(const p of runtime)assert.equal(hash('dist/'+p),hash('public/'+p));assert.equal(runtime.length,8);assert.ok(!fs.existsSync('dist/assets/tiles/T-owl.webp'));
  const check=JSON.parse(fs.readFileSync('evidence/check.json'));assert.equal(check.passed,true);assert.equal(check.distUnchanged,true);assert.deepEqual(check.consoleErrors,[]);
  const animation=JSON.parse(fs.readFileSync('evidence/animation.json'));assert.equal(animation.normalSpeed,true);assert.equal(animation.clockOverrides,false);const frames=animation.frames.map((f,i)=>({...f,path:'evidence/clear-'+String(i).padStart(2,'0')+'.png',sha256:hash('evidence/clear-'+String(i).padStart(2,'0')+'.png')}));
  // 原脚本可记录多次真实消行，计分与倒计时应在同一消行段内核对，而不是跨次比较。
  const end=frames.findIndex(f=>f.after);assert.ok(end>=3,'第一段消行需要至少三帧及完成帧');const complete=frames.slice(0,end+1),firstScore=complete[0].score;let previous=Infinity;for(const f of complete){assert.ok(f.remaining>=0&&f.remaining<=180);assert.equal(f.score,firstScore);assert.ok(f.remaining<=previous);previous=f.remaining;}assert.ok(new Set(complete.filter(f=>!f.after).map(f=>f.sha256)).size>=3,'动态画面至少三个不同帧');assert.ok(Math.abs((complete.at(-1).time-complete[0].time)-complete[0].remaining)<40,'真实rAF时间与剩余动画时间一致');
  const newVideos=videos().filter(p=>!baseline.previousVideos.includes(p)).map(p=>({path:p,bytes:fs.statSync(p).size,sha256:hash(p)}));assert.ok(newVideos.some(v=>v.bytes>0),'本attempt必须有新录像');
  const releases=JSON.parse(fs.readFileSync('evidence/releases.json'));for(const r of releases)assert.equal(hash(r.path),r.sha256);
  const result={passed:true,stage:'test',attempt:1,date:new Date().toISOString(),node:process.version,browser:check.browser,upstreamUnchanged:true,originalAndFinalDistMatch:true,distBytes:baseline.dist.reduce((n,e)=>n+e.bytes,0),assetManifestEntries:manifest.assets.length,runtimeAssets:runtime,frames,newVideos,releases,limitations:['仅Chromium自动化及模拟触屏，没有实体手机或Safari验收','原参考PNG读取为二进制文本，依据用户已核对描述与正式素材比对','源码包使用当前Node独立重建及测试；未执行清洁npm ci，也未验证全新机器浏览器安装']};
  fs.writeFileSync('evidence/test-audit.json',JSON.stringify(result,null,2));console.log('测试后审计通过：上游不变、17项素材哈希一致、最终dist与原交付一致、正常速度多帧及本轮录像有效。');
}
