import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';import {createHash} from 'node:crypto';import assert from 'node:assert/strict';import {files,sourceFiles,fingerprint} from './build.mjs';
// 无外部压缩命令：ZIP STORE条目，确定时间戳，CRC32完整校验。
const table=Array.from({length:256},(_,n)=>{let c=n;for(let k=0;k<8;k++)c=(c&1)?0xedb88320^(c>>>1):c>>>1;return c>>>0;});
function crc32(data){let c=0xffffffff;for(const b of data)c=table[(c^b)&255]^(c>>>8);return (c^0xffffffff)>>>0;}
function hash(data){return createHash('sha256').update(data).digest('hex');}
async function zip(paths,path,prefix='') {
 let offset=0;const local=[],central=[];
 for(const file of paths){const data=await readFile(file),name=Buffer.from(prefix+file.replace(/^dist\//,'')),crc=crc32(data);const h=Buffer.alloc(30);h.writeUInt32LE(0x04034b50,0);h.writeUInt16LE(20,4);h.writeUInt16LE(0x0800,6);h.writeUInt16LE(0x21,12);h.writeUInt32LE(crc,14);h.writeUInt32LE(data.length,18);h.writeUInt32LE(data.length,22);h.writeUInt16LE(name.length,26);local.push(h,name,data);
 const c=Buffer.alloc(46);c.writeUInt32LE(0x02014b50,0);c.writeUInt16LE(20,4);c.writeUInt16LE(20,6);c.writeUInt16LE(0x0800,8);c.writeUInt16LE(0x21,14);c.writeUInt32LE(crc,16);c.writeUInt32LE(data.length,20);c.writeUInt32LE(data.length,24);c.writeUInt16LE(name.length,28);c.writeUInt32LE(offset,42);central.push(c,name);offset+=h.length+name.length+data.length;
 }
 const directory=Buffer.concat(central),end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50,0);end.writeUInt16LE(paths.length,8);end.writeUInt16LE(paths.length,10);end.writeUInt32LE(directory.length,12);end.writeUInt32LE(offset,16);const data=Buffer.concat([...local,directory,end]);await writeFile(path,data);return {path,bytes:data.length,sha256:hash(data),entries:paths.length};
}
const check=JSON.parse(await readFile('evidence/browser/report.json','utf8'));assert.equal(check.passed,true,'最终浏览器check必须通过');const source=await fingerprint();assert.equal(source.sha256,check.source,'验收后源码已变动');
for(const [p,h]of Object.entries(check.distHashes))assert.equal(hash(await readFile(p)),h,'最终dist验收后被修改');
await mkdir('releases',{recursive:true});
const sourceList=[...await sourceFiles(),'workflow/prototype.md','workflow/art.md','workflow/reference-evidence.md','workflow/code.md'];
const packages=[await zip(sourceList,'releases/ludo-source.zip'),await zip(await files('dist'),'releases/ludo-play.zip')];
await writeFile('releases/manifest.json',JSON.stringify({version:'1.0.0',source:source.sha256,packages,distHashes:check.distHashes,limits:'参考素材商业/再发布许可未核验；浏览器模拟非真机'},null,2));console.log('已生成源码与试玩ZIP，未修改最终dist：'+JSON.stringify(packages));
