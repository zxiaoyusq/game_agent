import { STORAGE_KEY, restore, saveData, collect, restart, targetPoint, isHit, animationScale } from './rules.js';

const canvas = document.querySelector('#board');
const context = canvas.getContext('2d');
const counter = document.querySelector('#counter');
const status = document.querySelector('#status');
const warning = document.querySelector('#warning');
const assetError = document.querySelector('#asset-error');
const retry = document.querySelector('#retry');
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
let state, config, image, width = 0, height = 0, active = null, animationStart = null, frame = 0, ready = false;
try {
  const result = restore(localStorage.getItem(STORAGE_KEY));
  state = result.state;
  if (result.invalid) warning.textContent = '存档无效，已开始新局。';
} catch {
  state = restore(null).state;
  warning.textContent = '进度无法保存，刷新后可能丢失';
}

function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saveData(state)));
    warning.textContent = '';
  } catch { warning.textContent = '进度无法保存，刷新后可能丢失'; }
}
function updateText() {
  counter.textContent = `${state.count} / 5`;
  status.textContent = state.phase === 'won' ? config?.copy.victory ?? '采集完成！' : '';
}
function target() { return targetPoint(state, width, height, config); }
function locked() { return animationStart !== null && performance.now() - animationStart < config.animation.durationMs; }
function draw(now = performance.now()) {
  frame = 0;
  if (!ready || document.hidden) return;
  let scale = 1;
  if (animationStart !== null) {
    const progress = (now - animationStart) / config.animation.durationMs;
    scale = animationScale(progress);
    if (progress >= 1) animationStart = null;
  }
  const dpr = Math.min(devicePixelRatio || 1, 3);
  context.setTransform(dpr, 0, 0, dpr, 0, 0);
  context.clearRect(0, 0, width, height);
  const point = target();
  const size = config.star.displayWidthCss * scale;
  context.drawImage(image, point.x - size / 2, point.y - size / 2, size, size);
  // 只读绘制诊断，便于验收连续帧；规则状态不从这些属性读取。
  canvas.dataset.scale = String(scale);
  canvas.dataset.ready = 'true';
  if (animationStart !== null) frame = requestAnimationFrame(draw);
}
function appear() {
  cancelAnimationFrame(frame);
  animationStart = reduced.matches || document.hidden ? null : performance.now();
  draw();
}
function resize() {
  active = null;
  const rect = canvas.getBoundingClientRect();
  width = rect.width; height = rect.height;
  const dpr = Math.min(devicePixelRatio || 1, 3);
  canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
  cancelAnimationFrame(frame); draw();
}
function localPoint(event) {
  const rect = canvas.getBoundingClientRect();
  return { x: (event.clientX - rect.left) * width / rect.width, y: (event.clientY - rect.top) * height / rect.height };
}
function allowed(event) { return ready && !document.hidden && state.phase === 'playing' && !locked() && event.isPrimary && event.button === 0; }
// 主指针按下及释放均命中才提交；拖出后不允许拖回补点。
canvas.addEventListener('pointerdown', event => {
  if (active || !allowed(event) || !isHit(localPoint(event), target(), config.star.hitRadiusCss)) return;
  active = { id: event.pointerId, roundId: state.roundId, targetIndex: state.targetIndex };
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener('pointermove', event => {
  if (active?.id === event.pointerId && !isHit(localPoint(event), target(), config.star.hitRadiusCss)) active = null;
});
canvas.addEventListener('pointerup', event => {
  const pending = active;
  if (pending?.id !== event.pointerId) return;
  active = null;
  if (!allowed(event) || pending.roundId !== state.roundId || pending.targetIndex !== state.targetIndex || !isHit(localPoint(event), target(), config.star.hitRadiusCss)) return;
  state = collect(state); save(); updateText(); appear();
});
for (const name of ['pointercancel', 'lostpointercapture']) canvas.addEventListener(name, event => {
  if (active?.id === event.pointerId) active = null;
});
document.querySelector('#restart').addEventListener('click', () => {
  active = null; state = restart(state); save(); updateText(); if (ready) appear();
});
document.addEventListener('visibilitychange', () => {
  active = null; cancelAnimationFrame(frame); animationStart = null;
  if (!document.hidden) draw();
});
reduced.addEventListener('change', () => { active = null; animationStart = null; cancelAnimationFrame(frame); draw(); });
new ResizeObserver(resize).observe(canvas);

async function loadAssets() {
  ready = false; canvas.dataset.ready = 'false'; retry.hidden = true; assetError.hidden = true;
  try {
    const response = await fetch('./assets/visual-config.json');
    if (!response.ok) throw Error('配置请求失败');
    config = await response.json();
    image = new Image(); image.src = config.star.asset;
    await image.decode();
    ready = true; resize(); updateText(); appear();
  } catch {
    assetError.hidden = false; retry.hidden = false;
  }
}
retry.addEventListener('click', loadAssets);
updateText(); loadAssets();
