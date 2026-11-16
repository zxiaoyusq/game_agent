// 只读诊断：不执行游戏源码、不加载联网依赖，只记录锚点与静态证据。
const fs = require('node:fs');
const crypto = require('node:crypto');
const path = 'ref/mcp-inputs/mac-codex/98cdce5f52ad498f6aea9fabb86f9c9020ad7b5c594c9cd6c1ac9dd03a769262/Carrom_ai_force_98cdce5f.js';
const text = fs.readFileSync(path, 'utf8');
const lines = text.split('\n');
const needles = ['function _0x50a0ff','function _0xd6b627','function _0x4662ac','function _0x223471','function _0x4b3cc6','function _0x3d12d7','function _carromAiBoardChanged','function _0x52106f','function _0x25af2a','function _0x521eef','function _0x30849b','function _0x3ea989','function _0x49d791','function _0x4bf21a','function _0x338c29','function _0x3f3a','function _0x3797','_0x13fb80 =','_0x902691 =','_0x54e9a5 =','_0x301cde =','_0x18e0e1 =','_0x647bf3 =','function _0x5480e3','function _0x5e0129','function _0x1e39ba','function _0x56abf7','function _0xbdafb3'];
const anchors = needles.map(needle => ({needle, lines:lines.flatMap((line,index) => line.includes(needle) ? [index+1] : [])}));
const result = {source:path, sha256:crypto.createHash('sha256').update(text).digest('hex'),bytes:Buffer.byteLength(text),lineCount:lines.length,anchors};
fs.mkdirSync('evidence',{recursive:true});
fs.writeFileSync('evidence/source-anchors.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
// 只输出发射器与相关属性附近原文，保留原始行号。
for (const needle of ['_0x13fb80 =','_0x902691 =','_0x54e9a5 =','function _0x3f3a','function _0x3797']) {
 const index=lines.findIndex(line=>line.includes(needle));
 if(index>=0) console.log(lines.slice(index,index+430).map((line,j)=>`${index+j+1}: ${line}`).join('\n'));
}
