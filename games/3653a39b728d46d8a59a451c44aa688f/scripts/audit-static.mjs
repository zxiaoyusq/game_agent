// 仅分析已提取的研究副本；不执行参考游戏，不读取或修改主工程。
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const sourceBuffer = fs.readFileSync('reference-inputs/original-game.js');
assert.equal(hash(sourceBuffer), '2a036140fcf41e307b604373d307ff4014d061eef4bee5fb9504b90424b3460e');
const source = sourceBuffer.toString('utf8');
const literal = source.match(/var _0x1c9b5e = \[([\s\S]*?)\n  \];/)[1];
const table = [...literal.matchAll(/"(?:\\.|[^"\\])*"/g)].map(m => JSON.parse(m[0].replace(/\\x([0-9a-f]{2})/gi, '\\u00$1')));
// 由多个可见字面量交叉验证旋转偏移，不运行混淆初始化循环。
const shift = (table.indexOf('register') - (0x314 - 0xcf) + table.length) % table.length;
const lookup = index => table[(index - 0xcf + shift) % table.length];
for (const [index, expected] of [[0x314,'register'],[0x321,'step'],[0x182,'length'],[0x385,'Sprite'],[0x444,'down'],[0x43e,'pointerdown'],[0x215,'ticker'],[0x378,'renderer'],[0x383,'play']]) assert.equal(lookup(index), expected);
const aliases = new Set(['_0x3797']);
let changed = true;
while(changed) {
  changed = false;
  for (const m of source.matchAll(/(_0x[0-9a-f]+)\s*=\s*(_0x[0-9a-f]+)\s*[,;]/g)) {
    if(aliases.has(m[2]) && !aliases.has(m[1])) { aliases.add(m[1]); changed=true; }
  }
}
const decoded = source.replace(/(_0x[0-9a-f]+)\((0x[0-9a-f]+)\)/g, (all, name, value) => aliases.has(name) ? JSON.stringify(lookup(Number(value))) : all);
fs.mkdirSync('evidence',{recursive:true});
fs.writeFileSync('evidence/source-decoded.txt', decoded);
const registryText = decoded.slice(decoded.indexOf('bitmaps: {'), decoded.indexOf('    sprites: {'));
const declarations = [...registryText.matchAll(/^\s*(\w+):\s*("(?:\\.|[^"\\])*")/gm)].map(m=>({key:m[1],path:JSON.parse(m[2])}));
assert(declarations.length > 250);
const archiveNames = fs.readFileSync('workflow/archive-assets.txt','utf8').trim().split('\n');
assert.equal(archiveNames.length,321);
assert.equal(new Set(archiveNames).size,321);
const names = new Set(archiveNames.map(p=>'assets/'+p));
function imageSize(b) {
  if(b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))) return {format:'PNG',width:b.readUInt32BE(16),height:b.readUInt32BE(20)};
  if(b.toString('ascii',0,4)==='RIFF' && b.toString('ascii',8,12)==='WEBP') {
    for(let pos=12;pos+8<=b.length;) {
      const kind=b.toString('ascii',pos,pos+4), length=b.readUInt32LE(pos+4), at=pos+8;
      if(kind==='VP8X') return {format:'WebP',width:1+b.readUIntLE(at+4,3),height:1+b.readUIntLE(at+7,3)};
      if(kind==='VP8L') { const bits=b.readUInt32LE(at+1); return {format:'WebP',width:1+(bits&0x3fff),height:1+((bits>>>14)&0x3fff)}; }
      if(kind==='VP8 ') return {format:'WebP',width:b.readUInt16LE(at+6)&0x3fff,height:b.readUInt16LE(at+8)&0x3fff};
      pos=at+length+(length&1);
    }
  }
  throw Error('未知图像头，禁止猜测尺寸');
}
const samples = fs.readdirSync('reference-assets').filter(p=>p.endsWith('.png')).map(file=>{
  const bytes=fs.readFileSync('reference-assets/'+file);
  const relative=archiveNames.find(p=>p.split('/').at(-1)===file);
  assert(relative);
  return {path:'reference-assets/'+file,member:'www.excellenth5game.com/Carrom_Clash_Master/assets/'+relative,bytes:bytes.length,sha256:hash(bytes),...imageSize(bytes)};
});
function category(p) {
 if(p.includes('/sounds/')) return '音频';
 if(p.includes('/fonts/')) return '字体与动态文字依赖';
 if(p.includes('/sprites/')) return '独立动态效果帧表';
 if(/matchmaking_bg_.*_slices\.png/.test(p)) return '背景覆盖层（源码cover实例；不是多张切片）';
 if(/title_with_glow/.test(p)) return '静态图文（带光命名；须核查内嵌效果）';
 if(/glow|sfx|brights|lights|confetti|highlight|overlay|shadow|circle_around/.test(p)) return '独立效果（部分仅命名推断）';
 if(/tables\/\d\//.test(p)) return /background/.test(p)?'背景整图':/logo/.test(p)?'静态图文':'棋盘与边角组件';
 if(/Carrom_(black|white|red|strike)\.png|shop\/(stones\/stone_\d+|strike_\d+)/.test(p)) return '棋子或商品展示（需实例区分）';
 if(/button|ARROW_LEFT|ARROW_RIGHT|tableselect_arrow|shop_tab/.test(p)) return '独立可点击控件候选';
 if(/bg\.png|winner_background|preloader\/bg/.test(p)) return '背景整图';
 if(/text|title|label|tutorial\/\d_\d|starting\/[12]\.png|Congratulations/.test(p)) return '静态文字或教学图（不可当动态文字）';
 return '独立底板或图标（需实例核对）';
}
const inventory=archiveNames.map(relative=>{
 const path='assets/'+relative, rows=declarations.filter(d=>d.path===path), sample=samples.find(s=>s.member.endsWith('/'+path));
 const sourceLines=decoded.split('\n').flatMap((line,i)=>line.includes(JSON.stringify(path))?[i+1]:[]);
 return {member:'www.excellenth5game.com/Carrom_Clash_Master/'+path,category:category(path),priority:/tables\/|Carrom_(black|white|red|strike)|fonts\/|pause_button|loading_bar/.test(path)?'P0':/lobby|select|shop|pause|settings|preloader|tutorial|matchmaking/.test(path)?'P1':'P2',registry_keys:rows.map(r=>r.key),source_lines:sourceLines,reference_status:rows.length?'加载表声明；运行可达性未验证':sourceLines.length?'源码字符串存在；非加载表声明':'清单存在；所分析JS未见路径，不等于未使用',width:sample?.width??'UNKNOWN',height:sample?.height??'UNKNOWN',actual_format:sample?.format??'UNKNOWN',sha256:sample?.sha256??'UNKNOWN（未提取；以冻结ZIP逐条清单为准）',bytes:sample?.bytes??'UNKNOWN（以ZIP逐条清单为准）',dimension_status:sample?'已读实际图像头':'未提取，禁止推定同族尺寸',reuse:'保持原路径与状态；同族可共用风格母版，不直接合图或删件',evidence:'原包清单＋source_lines；声明不等于画面实例'};
});
const missing=declarations.filter(d=>!names.has(d.path));
// 对象字面量同名键采用最后一次声明；前面的缺路径不是实际加载失败。
const effectiveDeclarations=[...new Map(declarations.map(d=>[d.key,d])).values()];
const effectiveMissing=effectiveDeclarations.filter(d=>!names.has(d.path));
assert.equal(effectiveMissing.length,0);
const sourceLineArray=decoded.split('\n');
for(const row of inventory) {
 row.source='历史Carrom_Clash_Master.zip；仅作隔离核查引用，授权状态未核实';
 row.source_archive='mcp-inputs/mac-codex/2b404cd4b23702153c3279109bcd48bf79ee9e2141fc3334492a100c66036db2/Carrom_Clash_Master.zip';
 row.delivery_status='研究索引/待制作规格，不是已生成或可直接上线的换皮资源';
 row.alpha_bounds='UNKNOWN（未进行像素透明边界测量）';
 row.instance_candidate_lines=sourceLineArray.flatMap((line,i)=> i>=430 && i<12138 && row.registry_keys.some(key=>line.includes(JSON.stringify(key))) ? [i+1] : []);
 row.instance_status=row.instance_candidate_lines.length?'已定位键名引用候选；需按报告逐处核对':'无直接键名实例候选；可能通过配置间接引用';
 row.constraints=row.category.includes('效果')?'独立效果层，不并入控件可点击主体，保持帧/转轴与合成模式':row.category.includes('文字')?'动态数值不烘焙入整图；字体页和字距不可猜测':row.category.includes('棋')?'保持贴图几何、物理轮廓与原锚点；棋子身份独立可辨':'保持原画布尺寸、主体占位、锚点与各状态；未测尺寸不得用于生产';
}
const keyCounts = new Map();
for(const d of declarations) keyCounts.set(d.key,(keyCounts.get(d.key)||0)+1);
const duplicateKeys=[...keyCounts].filter(([,n])=>n>1).map(([key,count])=>({key,count,declarations:declarations.filter(d=>d.key===key)}));
fs.writeFileSync('workflow/resource-inventory.json',JSON.stringify({scope:'历史原包隔离静态分析，不是换皮集成清单',archive_sha256:'2b404cd4b23702153c3279109bcd48bf79ee9e2141fc3334492a100c66036db2',classification_status:'按命名和加载声明初分；实际可点击性和所有页面可达性未验证',assets:inventory},null,2));
fs.writeFileSync('evidence/static-audit.json',JSON.stringify({source_sha256:hash(sourceBuffer),decoded_sha256:hash(Buffer.from(decoded)),string_table_length:table.length,shift,verified_mapping_anchors:9,alias_count:aliases.size,archive_asset_count:archiveNames.length,registry_declaration_count:declarations.length,effective_registry_count:effectiveDeclarations.length,missing_in_shadowed_declarations:missing,effective_missing_registry_paths:effectiveMissing,duplicate_keys:duplicateKeys,samples,limitations:['未执行游戏','未读全部图像头','未验证网络、性能、交互、当前开发版','FNT读取被工具拒绝，字体页/字距未核对']},null,2));
console.log('静态核查完成：清单',archiveNames.length,'项；加载表',declarations.length,'条；实测图像',samples.length,'项；被覆盖声明的缺路径',missing.length,'条；有效加载表缺路径',effectiveMissing.length,'条。未执行游戏。');
