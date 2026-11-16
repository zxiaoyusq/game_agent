import { createGame, rollDice, moveToken, legalMoves, FINISH } from './rules.mjs';
import { chooseMove } from './ai.mjs';
import { renderBoard } from './board.mjs';
import { createAudio } from './audio.mjs';
import { loadSave, saveGame } from './storage.mjs';

const app = document.querySelector('#app');
const modalRoot = document.querySelector('#modal-root');
const notice = document.querySelector('#notice');
const palette = ['#237b78', '#ce6f51', '#b58329', '#5d67a0'];
const teamNames = ['翡翠商队', '珊瑚商队', '琥珀商队', '靛蓝商队'];
const teamSymbols = ['◈', '❖', '✦', '◇'];
const saved = loadSave();
const audio = createAudio();
let game = saved.game;
let settings = saved.settings;
let screen = 'lobby';
let modal = null;
let busy = false;
let timer;
let animationTimer;
let generation = 0;
let saveFailed = false;
let lastFocus;
let selection = { mode: 'quick', count: 2, play: 'solo' };
audio.setEnabled(settings.sound);

// 所有文本来源虽然均为本地数据，仍统一转义存档内容，避免插入HTML。
function escapeText(value) { return String(value).replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character])); }
const modeName = mode => mode === 'quick' ? '疾风商路' : '经典远征';
const currentPlayer = () => game?.players[game.turn];
const humanTurn = () => currentPlayer()?.kind === 'human';
const delay = () => settings.fast || matchMedia('(prefers-reduced-motion: reduce)').matches ? 65 : 550;

function header() {
  return `<header class="topbar"><button class="brand" data-action="home" aria-label="返回商旅大厅"><img src="./assets/emblem.svg" alt=""><span>琥珀商路<small>AMBER CARAVAN</small></span></button><div class="top-tools"><span class="offline-label"><i></i> 离线也能畅玩</span><button class="icon-button" data-action="rules" aria-label="玩法说明">?</button><button class="icon-button" data-action="settings" aria-label="设置"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="3" fill="var(--cream)"/><circle cx="16" cy="17" r="3" fill="var(--cream)"/></svg></button></div></header>`;
}

function renderLobby() {
  const changingView = screen !== 'lobby';
  screen = 'lobby';
  app.innerHTML = `${header()}<main class="lobby"><section class="intro"><div class="eyebrow"><span></span> A JOURNEY BETWEEN OASES</div><h1>掷一枚骰子，<br>启程去绿洲。</h1><p class="intro-copy">沿着瓷砖铺就的商路，与朋友追逐、相遇。<br>让每一次幸运，都成为恰好的策略。</p><div class="intro-tags"><span>经典 LUDO</span><span>摩洛哥灵感</span><span>2—4 人同屏</span></div><div class="story-mark"><span>✧</span><div>一方棋盘，一段远行。<small>DESIGNED FOR LITTLE ESCAPES</small></div></div></section>
  <section class="setup panel" aria-label="开始旅程"><div class="panel-kicker">THE CARAVAN CLUB <span>01 / PLAY</span></div><h2>你的下一段旅程</h2><p class="muted">选好路线，邀上旅伴。即刻出发。</p><div class="choice-label">选择路线 <span>两种不同的取胜策略</span></div><div class="mode-choices"><button class="mode-card ${selection.mode === 'quick' ? 'selected' : ''}" data-mode="quick" aria-pressed="${selection.mode === 'quick'}"><span class="mode-symbol">➶</span><span><strong>疾风商路</strong><small>吃子解锁 · 一子归家</small></span><span class="radio"></span></button><button class="mode-card ${selection.mode === 'classic' ? 'selected' : ''}" data-mode="classic" aria-pressed="${selection.mode === 'classic'}"><span class="mode-symbol">✥</span><span><strong>经典远征</strong><small>四子归家 · 步步为营</small></span><span class="radio"></span></button></div>
  <div class="setup-row"><span class="choice-label">同行人数</span><div class="segmented" aria-label="同行人数">${[2, 3, 4].map(count => `<button data-count="${count}" aria-pressed="${selection.count === count}" class="${selection.count === count ? 'selected' : ''}">${count} 人</button>`).join('')}</div></div>
  <div class="play-choices"><button data-play="solo" class="${selection.play === 'solo' ? 'selected' : ''}" aria-pressed="${selection.play === 'solo'}"><span>人机旅程</span><small>你与电脑商队</small></button><button data-play="local" class="${selection.play === 'local' ? 'selected' : ''}" aria-pressed="${selection.play === 'local'}"><span>好友同屏</span><small>传递设备，轮流落子</small></button></div>
  <button class="primary start-button" data-action="start">开启旅程 <span>↗</span></button>${game ? `<button class="resume-button" data-action="resume">${game.phase === 'won' ? '查看上次结算' : '继续上次旅程'} <span>${modeName(game.mode)} · 第 ${game.stats.rolls} 次掷骰</span></button>` : ''}<p class="setup-note">无广告 · 无需登录 · 自动保存进度</p></section></main><footer class="lobby-footer"><span>✧ &nbsp; 在幸运与策略之间，找到你的路。</span><span>AMBER CARAVAN &nbsp; / &nbsp; LUDO REIMAGINED</span></footer>`;
  bindActions();
  if (changingView) window.scrollTo(0, 0);
}

function startGame() {
  clearTimers();
  const ids = selection.count === 2 ? [0, 2] : Array.from({ length: selection.count }, (_, i) => i);
  game = createGame({ mode: selection.mode, players: ids.map((id, index) => ({ id, name: teamNames[id], kind: selection.play === 'solo' && index > 0 ? 'ai' : 'human' })) });
  screen = 'game';
  persist();
  renderGame();
  scheduleAI();
}

function renderGame() {
  screen = 'game';
  app.innerHTML = `${header()}<main class="game-layout"><aside class="journey-sidebar"><div class="eyebrow">THE OASIS TRAIL</div><h1>${modeName(game.mode)}</h1><p class="journey-description">${game.mode === 'quick' ? '在追逐中打开商路。<br>先吃一子，再率先归家。' : '穿过沙海，回到绿洲。<br>四枚棋子归家即获胜。'}</p><div id="players" class="player-list"></div><div class="side-inscription"><span>✧</span><p>幸运决定起点<br>策略决定归途</p><small>LET THE JOURNEY UNFOLD</small></div></aside><section class="board-section" aria-label="商路棋盘"><div class="board-heading"><span><i></i> ${game.players.length} 支商队 · ${game.players.some(p => p.kind === 'ai') ? '人机旅程' : '好友同屏'}</span><button class="text-button" data-action="pause">暂停旅程 Ⅱ</button></div><div id="board"></div><div class="board-caption"><span>✧ 安全驿站免受攻击</span><span>◈ 相同颜色的路线通往家园</span></div></section><aside class="action-sidebar"><section class="turn-panel panel"><div class="panel-kicker">YOUR NEXT MOVE <span id="turn-number"></span></div><div id="turn-content"></div></section><section class="journal panel"><div class="journal-heading"><h3>商路见闻</h3><span>JOURNAL</span></div><ol id="history"></ol></section><div class="mini-rule"><span>✧</span><p id="tip"></p></div></aside></main>`;
  bindActions();
  updateGame();
  window.scrollTo(0, 0);
}

function updateGame() {
  if (screen !== 'game') return;
  const player = currentPlayer();
  const available = game.phase === 'move' && humanTurn() && !busy && !modal ? legalMoves(game) : [];
  document.querySelector('#players').innerHTML = game.players.map((item, index) => `<div class="player-card ${index === game.turn ? 'active' : ''}" style="--team:${palette[item.id]}"><div class="player-avatar">${teamSymbols[item.id]}</div><div class="player-info"><strong>${escapeText(item.name)} <small>${item.kind === 'ai' ? '电脑' : '玩家'}</small></strong><span>${game.mode === 'quick' ? (item.homeUnlocked ? '商路已开启' : '吃子开启归家路') : `${item.finished} / 4 已归家`}</span><div class="progress-pips">${item.tokens.map(progress => `<i class="${progress === FINISH ? 'finished' : progress >= 0 ? 'travelling' : ''}"></i>`).join('')}</div></div><span class="turn-marker">${index === game.turn ? '◂' : ''}</span></div>`).join('');
  document.querySelector('#turn-number').textContent = `掷骰 ${game.stats.rolls}`;
  const canRoll = !busy && !modal && humanTurn() && game.phase === 'roll';
  const prompt = busy ? '商旅正在前行…' : game.phase === 'won' ? '抵达绿洲，旅程完成' : !humanTurn() ? '电脑正在规划路线…' : game.phase === 'roll' ? '轮到你了，掷出好运。' : '选择一枚亮起的棋子前进。';
  document.querySelector('#turn-content').innerHTML = `<h2 style="--team:${palette[player.id]}"><i></i>${escapeText(player.name)}</h2><p class="turn-prompt">${prompt}</p><button id="roll-button" class="dice-button ${busy && game.lastAction?.type !== 'move' ? 'rolling' : ''}" data-action="roll" ${canRoll ? '' : 'disabled'} aria-label="掷骰子"><span class="dice" data-value="${game.dice || 1}">${Array.from({ length: 9 }, (_, index) => `<i class="dot dot-${index}"></i>`).join('')}</span><span class="roll-label">${game.phase === 'won' ? '旅程完成' : game.phase === 'move' ? `走 ${game.dice} 步` : busy || !humanTurn() ? '请稍候' : '点击掷骰'}</span></button><div class="message" role="status" aria-live="polite">${escapeText(game.message || '准备启程')}</div><div class="token-choices" aria-label="选择棋子">${player.tokens.map((progress, index) => `<button data-token="${index}" style="--team:${palette[player.id]}" ${available.includes(index) ? '' : 'disabled'} aria-label="移动${index + 1}号棋子"><span>${index + 1}</span><small>${progress === FINISH && !player.outerLast?.[index] ? '已归家' : progress === -1 ? '出发' : '前进'}</small></button>`).join('')}</div>`;
  document.querySelector('#history').innerHTML = (game.history || []).slice(-4).reverse().map((item, index) => `<li><span class="log-dot ${index === 0 ? 'new' : ''}"></span>${escapeText(typeof item === 'string' ? item : item.message || '')}</li>`).join('') || '<li class="muted">商队已集结，等待第一枚骰子。</li>';
  document.querySelector('#tip').textContent = game.mode === 'quick' && !player.homeUnlocked ? '疾风商路：先吃掉一枚对手棋子，才能进入自己的归家路线。锁门时会继续绕圈。' : '掷出六点可以出营并再掷一次。吃子、归家也能再掷；连续第三个六点结束回合。';
  renderBoard(document.querySelector('#board'), game, { legalTokens: available, onToken: handleMove });
  bindActions(document.querySelector('.action-sidebar'));
}

// 正式骰子使用系统随机源；拒绝252以上的取值，避免取模造成偏差。
function randomDie() {
  const bytes = new Uint8Array(1);
  do { crypto.getRandomValues(bytes); } while (bytes[0] >= 252);
  return bytes[0] % 6 + 1;
}

function handleRoll() {
  if (busy || modal || screen !== 'game' || game.phase !== 'roll') return;
  const epoch = generation;
  busy = true;
  audio.unlock();
  audio.play('roll');
  updateGame();
  animationTimer = setTimeout(() => {
    if (epoch !== generation) return;
    game = rollDice(game, randomDie());
    busy = false;
    persist();
    updateGame();
    scheduleAI();
  }, delay());
}

function handleMove(index) {
  if (busy || modal || screen !== 'game' || game.phase !== 'move' || !legalMoves(game).includes(index)) return;
  const epoch = generation;
  game = moveToken(game, index);
  busy = true;
  audio.unlock();
  audio.play(game.phase === 'won' ? 'win' : game.lastAction?.captured?.length ? 'capture' : game.lastAction?.to === FINISH ? 'home' : 'move');
  persist();
  updateGame();
  animationTimer = setTimeout(() => {
    if (epoch !== generation) return;
    busy = false;
    updateGame();
    if (game.phase === 'won') openModal('win');
    else scheduleAI();
  }, delay());
}

// 只有控制器拥有AI计时器；回到大厅/弹窗/后台都取消，避免旧局回调继续落子。
function clearTimers() {
  generation++;
  clearTimeout(timer);
  clearTimeout(animationTimer);
  busy = false;
}
function scheduleAI() {
  clearTimeout(timer);
  if (screen !== 'game' || modal || busy || document.hidden) return;
  // 结算也是已提交状态的表现；暂停或切后台后要重新显示，不能只依赖落子计时器。
  if (game.phase === 'won') { openModal('win'); return; }
  if (humanTurn()) return;
  const epoch = generation;
  timer = setTimeout(() => {
    if (epoch !== generation || modal || document.hidden) return;
    if (game.phase === 'roll') handleRoll();
    else handleMove(chooseMove(game));
  }, delay());
}
function persist() {
  saveFailed = !saveGame(game, settings);
  showNotice(saveFailed ? '浏览器未能保存进度，请勿关闭页面。' : '');
}
function showNotice(message) { notice.textContent = message; notice.classList.toggle('visible', !!message); }

function rulesContent() {
  return `<div class="modal-eyebrow">HOW TO PLAY</div><h2>一路好运，也要好策略。</h2><div class="rules-grid"><article><b>01</b><h3>掷骰 · 出发</h3><p>轮流掷骰。六点可以让营地棋子出发，或让路上的棋子前进六步。亮起的棋子可以点击，也可以用编号按钮选择。</p></article><article><b>02</b><h3>追逐 · 守护</h3><p>落在对手单枚棋子所在的普通格，会把它送回营地。星形驿站绝对安全；同色叠子也受保护，敌方不可落入。</p></article><article><b>03</b><h3>奖励 · 再掷</h3><p>掷出六点、吃子或抵达终点，均可再掷一次。连续第三个六点不移动，直接交给下一队。没有合法棋子会自动换人。</p></article><article><b>04</b><h3>归家 · 获胜</h3><p>归家必须点数恰好。经典远征需要四子归家；疾风商路开局两子在路上，必须先吃一子解锁归家，第一子归家即胜。</p></article></div><p class="modal-note">骰子对所有玩家使用相同的公平随机规则。支持 2—4 人本地同屏，或一位玩家与电脑对战。</p><button class="primary" data-action="close">明白了，继续旅程</button>`;
}

function openModal(type) {
  if (modal) return;
  lastFocus = document.activeElement;
  clearTimers();
  modal = type;
  if (screen === 'game') updateGame();
  let content;
  if (type === 'rules') content = rulesContent();
  else if (type === 'settings') content = `<div class="modal-eyebrow">MAKE IT YOURS</div><h2>旅途偏好</h2><p class="muted">让旅程按你的节奏展开。</p><button class="setting-row" data-action="sound" role="switch" aria-checked="${settings.sound}"><span><strong>声音反馈</strong><small>骰子、落子与归家的轻柔音效</small></span><i class="switch ${settings.sound ? 'on' : ''}"></i></button><button class="setting-row" data-action="fast" role="switch" aria-checked="${settings.fast}"><span><strong>快速节奏</strong><small>缩短等待与电脑思考时间</small></span><i class="switch ${settings.fast ? 'on' : ''}"></i></button><button class="primary" data-action="close">保存并继续</button>`;
  else if (type === 'win') {
    const winner = game.players.find(player => player.id === game.winner);
    content = `<div class="victory-ornament" style="--team:${palette[winner.id]}">✦</div><div class="modal-eyebrow">THE OASIS IS YOURS</div><h2>${escapeText(winner.name)}抵达绿洲</h2><p class="muted">每一步选择，都是这段旅程的风景。</p><div class="result-stats"><div><strong>${game.stats.rolls}</strong><small>次掷骰</small></div><div><strong>${game.stats.moves}</strong><small>次落子</small></div><div><strong>${game.stats.captures}</strong><small>次吃子</small></div></div><button class="primary" data-action="again">再来一局 ↗</button><button class="secondary" data-action="lobby">返回商旅大厅</button>`;
  } else content = `<div class="modal-eyebrow">TAKE A BREATH</div><h2>在绿洲歇一会儿。</h2><p class="muted">${saveFailed ? '当前未能保存，请继续留在页面。' : '旅程已自动保存，商队会在这里等你。'}</p><button class="primary" data-action="close">继续旅程</button><button class="secondary" data-action="restart">重新开始本局</button><button class="text-button full" data-action="lobby">返回商旅大厅</button>`;
  modalRoot.innerHTML = `<div class="modal-backdrop"><section role="dialog" aria-modal="true" aria-label="${type === 'rules' ? '玩法说明' : type === 'settings' ? '旅途偏好' : type === 'win' ? '旅程结算' : '暂停旅程'}" class="modal ${type === 'win' ? 'win-modal' : ''}"><button class="modal-close icon-button" data-action="close" aria-label="关闭">×</button>${content}</section></div>`;
  app.inert = true;
  bindActions(modalRoot);
  modalRoot.querySelector('button')?.focus();
}
function closeModal() {
  const wasVictory = modal === 'win';
  modal = null;
  modalRoot.innerHTML = '';
  app.inert = false;
  if (wasVictory && game.phase === 'won') { renderLobby(); return; }
  if (screen === 'game') updateGame();
  lastFocus?.isConnected && lastFocus.focus();
  scheduleAI();
}
function restart() {
  const players = game.players.map(({ id, name, kind }) => ({ id, name, kind }));
  clearTimers();
  game = createGame({ mode: game.mode, players });
  closeModal();
  persist();
  renderGame();
  scheduleAI();
}

function bindActions(root = app) {
  root.querySelectorAll('[data-action]').forEach(button => button.onclick = () => {
    audio.unlock();
    const action = button.dataset.action;
    if (action === 'start') startGame();
    else if (action === 'resume') { clearTimers(); renderGame(); scheduleAI(); }
    else if (action === 'roll' && humanTurn()) handleRoll();
    else if (action === 'rules' || action === 'settings') openModal(action);
    else if (action === 'pause' || action === 'home' && screen === 'game') openModal('pause');
    else if (action === 'close') closeModal();
    else if (action === 'again' || action === 'restart') restart();
    else if (action === 'lobby') { clearTimers(); screen = 'lobby'; closeModal(); renderLobby(); }
    else if (action === 'sound' || action === 'fast') {
      settings[action] = !settings[action];
      audio.setEnabled(settings.sound);
      persist();
      button.setAttribute('aria-checked', settings[action]);
      button.querySelector('.switch').classList.toggle('on', settings[action]);
    }
  });
  root.querySelectorAll('[data-token]').forEach(button => button.onclick = () => { if (humanTurn()) handleMove(Number(button.dataset.token)); });
  root.querySelectorAll('[data-mode]').forEach(button => button.onclick = () => { selection.mode = button.dataset.mode; renderLobby(); });
  root.querySelectorAll('[data-count]').forEach(button => button.onclick = () => { selection.count = Number(button.dataset.count); renderLobby(); });
  root.querySelectorAll('[data-play]').forEach(button => button.onclick = () => { selection.play = button.dataset.play; renderLobby(); });
}

// 弹窗完整键盘焦点环；隐藏标签页暂停计时，重新可见后从已提交状态继续。
document.addEventListener('keydown', event => {
  if (!modal) return;
  if (event.key === 'Escape') { closeModal(); return; }
  if (event.key !== 'Tab') return;
  const targets = [...modalRoot.querySelectorAll('button:not([disabled])')];
  if (event.shiftKey && document.activeElement === targets[0]) { event.preventDefault(); targets.at(-1).focus(); }
  else if (!event.shiftKey && document.activeElement === targets.at(-1)) { event.preventDefault(); targets[0].focus(); }
});
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { clearTimers(); if (screen === 'game') updateGame(); }
  else scheduleAI();
});

// 仅提供只读快照，供浏览器验收确认真实点击产生的局面；不提供改局/强制胜利入口。
Object.defineProperty(window, 'amberCaravan', { value: Object.freeze({ snapshot: () => structuredClone({ game, screen, modal, busy, settings, saveFailed }) }) });
renderLobby();
if (saved.warning) showNotice(saved.warning);
