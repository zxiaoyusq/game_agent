import { readFile, mkdir, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

// 只核验美术文件契约；不模拟浏览器或游戏测试。
const svg = await readFile('public/assets/star.svg', 'utf8');
const config = JSON.parse(await readFile('public/assets/visual-config.json', 'utf8'));
const preview = await readFile('workflow/art-preview.html', 'utf8');
assert.match(svg, /width="64" height="64" viewBox="0 0 64 64"/);
assert.match(svg, /fill="#14B8A6" stroke="#0F766E"/);
assert.doesNotMatch(svg, /<(?:rect|image|script|foreignObject)\b|href=|style=|opacity=/i);
const points = svg.match(/points="([^"]+)"/)[1].split(' ').map(pair => pair.split(',').map(Number));
assert.equal(points.length, 10);
assert(points.flat().every(Number.isFinite));
// 描边半宽1：验证全部顶点和描边均在画布内，无图集、裁切或非等比变换。
assert(points.every(([x,y]) => x >= 1 && x <= 63 && y >= 1 && y <= 63));
assert.equal(config.star.displayWidthCss, config.star.displayHeightCss);
assert.equal(config.star.displayWidthCss, 56);
assert.equal(config.star.hitRadiusCss, 32);
assert(56 * 1.06 / 2 < config.star.safeInsetCss);
assert.equal(config.animation.durationMs, 160);
assert.deepEqual(config.animation.keyframes.map(frame => frame.scale), [0.9, 1.06, 1]);
assert.equal(config.positions.length, 5);
assert.equal(new Set(config.positions.map(position => JSON.stringify(position))).size, 5);
assert.match(preview, /\.\.\/public\/assets\/star\.svg/);
assert.doesNotMatch(preview, /<script|https?:\/\//);
const files = [];
for (const path of ['public/assets/star.svg', 'public/assets/visual-config.json', 'workflow/art-preview.html']) {
  const bytes = await readFile(path);
  files.push({ path, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') });
}
const result = { stage: 'art', result: '通过文件与几何静态核验', checks: ['64×64 viewBox', '青绿色及描边一致', '未绘制背景且无外部依赖', '五角顶点及描边无越界', '等比尺寸与峰值安全内边距', '动画配置及五位置', '静态预览引用真实资源'], files, limitations: ['未启动浏览器，未验证实际栅格透明度或视觉效果', '未执行动画、游戏输入或真机测试'] };
await mkdir('evidence', { recursive: true });
await writeFile('evidence/art-validation.json', JSON.stringify(result, null, 2) + '\n');
console.log('美术静态文件核验通过；结果写入 evidence/art-validation.json。未执行浏览器验收。');
