// 只读取已提取的工程数据；记录每个实际使用文件的来源、哈希和加工方式。
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { applyMove, isComplete, solve } from '../src/rules.mjs';
const project = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const root = path.resolve(project, '../..');
const ref = path.join(root, 'ref/BallSort工程拆解_2026-10-01');
const manifest = [];
function record(source, target, use, processing) {
  manifest.push({ source: path.relative(root, source), sha256: crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'), target, use, processing });
}
const data = {};
for (const product of ['guru', 'hm', 'infinite']) {
  const source = path.join(ref, product, 'analysis/normalized_levels.json');
  data[product] = JSON.parse(fs.readFileSync(source, 'utf8'));
  record(source, 'assets/levels.json', '可解关卡与特殊玩法', '去除零占位、统一管底到管口顺序，逐条回放验证');
}
function convert(row, product, label, hidden = false) {
  let board = row.tubes.map(tube => tube.filter(Boolean));
  if (product !== 'infinite') board = board.map(tube => tube.reverse());
  const capacity = row.capacity;
  let solution = row.steps;
  function verify(steps) {
    let current = board;
    for (const [a,b] of steps || []) { const next = applyMove(current,a,b,capacity); if (!next) return false; current = next.board; }
    return isComplete(current,capacity);
  }
  if (!verify(solution)) solution = solve(board,capacity,700000).solution;
  if (!solution || !verify(solution)) return null;
  return { id: `${product}:${row.group}:${row.id}`, product, label, capacity, board, solution, hidden, source: row.source };
}
// 开场即提供三色整理体验；随后按颜色数和解法长度平滑增加难度。
const classic = [];
for (const row of data.infinite.filter(row => row.group==='LevelAssetB/NormalLevelResources' && row.id>=3 && row.id<=6)) {
  const level = convert(row,'infinite','经典整理'); if (level) classic.push(level);
}
for (const row of data.guru.filter(row => row.group==='lv_1_100').slice(2)) {
  if (classic.length >= 100) break;
  const level = convert(row,'guru','经典整理'); if (level) classic.push(level);
}
const challenge = [];
for (const capacity of [6,8]) {
  let count=0;
  for (const row of data.hm.filter(row => row.capacity===capacity && row.steps?.length && row.tubes.length<=8)) {
    const level = convert(row,'hm','长管挑战'); if (level) {challenge.push(level);count++;}
    if (count >= 6) break;
  }
}
const mystery = classic.slice(4,24).map(level => ({...level,id:`mystery:${level.id}`,label:'迷雾实验',hidden:true}));
fs.writeFileSync(path.join(project,'public/assets/levels.json'),JSON.stringify({classic,challenge,mystery}));
// 三款参考各自提供一个可见的材质组，不重新分发整套提取物。
const assetConfig = { guru: ['ball01.png','ball02.png','ball03.png','ball04.png','ball05.png','ball06.png','ball07.png','ball08.png','ball09.png','ball10.png','ball11.png','ball12.png'], hm: ['tube_2.png'], infinite: ['Ui_Game_1Ball_01.png','Ui_Game_1Ball_02.png','Ui_Game_1Ball_03.png','Ui_Game_1Ball_04.png','Ui_Game_1Ball_05.png','Ui_Game_1Ball_06.png','Ui_Game_1Ball_07.png','Ui_Game_1Ball_08.png','Ui_Game_1Ball_09.png','Ui_Game_1Ball_10.png','Ui_Game_1Ball_11.png','Ui_Game_1Ball_12.png'] };
const assets = {};
for (const [product,names] of Object.entries(assetConfig)) {
  const folder = path.join(ref,product,'exports/Sprite'); const files=fs.readdirSync(folder);
  assets[product]=[];
  for (let index=0;index<names.length;index++) {
    const file=files.find(file=>file.endsWith(`__${names[index]}`)); if (!file) continue;
    const source=path.join(folder,file); const target=`assets/${product}-${index}.png`;
    fs.copyFileSync(source,path.join(project,'public',target)); assets[product].push(target);
    record(source,target,product==='hm'?'高管玻璃描边':'可切换球体材质', '仅等比缩放，由 Cocos Sprite 渲染；不修改原始像素');
  }
}
const audioFolder=path.join(ref,'hm/exports/AudioClip');
for (const [key,needle] of [['tap','touch-sound'],['complete','Full-tube'],['move','tick1']]) {
 const file=fs.readdirSync(audioFolder).find(file=>file.includes(needle)); const source=path.join(audioFolder,file);const target=`assets/${key}.wav`;
 fs.copyFileSync(source,path.join(project,'public',target));record(source,target,'真实游戏反馈音效','保留 WAV 内容，播放音量通过 Cocos AudioSource 控制');
}
fs.writeFileSync(path.join(project,'public/assets/asset-map.json'),JSON.stringify(assets));
// 静态反汇编仅用于确认职责边界，实际 JavaScript/Cocos 逻辑由本项目重新实现。
for(const [source,target,use] of [
 ['guru/code/native_core/01d448e8__BallSort.TubeData__CanImport.asm','src/rules.mjs','确认规则层包含管间导入合法性检查'],
 ['guru/code/native_core/01d411a0__BallSort.TubeData__get_TopBallSameCount.asm','src/rules.mjs','确认连续同色球计数职责，并用原始解法回放校验'],
 ['hm/code/native_core/0191a780__LevelSprite__UndoMove.asm','src/main.mjs','确认操作历史与撤销职责，使用不可变局面快照重写'],
 ['infinite/code/native_core/00cadda0__BallSort.Scripts.Core.Logic.Gaming.GameController.GameController__Hint.asm','src/solver-worker.mjs','确认提示为异步任务，本项目使用Worker离线求解'],
]) record(path.join(ref,source),target,use,'只分析静态方法边界与已知调用；不声称恢复完整原始源码');
for(const product of ['guru','hm','infinite']) record(path.join(ref,product,'unity_summary.json'),'evidence/fusion-design.md','确认原始Unity资源/脚本框架组成','作为迁移分析证据，运行时重建为真实Cocos');
fs.writeFileSync(path.join(project,'evidence/source-manifest.json'),JSON.stringify(manifest,null,2));
fs.writeFileSync(path.join(project,'evidence/level-validation.json'),JSON.stringify({classic:classic.length,challenge:challenge.length,challengeCapacities:{6:challenge.filter(level=>level.capacity===6).length,8:challenge.filter(level=>level.capacity===8).length},mystery:mystery.length,total:classic.length+challenge.length+mystery.length,allSolutionsReplayed:true,rule:'管底到管口；连续同色批量移动；容量约束；完成必须满管同色'},null,2));
console.log(`已逐关验证：经典${classic.length}、长管${challenge.length}、迷雾${mystery.length}；已记录${manifest.length}个来源文件`);
