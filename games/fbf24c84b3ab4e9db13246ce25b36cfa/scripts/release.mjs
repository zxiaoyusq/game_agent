import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';
import { fileList, fingerprints } from './build.mjs';

// 标准无压缩ZIP：小型项目无需另引打包依赖；条目时间固定，按名称排序。
function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
  }
  return (crc ^ 0xffffffff) >>> 0;
}
async function zip(entries, destination) {
  const local = [], central = []; let offset = 0;
  for (const entry of entries.sort((a,b) => a.name.localeCompare(b.name,'en'))) {
    const data = await readFile(entry.path), name = Buffer.from(entry.name), crc = crc32(data);
    const header = Buffer.alloc(30);
    header.writeUInt32LE(0x04034b50); header.writeUInt16LE(20,4); header.writeUInt16LE(0x800,6); header.writeUInt16LE(33,12);
    header.writeUInt32LE(crc,14); header.writeUInt32LE(data.length,18); header.writeUInt32LE(data.length,22); header.writeUInt16LE(name.length,26);
    local.push(header,name,data);
    const index = Buffer.alloc(46);
    index.writeUInt32LE(0x02014b50); index.writeUInt16LE(20,4); index.writeUInt16LE(20,6); index.writeUInt16LE(0x800,8); index.writeUInt16LE(33,14);
    index.writeUInt32LE(crc,16); index.writeUInt32LE(data.length,20); index.writeUInt32LE(data.length,24); index.writeUInt16LE(name.length,28); index.writeUInt32LE(offset,42);
    central.push(index,name); offset += header.length + name.length + data.length;
  }
  const directory = Buffer.concat(central), end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50); end.writeUInt16LE(entries.length,8); end.writeUInt16LE(entries.length,10); end.writeUInt32LE(directory.length,12); end.writeUInt32LE(offset,16);
  const bytes = Buffer.concat([...local,directory,end]); await writeFile(destination,bytes);
  return { path:destination,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),entries:entries.length };
}
async function extractStored(path, destination) {
  const bytes = await readFile(path); let offset = 0;
  while (bytes.readUInt32LE(offset) === 0x04034b50) {
    assert.equal(bytes.readUInt16LE(offset+8),0);
    const size = bytes.readUInt32LE(offset+18), length = bytes.readUInt16LE(offset+26), extra = bytes.readUInt16LE(offset+28);
    const name = bytes.subarray(offset+30,offset+30+length).toString();
    assert(!name.includes('..') && !name.startsWith('/'));
    const start = offset+30+length+extra, data = bytes.subarray(start,start+size);
    assert.equal(crc32(data),bytes.readUInt32LE(offset+14));
    const output = `${destination}/${name}`;
    await mkdir(output.slice(0,output.lastIndexOf('/')),{ recursive:true }); await writeFile(output,data); offset = start+size;
  }
}
function run(command,args,cwd) {
  const result = spawnSync(command,args,{ cwd,encoding:'utf8',timeout:180000 });
  assert.equal(result.status,0,`${command} ${args.join(' ')}失败：${result.stdout}\n${result.stderr}`);
  return result.stdout + result.stderr;
}
const check = JSON.parse(await readFile('evidence/check.json','utf8'));
assert.equal(check.result,'通过','必须先跑通最终浏览器验收');
const distPaths = await fileList('dist');
assert.equal((await fingerprints(distPaths)).sha256,check.dist.sha256,'最终dist与验收快照不一致');
await mkdir('releases',{ recursive:true });
const sourcePaths = [...await fileList('public'),...await fileList('scripts'),...await fileList('tests'),...await fileList('workflow'),'README.md','package.json','package-lock.json'];
const source = await zip(sourcePaths.map(path => ({ path,name:path })),'releases/star-collection-source.zip');
const play = await zip(distPaths.map(path => ({ path,name:path.slice(5) })),'releases/star-collection-play.zip');
const root = 'evidence/source-rebuild';
await rm(root,{ recursive:true,force:true }); await mkdir(root,{ recursive:true }); await extractStored(source.path,root);
// 从实际源码ZIP提取，缓存离线清洁安装，不执行安装生命周期；不依赖原node_modules。
const installLog = run(process.platform === 'win32' ? 'npm.cmd' : 'npm',['ci','--offline','--ignore-scripts'],root);
const buildLog = run(process.execPath,['scripts/build.mjs'],root);
const ruleLog = run(process.execPath,['--test','tests/rules.test.mjs'],root);
for (const path of distPaths) assert.deepEqual(await readFile(path),await readFile(`${root}/${path}`),`重建不一致：${path}`);
await extractStored(play.path,'evidence/play-unpacked');
for (const path of distPaths) assert.deepEqual(await readFile(path),await readFile(`evidence/play-unpacked/${path.slice(5)}`));
assert.equal((await fingerprints(distPaths)).sha256,check.dist.sha256);
const result = { result:'通过',source,play,distFingerprint:check.dist.sha256,expandedBytes:check.dist.files.reduce((sum,file) => sum+file.bytes,0),checks:['源码ZIP实际提取','离线缓存npm ci清洁安装且禁用生命周期','源码ZIP重建与规则测试','重建逐文件字节一致','试玩ZIP CRC及逐文件字节一致','最终dist未修改'],installLog,buildLog,ruleLog };
await writeFile('evidence/release.json',JSON.stringify(result,null,2)+'\n');
await rm(root,{ recursive:true,force:true }); await rm('evidence/play-unpacked',{ recursive:true,force:true });
console.log('源码与试玩ZIP已生成；实际源码包清洁安装/重建通过，最终dist保持验收快照。');
