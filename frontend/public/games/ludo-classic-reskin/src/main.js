import { createMatch, dispatch, makeAction, legalMoves, ownersFor } from './rules.js';
import { chooseMove } from './ai.js';
import { freshSeed, seedFromSearch } from './rng.js';
import { loadMatch, SaveStore, SETTINGS_KEY } from './storage.js';
import { TaskGate } from './lifecycle.js';
import { loadAssets, createAudio } from './assets.js';
import { geometry, seats, labels } from './map.js';
import { createTimeline } from './timeline.js';
import { createRenderer } from './render.js';

const element = (id) => document.getElementById(id);
const canvas = element('game');
const scene = element('scene');
const controls = element('controls');
const menu = element('menu');
const settingsPanel = element('settings');
const timeline = createTimeline();
const gate = new TaskGate();
const audio = createAudio();
let io;
try {
  io = localStorage;
} catch {
  io = {
    getItem() {
      throw Error('存储被禁用');
    },
    setItem() {
      throw Error('存储被禁用');
    },
    removeItem() {
      throw Error('存储被禁用');
    },
  };
}
const store = new SaveStore(io);
const restored = loadMatch(io);
let state = null;
let ready = false;
let renderer;
let geo;
let scale = 1;
let paused = false;
let sample = null;
let events = [];
let visibility = [];
let settings = { mute: false, reduced: false };
let settingsError = null;
try {
  const saved = JSON.parse(io.getItem(SETTINGS_KEY) || 'null');
  if (saved) settings = { mute: saved.mute === true, reduced: saved.reduced === true };
} catch {
  settingsError = '设置无法保存或读取';
}
let message = restored.error || seedFromSearch(location.search).error || '';

function isPaused() {
  return paused || document.hidden || !settingsPanel.hidden || !menu.hidden;
}
function busy() {
  return timeline.active !== null;
}
function observe() {
  // 每次返回隔离副本；没有任何改变棋盘、骰子或胜者的测试入口。
  return structuredClone({
    state,
    ready,
    busy: busy(),
    paused: isPaused(),
    settings,
    legal: state ? legalMoves(state) : [],
    animation: sample,
    events,
    visibility,
    positions: renderer?.positions || [],
    epoch: timeline.epoch,
  });
}
Object.defineProperty(window, 'ludo', {
  value: Object.freeze({ observe }),
  writable: false,
});
function eventRecord(kind, stage, now, extra = {}) {
  events.push({
    matchId: state?.matchId,
    revision: state?.revision,
    epoch: timeline.epoch,
    kind,
    stage,
    time: now,
    ...extra,
  });
  if (events.length > 1800) events.splice(0, events.length - 1800);
}
function cancel(reason) {
  const old = timeline.cancel();
  if (old)
    eventRecord(old.clips[old.index].kind, 'cancel', performance.now(), { reason });
  sample = null;
  gate.cancel();
  audio.stop();
  syncControls();
}
function humanAllowed() {
  return (
    state &&
    !isPaused() &&
    !busy() &&
    state.seats.find((s) => s.owner === state.currentPlayer)?.type === 'human'
  );
}
function commit(type, pieceId, ai = false) {
  if (!state || isPaused() || busy()) return;
  const isAi = state.seats.find((s) => s.owner === state.currentPlayer).type === 'ai';
  if (isAi !== ai) return;
  const before = state;
  const result = dispatch(state, makeAction(state, type, pieceId));
  if (!result.ok) return;
  gate.cancel();
  state = result.state;
  store.save(state); // 规则事务只提交一次，先保存，再只读演出。
  if (!settings.reduced) {
    timeline.start(before, state, geo, performance.now());
    audio.play(type === 'ROLL' ? 'roll' : 'step');
  }
  syncControls();
  scheduleAi();
}
function scheduleAi() {
  gate.cancel();
  if (!state || state.phase === 'finished' || busy() || isPaused()) return;
  if (state.seats.find((s) => s.owner === state.currentPlayer).type !== 'ai') return;
  gate.schedule(
    state,
    settings.reduced ? 10 : 450,
    (stamp) =>
      state &&
      !busy() &&
      !isPaused() &&
      ['matchId', 'revision', 'phase'].every((k) => stamp[k] === state[k]),
    () => {
      if (state.phase === 'awaitRoll') commit('ROLL', null, true);
      else commit('MOVE', chooseMove(state)?.pieceId, true);
    },
  );
}
function button(id, label, handler, className = '') {
  const b = document.createElement('button');
  b.id = id;
  b.type = 'button';
  b.setAttribute('aria-label', label);
  b.className = className;
  b.addEventListener('click', () => {
    audio.unlock();
    handler();
  });
  controls.append(b);
  return b;
}
const settingsButton = button('settings-button', '设置', () => {
  settingsPanel.hidden = false;
  cancel('settings');
  syncControls();
  element('close').focus();
});
const pauseButton = button('pause', '暂停', () => {
  paused = !paused;
  if (paused) cancel('pause');
  syncControls();
  scheduleAi();
});
pauseButton.textContent = '暂停';
const diceButtons = seats.map((_, owner) =>
  button(`dice-${owner}`, `${labels[owner]}队掷骰`, () => {
    if (state?.currentPlayer === owner) commit('ROLL');
  }),
);
const pieceButtons = Array.from({ length: 4 }, (_, i) => {
  const b = button(
    `piece-${i + 1}`,
    `选择棋子${i + 1}`,
    () => commit('MOVE', `${state?.currentPlayer}:${i + 1}`),
    'piece',
  );
  b.textContent = String(i + 1);
  return b;
});
const again = button('again', '再来一局', () => reset());
function place(b, x, y, w = 44, h = 44) {
  const width = Math.max(44, w * scale),
    height = Math.max(44, h * scale);
  Object.assign(b.style, {
    left: `${x * scale - width / 2}px`,
    top: `${y * scale - height / 2}px`,
    width: `${width}px`,
    height: `${height}px`,
  });
}
function resize() {
  scale = Math.min(document.body.clientWidth / 360, document.body.clientHeight / 600);
  scene.style.width = `${360 * scale}px`;
  scene.style.height = `${600 * scale}px`;
  const dpr = Math.min(2, devicePixelRatio || 1);
  canvas.width = Math.round(360 * dpr);
  canvas.height = Math.round(600 * dpr);
  place(settingsButton, 332, 24);
  place(pauseButton, 31, 24);
  seats.forEach((s, i) => place(diceButtons[i], s.diceX, s.y, 52, 52));
  pieceButtons.forEach((b, i) => place(b, 99 + i * 54, 575));
  place(again, 180, 318, 140, 50);
}
window.addEventListener('resize', resize);
function syncControls() {
  if (!renderer) return;
  const available = humanAllowed();
  const moves = state ? legalMoves(state) : [];
  settingsButton.hidden = !menu.hidden;
  pauseButton.hidden = !menu.hidden;
  pauseButton.textContent = paused ? '继续' : '暂停';
  pauseButton.setAttribute('aria-label', paused ? '继续' : '暂停');
  diceButtons.forEach((b, i) => {
    b.hidden =
      !state ||
      !state.seats.some((s) => s.owner === i) ||
      !menu.hidden ||
      !settingsPanel.hidden;
    b.setAttribute(
      'aria-disabled',
      String(!available || state.currentPlayer !== i || state.phase !== 'awaitRoll'),
    );
  });
  pieceButtons.forEach((b, i) => {
    b.hidden =
      !state ||
      i >= (state.mode === 'classic' ? 4 : 2) ||
      !menu.hidden ||
      !settingsPanel.hidden ||
      state.phase === 'finished';
    b.setAttribute(
      'aria-disabled',
      String(
        !available || !moves.some((m) => m.pieceId === `${state.currentPlayer}:${i + 1}`),
      ),
    );
  });
  again.hidden =
    !state ||
    state.phase !== 'finished' ||
    busy() ||
    !settingsPanel.hidden ||
    !menu.hidden;
  const next = !state
    ? '选择模式与人数'
    : state.phase === 'finished'
      ? `${labels[state.winner]}队获胜`
      : `${labels[state.currentPlayer]}队 · ${busy() ? '演出中' : state.phase === 'awaitRoll' ? '请掷骰' : `骰子${state.dice} · 选择棋子`}`;
  element('status').textContent = next;
  element('error').textContent = [store.error, settingsError, message]
    .filter(Boolean)
    .join(' · ');
}
function start(resume = false) {
  // 原生disabled负责界面，ready负责处理器；资源未齐不能创建或恢复局面。
  if (!ready || (resume && !restored.state)) return;
  audio.unlock();
  cancel('start');
  state = resume
    ? structuredClone(restored.state)
    : createMatch({
        mode: element('mode').value,
        seats: ownersFor(Number(element('count').value)).map((owner, i) => ({
          owner,
          type: element('players').value === 'ai' && i > 0 ? 'ai' : 'human',
        })),
        seed: seedFromSearch(location.search).seed ?? freshSeed(),
        matchId: crypto.randomUUID(),
      });
  store.save(state);
  paused = false;
  menu.hidden = true;
  settingsPanel.hidden = true;
  syncControls();
  scheduleAi();
}
function reset() {
  cancel('restart');
  state = null;
  paused = false;
  menu.hidden = false;
  settingsPanel.hidden = true;
  element('resume').hidden = true;
  syncControls();
  element('start').focus();
}
element('retry').addEventListener('click', () => location.reload());
element('start').addEventListener('click', () => start());
element('resume').hidden = !restored.state;
element('resume').addEventListener('click', () => start(true));
element('close').addEventListener('click', () => {
  audio.unlock();
  settingsPanel.hidden = true;
  syncControls();
  scheduleAi();
  settingsButton.focus();
});
element('restart').addEventListener('click', reset);
for (const id of ['mute', 'reduced']) {
  element(id).checked = settings[id];
  element(id).addEventListener('change', () => {
    settings[id] = element(id).checked;
    audio.mute(settings.mute);
    try {
      io.setItem(SETTINGS_KEY, JSON.stringify(settings));
      settingsError = null;
    } catch {
      settingsError = '设置未保存';
    }
    if (id === 'reduced') cancel('reduced');
    syncControls();
  });
}
audio.mute(settings.mute);
// Pointer单入口；只命中真实棋子尺寸，叠子用编号按钮选择，不扩大重叠触区。
let pointer = null;
canvas.addEventListener('pointerdown', (event) => {
  audio.unlock();
  if (!event.isPrimary || event.button !== 0) {
    pointer = null;
    return;
  }
  pointer = { id: event.pointerId, x: event.clientX, y: event.clientY };
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener('pointercancel', () => {
  pointer = null;
});
canvas.addEventListener('pointerup', (event) => {
  const down = pointer;
  pointer = null;
  if (
    !down ||
    down.id !== event.pointerId ||
    Math.hypot(event.clientX - down.x, event.clientY - down.y) > 8 ||
    !humanAllowed()
  )
    return;
  const rect = canvas.getBoundingClientRect();
  const x = (event.clientX - rect.left) / scale,
    y = (event.clientY - rect.top) / scale;
  const hits = renderer.positions.filter(
    (p) =>
      Math.abs(p.x - x) < p.width / 2 &&
      y > p.y - p.height * 0.82 &&
      y < p.y + p.height * 0.18 &&
      legalMoves(state).some((m) => m.pieceId === p.pieceId),
  );
  if (hits.length === 1) commit('MOVE', hits[0].pieceId);
  else if (hits.length > 1) {
    message = '叠子请使用底部编号选择';
    syncControls();
  }
});
document.addEventListener('visibilitychange', (event) => {
  visibility.push({
    time: performance.now(),
    hidden: document.hidden,
    isTrusted: event.isTrusted,
  });
  if (visibility.length > 40) visibility.shift();
  if (document.hidden) cancel('hidden');
  else {
    syncControls();
    scheduleAi();
  }
});
window.addEventListener('pagehide', () => cancel('pagehide'));

function frame(now) {
  sample = timeline.sample(now);
  const active = timeline.active;
  renderer.render(state, active, sample, now, settings.reduced, isPaused());
  // 观测在真实Canvas绘制后产生，不能代替像素与截图验证。
  if (active && sample) {
    if (!active.started) {
      eventRecord(sample.kind, 'start', now, {
        duration: sample.clip.duration,
        pieceId: sample.clip.pieceId,
      });
      active.started = true;
      if (sample.kind === 'capture') audio.play('capture');
      if (sample.kind === 'home') audio.play('home');
    }
    eventRecord(sample.kind, 'frame', now, {
      frameId: sample.frameId,
      positions: sample.positions,
      fraction: sample.fraction,
    });
    if (sample.kind === 'walk') {
      const step = sample.positions[0].stepIndex;
      if (active.lastStep !== step) {
        eventRecord('walk', 'step', now, {
          stepIndex: step,
          position: sample.positions[0],
        });
        active.lastStep = step;
        audio.play('step');
      }
    }
    if (sample.done) {
      eventRecord(sample.kind, 'end', now);
      timeline.advance(now);
      syncControls();
      scheduleAi();
    }
  }
  requestAnimationFrame(frame);
}
try {
  const assets = await loadAssets();
  geo = geometry(assets.manifest);
  renderer = createRenderer(canvas, assets, geo);
  ready = true;
  element('start').disabled = false;
  element('resume').disabled = false;
  resize();
  syncControls();
  requestAnimationFrame(frame);
} catch (error) {
  element('error').textContent = `资源加载失败：${error.message}，请刷新重试`;
  element('start').disabled = true;
  element('resume').disabled = true;
  element('retry').hidden = false;
}
