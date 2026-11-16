import {mkdir,readFile,writeFile,cp,rm,readdir,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const hash=b=>createHash('sha256').update(b).digest('hex');
export async function files(dir) {const out=[];for(const entry of await readdir(dir,{withFileTypes:true})){const p=dir+'/'+entry.name;if(entry.isDirectory())out.push(...await files(p));else out.push(p);}return out.sort();}
export async function sourceFiles() {
  return ['package.json','package-lock.json','index.html','style.css','README.md','workflow/board-contract.json','workflow/art-integration.json','workflow/art-manifest.json',...await files('src'),...await files('tests'),'scripts/build.mjs','scripts/check.mjs','scripts/release.mjs',...await files('public/assets')].sort();
}
export async function fingerprint() {const map={};for(const p of await sourceFiles())map[p]=hash(await readFile(p));return {sha256:hash(Buffer.from(JSON.stringify(map))),files:map};}
export async function build() {
  const manifest=JSON.parse(await readFile('workflow/art-manifest.json','utf8'));
  for(const a of manifest.assets) {const b=await readFile(a.path);if(!b.length||hash(b)!==a.sha256)throw Error('美术交接哈希不一致：'+a.path);}
  await rm('dist',{recursive:true,force:true});await mkdir('dist',{recursive:true});
  for(const p of ['index.html','style.css','src'])await cp(p,'dist/'+p,{recursive:true});
  await cp('public/assets','dist/assets',{recursive:true});
  await cp('workflow/board-contract.json','dist/assets/board-contract.json');await cp('workflow/art-manifest.json','dist/assets/manifest.json');
  const source=await fingerprint();await writeFile('dist/build-info.json',JSON.stringify({version:'1.0.0',source},null,2));
  let bytes=0;for(const p of await files('dist'))bytes+=(await stat(p)).size;
  if(bytes>=10*1024*1024)throw Error('构建超过10MiB');
  await mkdir('evidence',{recursive:true});await writeFile('evidence/build.json',JSON.stringify({bytes,source,assetCount:manifest.assets.length},null,2));
  console.log(`构建成功：${bytes}字节，${manifest.assets.length}份原素材，源码指纹 ${source.sha256}`);
}
if(process.argv[1]?.endsWith('/build.mjs')) await build();
