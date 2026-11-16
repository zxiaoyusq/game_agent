// 对已写入的最终美术清单做独立只读校验，不改素材或预览。
const fs=require('node:fs');const crypto=require('node:crypto');
const manifest=JSON.parse(fs.readFileSync('workflow/art-manifest.json','utf8'));
if(!Array.isArray(manifest.assets)||!manifest.assets.length)throw Error('美术清单为空');
const seen=new Set();
for(const a of manifest.assets){for(const k of ['path','sha256','usage','source'])if(typeof a[k]!=='string'||!a[k].trim())throw Error('清单字段不是非空字符串：'+k);if(seen.has(a.path))throw Error('重复路径');seen.add(a.path);const data=fs.readFileSync(a.path);if(!data.length||crypto.createHash('sha256').update(data).digest('hex')!==a.sha256)throw Error('文件哈希不符：'+a.path);}
if(!manifest.assets.some(a=>/\.(png|webp)$/.test(a.path)))throw Error('缺少真实图片');
const result={stage:'art',manifestEntries:manifest.assets.length,allFilesNonEmpty:true,allHashesMatch:true,requiredFieldsValid:true,limitations:['仅文件清单校验，非浏览器或游戏验收']};
fs.writeFileSync('evidence/art-manifest-check.json',JSON.stringify(result,null,2));
console.log('最终美术清单校验通过：'+manifest.assets.length+'项，所有文件非空、字段有效、当前SHA256匹配。');
