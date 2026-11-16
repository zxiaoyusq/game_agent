// 中文审查日志；只读取上传证据，不启动游戏、联网或修改原源码。
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { performance } = require('node:perf_hooks');
const refs = [
'mcp-inputs/mac-codex/68c66ea75685ded3fdac809a40fe16da0677249b23acb8867864a96b1a510cf9/fallback-before.js',
'mcp-inputs/mac-codex/d1c897bdd07c0a4221d40dd9c2d1d222c83670e355ac6024193d87cbcb1aaa9c/fallback-fullpath.js'];
// 平台 ref 不映射到 Node 文件系统；从用户补充 ZIP 逐件提取只读副本后再进行全文差分。
const supplied = process.argv.filter(p => !p.startsWith('--')).slice(2);
const inputs = supplied.length === 2 ? supplied : refs.map(p => path.join('ref', p));
const sources = inputs.map(p => fs.readFileSync(path.resolve(process.cwd(), p), 'utf8'));
fs.mkdirSync('evidence', { recursive: true });
function section(source, name) {
  const start = source.indexOf('    function ' + name + '(');
  assert(start >= 0, '函数不存在：' + name);
  const next = source.indexOf('\n    function ', start + 10);
  return { start, line: source.slice(0, start).split('\n').length, text: source.slice(start, next < 0 ? source.length : next) };
}
const names = ['_carromStartPathBlocked','_0x3d12d7','_carromFindOpenBaseline','_0x52106f','_0x25af2a','_0x521eef','_0x30849b','_0x3ea989','_0x50a0ff','_0x4b3cc6','_0x223471','_carromAiBoardChanged','_0x8b2762','_0x2bd695'];
const inventory = sources.map((s,i) => ({ path: inputs[i], originalReferencePath: 'ref/' + refs[i], bytes: Buffer.byteLength(s), sha256: crypto.createHash('sha256').update(s).digest('hex'), lines: s.split('\n').length, functions: names.map(n => ({ name:n, line:section(s,n).line, sha256:crypto.createHash('sha256').update(section(s,n).text).digest('hex') })) }));
let prefix=0; while(prefix < sources[0].length && sources[0][prefix] === sources[1][prefix]) prefix++;
let suffix=0; while(suffix < sources[0].length-prefix && sources[0].at(-1-suffix) === sources[1].at(-1-suffix)) suffix++;
const changed = names.filter(n => section(sources[0],n).text !== section(sources[1],n).text);
fs.writeFileSync('evidence/source-inventory.json', JSON.stringify({inventory,changed,prefix,suffix,node:process.version},null,2));
let excerpts='';
for (const name of names) if(changed.includes(name) || ['_0x8b2762','_0x2bd695'].includes(name)) for(let i=0;i<2;i++) excerpts += `\n### ${i===0?'变更前':'变更后'} ${name} 第${section(sources[i],name).line}行\n${section(sources[i],name).text}\n`;
fs.writeFileSync('evidence/source-excerpts.txt', excerpts);
// 按完整顶层函数边界切块，对两份全文进行顺序比较。
function blocks(s) { const starts=[0]; for(const m of s.matchAll(/\n    function /g)) starts.push(m.index+1); starts.push(s.length); return starts.slice(0,-1).map((a,i)=>({line:s.slice(0,a).split('\n').length,text:s.slice(a,starts[i+1])})); }
const a=blocks(sources[0]),b=blocks(sources[1]);
const differences=[];
assert.equal(a.length,b.length);
for(let i=0;i<a.length;i++) if(a[i].text!==b[i].text) differences.push({beforeLine:a[i].line,afterLine:b[i].line,before:a[i].text,after:b[i].text});
fs.writeFileSync('evidence/full-diff-blocks.json',JSON.stringify(differences,null,2));
// 仅以四项预期替换重构整份新文件，再逐字节比较；不执行参考源码。
const patches = [
 ['function _carromStartPathBlocked(origin, angle, length, intendedTarget)', 'function _carromStartPathBlocked(origin, angle, length, intendedTarget, fullFallbackPath)'],
 ['end = Math.min(length, _0x133600 * 2)', 'end = fullFallbackPath ? Math.max(0, length - (_0x133600 + 16)) : Math.min(length, _0x133600 * 2)'],
 ['_carromFallbackDistance, _0xe88441)', '_carromFallbackDistance, _0xe88441, true)'],
 ['_carromDistance, _0xe88441)', '_carromDistance, _0xe88441, true)']
];
let reconstructed=sources[0];
for(const [from,to] of patches){assert.equal(reconstructed.split(from).length-1,1);reconstructed=reconstructed.replace(from,to);}
assert(Buffer.from(reconstructed).equals(Buffer.from(sources[1])), '全文存在四项预期替换外的差异');
const regression=fs.readFileSync('scripts/fallback-regression.cjs','utf8');
const transcriptionMatch=regression.match(/const before = `([\s\S]*?)`;/);
assert(transcriptionMatch, '回归脚本中未找到几何转录文本');
const transcribed=transcriptionMatch[1];
const compact=s=>s.replace(/\s+/g,'');
assert.equal(compact(transcribed),compact(section(sources[0],'_carromStartPathBlocked').text));
assert.equal(compact(transcribed.replace(patches[0][0],patches[0][1]).replace(patches[1][0],patches[1][1])),compact(section(sources[1],'_carromStartPathBlocked').text));
fs.writeFileSync('evidence/exact-patch-proof.json',JSON.stringify({status:'PASS',inputPaths:inputs,byteDelta:Buffer.byteLength(sources[1])-Buffer.byteLength(sources[0]),patches,byteIdenticalAfterReconstruction:true,transcriptionMatchesIgnoringWhitespace:true,referenceCodeExecuted:false},null,2));
console.log('源码证据已落盘：'+JSON.stringify({changed,blocks:differences.length,exactPatch:true,inventory:inventory.map(x=>({bytes:x.bytes,sha256:x.sha256}))}));
if(process.argv.includes('--inventory')) process.exit(0);
