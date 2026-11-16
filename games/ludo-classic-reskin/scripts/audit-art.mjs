import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';

// 仅美术资产对账与Canvas配置序列化，不构建游戏、不执行参考源码、不处理图片。
const load = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const hash = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const spec = load('design/art-resource-spec.json');
const index = load('reference-assets/research-index.json');
const dice = load('reference-assets/research-dice-frames.json');
const runtime = load('reference-assets/research-board-runtime.json');
const root = 'public/assets/';
const reuse = load('design/reuse-baseline.json');
for (const item of reuse.files) assert.equal(hash(item.path), item.sha256, `上游核心已改变${item.path}`);
const upstream = [...reuse.files.map(f => f.path), 'workflow/prototype.md', 'design/visual-baseline.md', 'design/acceptance.md', 'design/reuse-baseline.json'].map(p => ({path:p,sha256:hash(p)}));
const assets = [];
function add(file, usage, source, classification, geometry = {}) {
  const p = root + file;
  const bytes = fs.readFileSync(p);
  const entry = {path:p, runtime_path:'assets/' + file, sha256:hash(p), bytes:bytes.length, usage, source, classification, input_format:file.endsWith('.png') ? 'WEBP' : 'MP3', ...geometry};
  if (file.endsWith('.png')) {
    assert.equal(bytes.subarray(0,8).toString('hex'), '89504e470d0a1a0a', `${file}不是PNG编码`);
    entry.output_format = 'PNG';
    entry.size = [bytes.readUInt32BE(16), bytes.readUInt32BE(20)];
    entry.png_color_type = bytes[25];
    assert.equal(entry.png_color_type, 6, `${file}未保留RGBA`);
    if (geometry.expectedSize) assert.deepEqual(entry.size, geometry.expectedSize, `${file}尺寸不一致`);
    delete entry.expectedSize;
  } else entry.output_format = 'MP3';
  assert(!assets.some(a => a.path === p), `重复资源${p}`);
  assets.push(entry);
  return entry;
}
const source = (native, metadata, more={}) => ({archive:spec.archive, archive_sha256:spec.archive_sha256, member:spec.prefix + native, ...(metadata ? {metadata_member:spec.prefix + metadata}:{}), origin:'用户提供参考库，未独立核实商业授权', ...more});
const bg = spec.background;
assert.equal(hash(bg.reference), bg.reference_sha256, '生图参考哈希改变');
assert.equal(hash(bg.input), bg.candidate_sha256, '原候选哈希改变');
assert.equal(hash(root + bg.file), bg.final_sha256, '最终背景哈希改变');
add(bg.file, bg.usage, {...source('loading/assets/resources/native/51/5115ecbc-d727-4655-84ac-e700038972d5.b2713.png','loading/assets/resources/import/04/04afb2abe.9a5b4.json',{original_frame:'original_img_beijing', original_crop:[1,1,719,1600]}), method:'真实参考编辑后确定性裁切等比装配', provider:bg.provider, model:bg.model, reference:bg.reference, reference_sha256:bg.reference_sha256, original_candidate:bg.input, original_candidate_sha256:bg.candidate_sha256, crop:bg.crop, target_size:bg.target_size, prompt:bg.prompt}, 'api-edited', {expectedSize:[719,1600], originalSize:[719,1600], offset:[0,0], anchor:[0.5,0.5], draw_mode:'full-canvas', alpha_extrema:bg.alpha_extrema});
for (const item of spec.crops) {
  const atlas = index.atlases.find(a => a.role === spec.atlas_keys[item.atlas]);
  assert(atlas, '缺少图集证据');
  assert.equal(hash(spec.atlas_inputs[item.atlas]), atlas.sha256, '图集源哈希改变');
  const frames = index.frames.map(f => f.frame).concat(runtime.assets ?? []);
  assert(frames.some(f => f.name === item.frame && JSON.stringify(f.rect) === JSON.stringify(item.rect)), `缺少已读帧规格${item.frame}`);
  add(item.file, item.usage, source(atlas.entry.slice(spec.prefix.length), item.metadata ?? atlas.metadata.slice(spec.prefix.length), {atlas_sha256:atlas.sha256, original_frame:item.frame, method:'原版imported图集精确crop后processed PNG，无旋转无缩放'}), 'processed', {expectedSize:item.rect.slice(2), source_rect:item.rect, originalSize:item.originalSize ?? item.rect.slice(2), offset:item.offset ?? [0,0], rotated:false, capInsets:[0,0,0,0], anchor:[0.5,0.5], draw_mode:item.originalSize ? 'trimmed-sprite' : 'full-canvas'});
}
for (const item of spec.hud) {
  const original = index.hud.assets.find(a => a.name === item.frame);
  assert(original, `缺少HUD证据${item.frame}`);
  assert.equal(hash(root + item.input), original.native_sha256, 'HUD源哈希改变');
  add(item.file, item.usage, source(original.native_entry.slice(spec.prefix.length), original.metadata_entry.slice(spec.prefix.length), {native_sha256:original.native_sha256, original_frame:original.name, method:'原版imported native整画布规范为processed PNG，不trim不缩放'}), 'processed', {expectedSize:original.native_size, source_rect:original.rect, originalSize:original.originalSize, source_offset:original.offset, offset:[0,0], rotated:false, capInsets:original.capInsets, anchor:[0.5,0.5], draw_mode:'full-canvas'});
}
for (const item of spec.standalone) add(item.file, item.usage, source(item.native, item.metadata, {native_sha256:hash(item.input), original_frame:item.frame, method:'原版imported native整画布规范为processed PNG'}), 'processed', {expectedSize:item.originalSize, originalSize:item.originalSize, source_rect:item.rect, source_offset:item.offset, offset:[0,0], capInsets:item.capInsets, rotated:false, anchor:[0.5,0.5], draw_mode:'full-canvas'});
for (const n of spec.roll.unique) {
  const label = String(n).padStart(2,'0');
  const frame = dice.frames.find(f => f.name === `合成_000${label}`);
  assert(frame, '缺少摇骰原帧');
  assert.equal(hash(root + `dice-roll-${label}.png`), frame.sha256, '摇骰源帧改变');
  add(`roll-${label}.png`, `${spec.roll.usage}；像素帧${label}`, source(frame.native_entry.slice(spec.prefix.length), dice.clip_entry.slice(spec.prefix.length), {native_sha256:frame.sha256, original_frame:frame.name, method:'整幅220×220 native规范为PNG，未二次trim'}), 'processed', {expectedSize:[220,220], originalSize:[220,220], source_rect:frame.rect, source_offset:frame.offset, offset:[0,0], anchor:[0.5,0.5], rotated:false, capInsets:frame.capInsets, draw_mode:'full-canvas'});
}
for (const item of spec.audio) add(item.file, item.usage, source(item.native, null, {method:'原版imported音频逐件提取，源字节未改'}), 'imported');
const sequence = spec.roll.sequence.map((n,i) => {
  const original = dice.frames.find(f => f.name === `合成_000${String(i).padStart(2,'0')}`);
  const shared = dice.frames.find(f => f.name === `合成_000${String(n).padStart(2,'0')}`);
  assert.equal(original.sha256, shared.sha256, '错误去重摇骰帧');
  return {frameIndex:i, time_seconds:i / 30, path:`assets/roll-${String(n).padStart(2,'0')}.png`, original_frame:original.name, source:source(original.native_entry.slice(spec.prefix.length), dice.clip_entry.slice(spec.prefix.length), {native_sha256:original.sha256}), source_rect:original.rect, source_offset:original.offset, originalSize:original.originalSize, draw_mode:'full-canvas'};
});
const P = [[13,6],[12,6],[11,6],[10,6],[9,6],[8,5],[8,4],[8,3],[8,2],[8,1],[8,0],[7,0],[6,0],[6,1],[6,2],[6,3],[6,4],[6,5],[5,6],[4,6],[3,6],[2,6],[1,6],[0,6],[0,7],[0,8],[1,8],[2,8],[3,8],[4,8],[5,8],[6,9],[6,10],[6,11],[6,12],[6,13],[6,14],[7,14],[8,14],[8,13],[8,12],[8,11],[8,10],[8,9],[9,8],[10,8],[11,8],[12,8],[13,8],[14,8],[14,7],[14,6]];
assert.equal(new Set(P.map(v => v.join(','))).size,52);
const board = {
  coordinate_source:'workflow/prototype.md 第3节为逻辑映射真源；原场景坐标仅作分层纹理装配',
  prototype_grid:{scene:[360,600], rect:[12,126,336,336], rows:15, cols:15, cellSize:22.4, public_path:P, safe:[0,8,13,21,26,34,39,47], stars:[8,21,34,47], arrows:[0,13,26,39], private_paths:[[[13,7],[12,7],[11,7],[10,7],[9,7],[8,7]],[[7,1],[7,2],[7,3],[7,4],[7,5],[7,6]],[[1,7],[2,7],[3,7],[4,7],[5,7],[6,7]],[[7,13],[7,12],[7,11],[7,10],[7,9],[7,8]]]},
  source_assembly:{axes:'x右y上，Canvas统一翻y', center:{path:'assets/board-cross.png', position:[0.639,-20], size:[586,585]}, frame:{path:'assets/board-frame.png', position:[0,-29], size:[628,628], alpha_extrema:[0,51]}, camps:[{owner:0,color:'blue',position:[-175,-197],holes:[[-215,-157],[-137,-157],[-215,-237],[-137,-237]]},{owner:1,color:'red',position:[-175,156],holes:[[-215,196],[-137,196],[-215,119],[-137,119]]},{owner:2,color:'green',position:[176,156],holes:[[138,196],[217,196],[138,119],[217,119]]},{owner:3,color:'yellow',position:[176,-197],opacity:250,holes:[[138,-157],[217,-157],[138,-237],[217,-237]]}], campSize:[233,233], original_map_scale:1.15, apply_map_scale:false, layer_order:['background','frame','camps','cross','stars/arrows','landing/selection','pieces','HUD','local-effects']},
  arrow_decision:{original_runtime:[50,11,24,37], project:[0,13,26,39], policy:'服从已确认原型；原箭头纹理用于项目出营点，位置不是原版逐像素复刻'},
  piece_anchor:{source_node:[0.5,0.5], render_basis:'以底座中心锚定逻辑格，不以全图中心锚格；营地原场景位置是源节点中心', proposed_base_uv:[0.5,0.82], status:'底座uv是美术设计建议，非源SpriteFrame元数据；集成时用截图核验，不修改图像字节'},
  display_policy:'用同一棋盘变换定位所有部件；十字有效网格用586×585独立层标定，外框628不得作为15格宽；不重复应用原map scale1.15'
};
const visual = {version:1, framework:'Canvas 2D', stage:'美术交接，尚未运行集成', assets, board, hud:{source_player_info:[231,174], seatSize:[146,146], source_seat_position:[0,11], source_avatar_position:[0,9], source_dice_button_size:[75,75], source_dice_button_position:[0,11], source_dice_node_position:[-5,9], anchor:[0.5,0.5], placement:'红绿上方44…118，蓝黄下方470…544；原局部HUD坐标统一翻y并整体等比缩小，不把146按CSS像素直接铺满', min_css_hit:44}, dice:{fps:30,duration_ms:spec.roll.duration_ms,originalSize:[220,220],excluded_negative_frame:'dice0@-0.133333秒',sequence, face_draw_formula:'中心锚点x,y：左=x-110*s+62*s，顶=y-110*s+54*s，绘104*s×106*s；trim offset原[4,3]，Canvas y反号。摇骰整图左x-110*s、顶y-110*s，不套该偏移', result_source:'已提交ROLL，不由贴图决定随机'}, effects:{mode:'procedural', classification:'procedural', implementation_status:'本阶段只交接非空设计，不声称已实现动画', design:'design/art-integration.md', design_sha256:hash('design/art-integration.md'), walk_ms_per_cell:110, arc_height_cells:[0.25,0.4], walk_scale_peak:1.15,capture_impact_ms:100,capture_reverse_ms_per_cell:30,capture_final_ms:100,home_ms:375,victory_ms:1000,breathing_ms:1400}, audio:{unlock:'首自然交互',mute:'设置可关闭',cancel:'隐藏/暂停/重开立即停止',win_sound:null}, package_policy:{only_assets_allowlist:assets.map(a=>a.runtime_path), additional_config:['assets/visual-manifest.json'], excluded:'旧格式原件、候选、背景母版、图集、reference-assets、reference-inputs、拒绝背景均不自动复制', total_dist_max_bytes_exclusive:10000000}};
assert.equal(assets.length,58, '资源数异常');
fs.mkdirSync('workflow',{recursive:true});
fs.mkdirSync('evidence',{recursive:true});
// 平台简表要求四个字段均为非空字符串；完整来源对象另存，不改变运行配置。
const manifest = {assets:assets.map(a => ({
  path:a.path,
  sha256:a.sha256,
  usage:a.usage,
  source:[
    `源ZIP：${a.source.archive}`,
    `成员：${a.source.member}`,
    a.source.original_frame ? `原帧：${a.source.original_frame}` : null,
    a.source.method,
    a.source.reference ? `工程图片API参考编辑：${a.source.reference}（${a.source.provider}/${a.source.model}）` : null,
    a.source.origin
  ].filter(Boolean).join('；'),
  source_details:a.source,
  classification:a.classification
}))};
for (const item of manifest.assets) {
  for (const field of ['path','sha256','usage','source']) {
    assert(typeof item[field] === 'string' && item[field].trim().length > 0, `${item.path}的${field}必须为非空字符串`);
  }
}
// 补正不能改变58件资源的路径、顺序或哈希。
const identities = list => list.map(({path,sha256}) => ({path,sha256}));
assert.deepEqual(identities(manifest.assets), identities(load('workflow/art-manifest.json').assets), '正式资源与既有清单不一致');
fs.writeFileSync('workflow/art-manifest.json', JSON.stringify(manifest,null,2)+'\n');
fs.writeFileSync(root+'visual-manifest.json', JSON.stringify(visual,null,2)+'\n');
const evidence = {stage:'art',command:'node scripts/audit-art.mjs',passed:true,scope:'PNG签名、RGBA编码、尺寸、源哈希、25帧去重时序、路径和非空清单对账；非浏览器/动画/音频播放验证',asset_count:assets.length,image_count:assets.filter(a=>a.output_format==='PNG').length,audio_count:4,asset_bytes:assets.reduce((s,a)=>s+a.bytes,0),config_bytes:fs.statSync(root+'visual-manifest.json').size,files:assets.map(({path,sha256,bytes,size,output_format,png_color_type})=>({path,sha256,bytes,size,output_format,png_color_type})),upstream_files:upstream,source_artifacts:['design/art-resource-spec.json','reference-assets/research-index.json','reference-assets/research-dice-frames.json','reference-assets/research-board-runtime.json'].map(p=>({path:p,sha256:hash(p)})),outputs:['workflow/art-manifest.json',root+'visual-manifest.json'].map(p=>({path:p,sha256:hash(p)})),not_executed:['npm run build','npm test','npm run check','真机验收','部署','商业授权核实']};
fs.writeFileSync('evidence/art-audit.json',JSON.stringify(evidence,null,2)+'\n');
console.log(`美术对账通过：${assets.length}件，PNG ${evidence.image_count}件，音频4件，资产${evidence.asset_bytes}字节；不代表游戏或音频播放验收。`);
