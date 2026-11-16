<script setup>
import { apiFetch } from '../api/http.js'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { deleteProducedGame, loadProducedGames, producedGames } from '../data/producedGames.js'

const emit = defineEmits(['navigate'])
const query = ref('')
const selectedId = ref('')
const playing = ref(false)
const launching = ref(false)
const frameLoading = ref(false)
const playError = ref('')
const frameVersion = ref(0)
const playPanel = ref(null)
const previewWidth = 720
const previewHeight = 1600
const previewScale = ref(0)
const deletingId = ref('')
const deleteError = ref('')
const failedDeletion = ref(null)
const selected = computed(() => producedGames.items.find((game) => game.id === selectedId.value))
const playableCount = computed(() => producedGames.items.filter((game) => game.available !== false).length)
const filtered = computed(() => {
  const term = query.value.trim().toLowerCase()
  return producedGames.items.filter((game) => [game.name, game.category, game.description].join(' ').toLowerCase().includes(term))
})
let launchVersion = 0
let controller
let timeout
let resizeObserver

// 游戏始终使用固定的手机视口，窗口变化时仅缩放预览，保持内部排版和点击坐标一致。
watch(playPanel, (element) => {
  resizeObserver?.disconnect()
  if (!element) return
  resizeObserver = new ResizeObserver(([entry]) => {
    previewScale.value = Math.min(entry.contentRect.width / previewWidth, entry.contentRect.height / previewHeight, 1)
  })
  resizeObserver.observe(element)
}, { flush: 'post' })

// 切换或离开时销毁 iframe，停止上一个游戏的声音、动画和计时。
function stopGame() {
  launchVersion++
  controller?.abort()
  clearTimeout(timeout)
  playing.value = false
  launching.value = false
  frameLoading.value = false
  playError.value = ''
}
function chooseGame(game) {
  if (game.id === selectedId.value) return
  stopGame()
  selectedId.value = game.id
}

async function deleteGame(game) {
  if (deletingId.value) return
  const confirmed = window.confirm(`确定删除《${game.name}》及其产出内容？\n\n将永久删除工程、策划文档、美术资源、代码、运行包和生成记录，同一工程的所有发布版本也会一并删除。此操作无法撤销。`)
  if (!confirmed) return
  deletingId.value = game.id
  deleteError.value = ''
  failedDeletion.value = null
  if (selectedId.value === game.id) stopGame()
  try {
    const result = await deleteProducedGame(game.id)
    if (result.deleted_ids.includes(selectedId.value)) stopGame()
  } catch (error) {
    deleteError.value = error.message || '删除失败，请重试。'
    failedDeletion.value = game
  } finally {
    deletingId.value = ''
  }
}

async function startGame() {
  if (!selected.value?.play_url || selected.value.available === false || launching.value || deletingId.value) return
  const game = selected.value
  stopGame()
  const version = launchVersion
  controller = new AbortController()
  launching.value = true
  timeout = setTimeout(() => controller.abort(), 15000)
  try {
    // 浏览器对 iframe 的 404 也可能触发 load，先检查真实入口再创建播放器。
    const response = await apiFetch(game.play_url, { method: 'HEAD', signal: controller.signal })
    if (!response.ok) throw new Error('这个游戏暂时无法打开，请刷新列表后重试。')
    if (version !== launchVersion) return
    clearTimeout(timeout)
    frameVersion.value++
    frameLoading.value = true
    playing.value = true
    timeout = setTimeout(() => {
      frameLoading.value = false
      playError.value = '加载时间较长，可以重新运行，或在新窗口中打开。'
    }, 20000)
  } catch (error) {
    if (version === launchVersion) playError.value = error.name === 'AbortError' ? '游戏连接超时，请重试。' : error.message
  } finally {
    if (version === launchVersion) {
      launching.value = false
      if (!playing.value) clearTimeout(timeout)
    }
  }
}
function frameLoaded() {
  clearTimeout(timeout)
  frameLoading.value = false
}
function frameFailed() {
  clearTimeout(timeout)
  frameLoading.value = false
  playError.value = '游戏加载失败，请重新运行或在新窗口打开。'
}

// 列表更新后保留仍存在的选择；已移除的游戏不会留下失效的播放器。
watch(() => producedGames.items, (items) => {
  if (!items.some((game) => game.id === selectedId.value)) {
    stopGame()
    selectedId.value = items[0]?.id || ''
  }
}, { immediate: true })
onMounted(() => { window.scrollTo(0, 0); loadProducedGames() })
onBeforeUnmount(() => { stopGame(); resizeObserver?.disconnect() })
</script>

<template>
  <div class="produced-page">
    <header class="page-header">
      <button class="back-button" @click="emit('navigate', 'home')">← 返回首页</button>
      <div class="header-title">
        <h1>产出游戏 <span v-if="producedGames.loaded" class="count-badge">{{ producedGames.items.length }}</span></h1>
        <p v-if="producedGames.loaded">{{ playableCount }} 款可运行<span v-if="playableCount < producedGames.items.length">，{{ producedGames.items.length - playableCount }} 款待补全</span></p>
      </div>
      <label class="search-box"><span aria-hidden="true">⌕</span><input v-model="query" type="search" aria-label="搜索产出游戏" placeholder="搜索游戏名称或类型"></label>
      <button class="outline-button refresh-button" :disabled="producedGames.loading || Boolean(deletingId)" @click="loadProducedGames">
        {{ producedGames.loading ? '刷新中…' : '↻ 刷新列表' }}
      </button>
    </header>

    <main class="library-main">
      <div v-if="producedGames.error" class="error-message" role="alert">
        <span>{{ producedGames.error }}</span><button @click="loadProducedGames">重新加载</button>
      </div>
      <div v-if="deleteError" class="error-message" role="alert">
        <span>{{ deleteError }}</span><button :disabled="Boolean(deletingId)" @click="deleteGame(failedDeletion)">重试删除</button>
      </div>
      <div v-if="!producedGames.loaded && producedGames.loading" class="empty-state" role="status">正在整理你的游戏…</div>
      <div v-else-if="producedGames.loaded && !producedGames.items.length" class="empty-state">
        <span class="empty-icon" aria-hidden="true">✣</span><h2>第一款作品，等待登场</h2><p>游戏生成可运行版本后，会自动出现在这里。</p>
        <button class="primary-button" @click="emit('navigate', 'workflow')">去生成游戏 ↗</button>
      </div>
      <div v-else-if="producedGames.items.length" class="library-layout">
        <aside class="game-picker" aria-label="选择游戏">
          <div class="picker-title"><h2>游戏列表</h2><span>{{ filtered.length }} 款作品</span></div>
          <div v-if="!filtered.length" class="no-results"><p>没有找到匹配的游戏</p><button class="outline-button" @click="query = ''">清空搜索</button></div>
          <div class="game-list">
            <div v-for="game in filtered" :key="game.id" class="game-card" :class="{ selected: selectedId === game.id }">
              <button class="game-select" :disabled="Boolean(deletingId)" :aria-pressed="selectedId === game.id" :aria-label="`选择 ${game.name}`" @click="chooseGame(game)">
              <div class="card-cover">
                <span class="cover-symbol" aria-hidden="true">✣</span>
                <img v-if="game.cover_url" :src="game.cover_url" alt="" loading="lazy" @error="event => { event.target.hidden = true }">
                <span class="game-tag">{{ game.category }}</span>
              </div>
                <h3 class="card-title">{{ game.name }}</h3>
              </button>
              <div class="card-footer">
                <span class="card-status" :class="{ unavailable: game.available === false }"><i></i> {{ game.deletion_pending ? '待清理产出' : game.available === false ? '待补全运行包' : selectedId === game.id ? '当前选择' : '可运行' }}</span>
                <button class="delete-button" :disabled="Boolean(deletingId)" :aria-label="`删除 ${game.name} 及产出内容`" @click="deleteGame(game)">{{ deletingId === game.id ? '删除中…' : game.deletion_pending ? '重试删除' : '删除' }}</button>
              </div>
            </div>
          </div>
        </aside>

        <section v-if="selected" ref="playPanel" class="play-panel" aria-label="游戏试玩">
          <div class="game-screen" :style="{ width: `${previewWidth}px`, height: `${previewHeight}px`, transform: `translate(-50%, -50%) scale(${previewScale})` }" :aria-busy="launching || frameLoading">
            <iframe v-if="playing" :key="`${selected.id}:${frameVersion}`" :src="selected.play_url" :title="`${selected.name} 游戏窗口`" :width="previewWidth" :height="previewHeight"
              sandbox="allow-scripts allow-same-origin allow-pointer-lock" allow="autoplay; fullscreen" allowfullscreen @load="frameLoaded" @error="frameFailed"></iframe>
            <div v-else-if="selected.available === false" class="unavailable-game">
              <span aria-hidden="true">▧</span><h3>{{ selected.deletion_pending ? '删除尚未完成' : '还缺少游戏内容' }}</h3><p>{{ selected.unavailable_reason }}</p><small>{{ selected.deletion_pending ? '点击列表中的删除按钮，继续清理。' : '补齐运行包后，即可在这里开始游玩。' }}</small>
            </div>
            <div v-else class="game-poster">
              <img v-if="selected.cover_url" :src="selected.cover_url" alt="" @error="event => { event.target.hidden = true }">
              <div class="poster-content"><span class="play-symbol" aria-hidden="true">▷</span><h3>{{ selected.name }}</h3><p>让这段新旅程，从现在开始。</p><button class="poster-play" :disabled="launching" @click="startGame">{{ launching ? '正在打开…' : '开始游玩 →' }}</button></div>
            </div>
            <div v-if="frameLoading" class="loading-overlay" role="status">正在打开游戏…</div>
          </div>
        </section>
        <aside v-if="selected" class="game-details" aria-label="当前游戏操作">
          <span class="eyebrow">{{ selected.available === false ? '等待完整游戏包' : playing ? '正在游玩' : '准备好，开始游戏' }}</span>
          <h2>{{ selected.name }}</h2>
          <p class="game-description">{{ selected.description }}</p>
          <div class="play-actions">
            <button class="primary-button" :disabled="launching || selected.available === false || Boolean(deletingId)" @click="startGame">{{ selected.deletion_pending ? '待清理产出' : selected.available === false ? '待补全运行包' : launching ? '正在打开…' : playing ? '↻ 重新运行' : '▶ 开始游戏' }}</button>
            <a v-if="selected.play_url" class="outline-button" :href="selected.play_url" target="_blank" rel="noopener noreferrer" @click="stopGame">新窗口打开 ↗</a>
            <button v-if="playing" class="stop-button" @click="stopGame">结束试玩</button>
          </div>
          <div v-if="playError" class="error-message player-error" role="alert">{{ playError }}</div>
          <p class="play-note">{{ selected.available === false ? '补齐完整游戏包后即可运行。' : playing ? '切换游戏或结束试玩，会关闭当前游戏。' : '支持在中间试玩，也可在新窗口打开。' }}</p>
          <p class="viewport-label">手机竖屏 · 720 × 1600</p>
        </aside>
      </div>
    </main>
  </div>
</template>

<style scoped>
.produced-page { min-height: 100vh; background: var(--bg-primary); }
.page-header { min-height: 68px; padding: 10px 24px; display: flex; gap: 20px; align-items: center; border-bottom: 2px solid var(--border-color); background: var(--bg-secondary); }
.back-button { border: 0; background: none; font-size: 14px; font-weight: 700; color: var(--text-primary); }
.header-title { min-width: 0; }
.header-title p { font-size: 11px; color: var(--text-tertiary); margin-top: 3px; }
.library-main { width: 100%; max-width: 1800px; margin: auto; padding: 16px 24px; }
.eyebrow { color: var(--accent-blue); font-size: 11px; letter-spacing: 2px; font-weight: 700; }
h1 { font-size: 22px; font-weight: 900; line-height: 1.3; display: flex; align-items: center; gap: 10px; }
.count-badge { font-size: 12px; background: #e9efff; border: 1.5px solid var(--accent-blue); color: var(--accent-blue); border-radius: 6px; padding: 1px 8px; }
.search-box { display: flex; align-items: center; gap: 10px; width: 290px; margin-left: auto; padding: 8px 12px; background: var(--bg-card); border: 1.5px solid var(--border-color); border-radius: 6px; }
.search-box span { color: var(--accent-blue); font-size: 24px; line-height: 1; }
.search-box input { min-width: 0; width: 100%; border: 0; background: transparent; outline: none; font: inherit; font-size: 13px; }
.search-box:focus-within { border-color: var(--accent-blue); outline: 2px solid var(--accent-blue-dim); }
.library-layout { display: grid; grid-template-columns: 280px minmax(0, 1fr) 260px; grid-template-areas: 'picker player details'; gap: 20px; align-items: stretch; }
.game-picker { grid-area: picker; min-width: 0; }
.picker-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.picker-title h2 { font-size: 15px; font-weight: 800; }
.picker-title > span { font-size: 12px; color: var(--text-tertiary); }
.game-list { display: grid; gap: 16px; }
.game-card { text-align: left; width: 100%; border: 2px solid var(--border-color); border-radius: 8px; overflow: hidden; background: var(--bg-card); transition: border-color .15s, box-shadow .15s; }
.game-card:hover { border-color: var(--accent-blue); }
.game-card.selected { border-color: var(--accent-blue); box-shadow: 3px 3px 0 var(--accent-blue); }
.game-select { display: block; width: 100%; text-align: left; }
.card-title { padding: 11px 14px 0; font-size: 14px; line-height: 1.5; font-weight: 800; }
.card-footer { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 0 14px 10px; }
.delete-button { padding: 4px 0 0; color: #ad443d; font-size: 11px; flex-shrink: 0; }
.delete-button:hover { color: #c52319; text-decoration: underline; }
.card-cover { position: relative; height: 125px; overflow: hidden; background: #e5ebf8; display: grid; place-items: center; }
.cover-symbol { font-size: 64px; color: #849bd4; }
.card-cover img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: center 30%; }
.game-tag { position: absolute; bottom: 8px; left: 10px; font-size: 10px; padding: 2px 8px; background: #fffffff0; color: #343b4a; border: 1px solid #ffffff; border-radius: 4px; }
.card-status { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-tertiary); margin-top: 6px; }
.card-status.unavailable { color: #9b651c; }
.card-status.unavailable i { background: #b37c2c; }
.unavailable-game { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; padding: 32px; text-align: center; color: #425064; background: #eef1f6; }
.unavailable-game > span { font-size: 56px; color: #8a96a7; }
.unavailable-game h3 { font-size: 40px; }
.unavailable-game p { max-width: 560px; font-size: 26px; line-height: 1.8; }
.unavailable-game small { font-size: 22px; color: #657388; }
.card-status i { width: 6px; height: 6px; display: inline-block; border-radius: 50%; background: var(--accent-green); }
.play-panel { grid-area: player; position: relative; min-width: 0; height: 72svh; min-height: 520px; border: 2px solid var(--shadow-dark); border-radius: 10px; overflow: hidden; background: #101324; box-shadow: 5px 5px 0 var(--shadow-dark); }
.game-details { grid-area: details; align-self: start; min-width: 0; padding: 16px; border: 1.5px solid var(--border-color); border-radius: 8px; background: var(--bg-card); }
.game-details h2 { font-size: 17px; line-height: 1.5; margin: 6px 0 8px; font-weight: 900; overflow-wrap: anywhere; }
.game-description { font-size: 12px; line-height: 1.7; color: var(--text-secondary); }
.play-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.play-actions .primary-button, .play-actions .outline-button { padding: 8px 10px; font-size: 12px; }
.play-note { margin-top: 12px; font-size: 11px; line-height: 1.7; color: var(--text-tertiary); }
.viewport-label { margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border-color); font-size: 12px; color: var(--text-tertiary); }
.primary-button, .outline-button, .poster-play { display: inline-flex; justify-content: center; align-items: center; border-radius: 5px; padding: 9px 15px; font: inherit; font-size: 13px; font-weight: 700; text-decoration: none; }
.primary-button { background: var(--accent-blue); border: 1.5px solid var(--accent-blue); color: white; }
.outline-button { background: var(--bg-card); color: var(--text-primary); border: 1.5px solid var(--border-color); }
.outline-button:hover { border-color: var(--accent-blue); color: var(--accent-blue); }
.stop-button { background: none; border: none; color: var(--text-secondary); font-size: 12px; padding: 8px 0; }
/* 逻辑视口固定为手机尺寸，缩放以视口中心为原点，外层面板保持固定。 */
.game-screen { position: absolute; left: 50%; top: 50%; overflow: hidden; border-radius: 8px; background: #101324; }
iframe { display: block; width: 100%; height: 100%; border: 0; }
.game-poster { position: absolute; inset: 0; display: grid; place-items: center; overflow: hidden; background: linear-gradient(135deg, #173f42, #263e5b); }
.game-poster > img { position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: .25; filter: blur(2px); }
.poster-content { position: relative; text-align: center; padding: 30px; color: white; }
.play-symbol { display: inline-grid; place-items: center; width: 74px; height: 74px; border: 1px solid #ffffff60; background: #ffffff15; border-radius: 50%; font-size: 42px; margin-bottom: 20px; }
.poster-content h3 { font-size: 40px; line-height: 1.5; }
.poster-content p { font-size: 24px; color: #d1dde0; margin: 10px 0 28px; }
.poster-play { background: #e8f2c9; color: #1b3431; border: 1px solid #e8f2c9; padding: 14px 32px; font-size: 26px; }
.loading-overlay { position: absolute; inset: 0; display: grid; place-items: center; color: var(--accent-blue); font-size: 28px; background: #f5f7fcf5; }
.empty-state { min-height: 350px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px; color: var(--text-secondary); text-align: center; }
.empty-state h2 { font-size: 24px; color: var(--text-primary); }
.empty-state p { font-size: 14px; }
.empty-icon { font-size: 62px; color: var(--accent-blue); }
.no-results { padding: 30px 10px; text-align: center; color: var(--text-secondary); font-size: 13px; }
.no-results button { margin-top: 12px; }
.error-message { display: flex; gap: 14px; align-items: center; justify-content: space-between; padding: 12px 16px; margin-bottom: 20px; background: #fff0ed; color: #9b3c30; border: 1px solid #e7b3a9; border-radius: 5px; font-size: 13px; }
.error-message button { flex-shrink: 0; background: none; border: 0; color: inherit; text-decoration: underline; }
.player-error { margin: 12px 0 0; }
button { cursor: pointer; }
button:disabled { opacity: .6; cursor: wait; }
button:focus-visible, a:focus-visible { outline: 3px solid var(--accent-blue); outline-offset: 4px; }
@media (max-width: 1100px) { .library-layout { grid-template-columns: 220px minmax(0, 1fr) 210px; gap: 16px; } .library-main { padding: 12px 16px; } }
/* 桌面工作区占满窗口，列表独立滚动，播放器始终留在当前可见区域。 */
@media (min-width: 781px) {
  .produced-page { height: 100vh; height: 100dvh; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
  .page-header { flex-shrink: 0; }
  .library-main { flex: 1; min-height: 0; margin: 0 auto; display: flex; flex-direction: column; }
  .library-main > .error-message { flex-shrink: 0; }
  .library-layout { flex: 1; min-height: 0; align-items: stretch; }
  .game-picker { min-height: 0; display: flex; flex-direction: column; }
  .picker-title { flex-shrink: 0; }
  .game-list { min-height: 0; overflow-y: auto; overscroll-behavior: contain; grid-auto-rows: max-content; align-content: start; padding: 4px 10px 8px 4px; scrollbar-gutter: stable; }
  .play-panel { min-height: 0; height: auto; }
  .empty-state { flex: 1; min-height: 0; }
}
@media (max-width: 780px) {
  .page-header { padding: 12px 16px; gap: 10px; flex-wrap: wrap; }
  .back-button { font-size: 12px; } h1 { font-size: 20px; } .refresh-button { margin-left: auto; }
  .search-box { width: 100%; margin-left: 0; order: 1; }
  .library-main { padding: 16px; } .library-layout { grid-template-columns: minmax(0, 1fr); grid-template-areas: 'picker' 'details' 'player'; gap: 16px; }
  .game-list { display: flex; overflow-x: auto; padding: 0 6px 8px 0; gap: 12px; } .game-card { flex: 0 0 230px; } .card-cover { height: 110px; }
}
</style>
