<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { fetchReferenceGame, fetchReferenceGames, fetchResearchDocument } from '../api/workflow.js'

const props = defineProps({
  compact: Boolean,
  selectedPaths: { type: Array, default: () => [] },
})
const emit = defineEmits(['select'])
const items = ref([])
const summary = ref(null)
const loading = ref(false)
const error = ref('')
const query = ref('')
const category = ref('')
const packageStatus = ref('')
const selectedGame = ref(null)
const detailLoading = ref(false)
const detailError = ref('')
const selectedAsset = ref(null)
const selectedDocument = ref(null)
const documentLoading = ref(false)
const documentError = ref('')
let disposed = false
let detailVersion = 0
let documentVersion = 0

// 所有过滤都基于后端核验的本地目录，不以历史采集成功记录推断包体可用性。
const categories = computed(() => [...new Set(items.value.map((item) => item.category).filter(Boolean))].sort())
const categoryLabels = { Puzzle: '益智', Action: '动作', Simulation: '模拟', Card: '卡牌', Casual: '休闲', Match: '消除', Racing: '竞速', Children: '儿童', Strategy: '策略', Parkour: '跑酷', Female: '女性向', 'Single challenge': '单人挑战', Arcade: '街机', Tabletop: '桌游', Adventure: '冒险', Sports: '体育', Shooting: '射击', 'Ball games': '球类' }
function categoryLabel(value) { return categoryLabels[value] || value || '未分类' }
const filteredGames = computed(() => {
  const term = query.value.trim().toLowerCase()
  return items.value.filter((item) => (!category.value || item.category === category.value)
    && (!packageStatus.value || item.package_status === packageStatus.value)
    && (!term || [item.name, item.id, item.description, item.category, categoryLabel(item.category)].join(' ').toLowerCase().includes(term)))
})
const assetLabels = { icon: '图标', banner: '横幅', hotgame: '推荐图', hot: '推荐图', theme: '主题图', preview: '预览动图', screenshot: '商店截图' }
function assetLabel(asset) { return assetLabels[asset.role] || asset.name }
function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) return '—'
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(bytes / 1024)} KB`
}
// 明确携带已经存在的ZIP，不把“选择游戏资料”误说成已经向Agent提供原包。
function gameReferencePaths(item) {
  const packages = item.package_files || (item.package ? [item.package] : [])
  const paths = [item.reference_path]
  if (item.directory_reference_path) {
    paths.push(...packages.map(file => `${item.directory_reference_path}/${file.name}`))
  }
  return [...new Set(paths.filter(Boolean))]
}
function isSelected(item) {
  const paths = gameReferencePaths(item)
  return paths.length > 0 && paths.every(path => props.selectedPaths.includes(path))
}
function chooseGame(item) {
  for (const path of gameReferencePaths(item)) {
    if (!props.selectedPaths.includes(path)) emit('select', path)
  }
}
// 详情请求编号避免快速切换卡片时，迟到的响应覆盖当前选择。
async function openGame(item) {
  const version = ++detailVersion
  selectedGame.value = item
  selectedAsset.value = null
  detailError.value = ''
  detailLoading.value = true
  try {
    const detail = await fetchReferenceGame(item.id)
    if (!disposed && version === detailVersion) {
      selectedGame.value = detail
      selectedAsset.value = detail.assets?.[0] || null
    }
  } catch (cause) {
    if (!disposed && version === detailVersion) detailError.value = cause.message || '游戏详情加载失败'
  } finally {
    if (!disposed && version === detailVersion) detailLoading.value = false
  }
}
function closeGame() { detailVersion++; selectedGame.value = null; selectedAsset.value = null }
// 案例文档作为文本显示；脚本、HTML 和整套工程不在此执行或自动加入项目。
async function openDocument(item) {
  const version = ++documentVersion
  selectedDocument.value = item
  documentLoading.value = true
  documentError.value = ''
  try {
    const document = await fetchResearchDocument(item.reference_path)
    if (!disposed && version === documentVersion) selectedDocument.value = document
  } catch (cause) {
    if (!disposed && version === documentVersion) documentError.value = cause.message || '研究文档加载失败'
  } finally {
    if (!disposed && version === documentVersion) documentLoading.value = false
  }
}
function closeDocument() { documentVersion++; selectedDocument.value = null }
function chooseDocument(item) {
  if (!props.selectedPaths.includes(item.reference_path)) emit('select', item.reference_path)
}
async function loadGames() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchReferenceGames()
    if (disposed) return
    items.value = data.items || []
    summary.value = data.summary || null
  } catch (cause) {
    if (!disposed) error.value = cause.message || '公司游戏参考加载失败'
  } finally {
    if (!disposed) loading.value = false
  }
}
onMounted(loadGames)
onBeforeUnmount(() => { disposed = true; detailVersion++; documentVersion++ })
</script>

<template>
  <section class="reference-library" :class="{ compact }" aria-label="公司游戏参考">
    <header class="reference-heading">
      <div>
        <h2>{{ compact ? '从公司游戏参考添加' : '公司游戏参考' }}</h2>
        <p>{{ compact ? '选择游戏后，加入游戏信息及已提供的本地原包路径；缺少原包时仅加入信息资料。' : '浏览本地收集的游戏信息、商店素材与研究资料。' }}</p>
      </div>
      <button type="button" class="reference-button" :disabled="loading" @click="loadGames">{{ loading ? '读取中…' : '刷新目录' }}</button>
    </header>
    <p v-if="error" class="reference-error" role="alert">{{ error }}</p>
    <template v-if="summary">
      <div class="reference-stats">
        <span><strong>{{ items.length }}</strong> 款游戏</span>
        <span><strong>{{ summary.art_file_count }}</strong> 份美术素材</span>
        <span><strong>{{ summary.local_package_games }}</strong> 款有本地原包</span>
        <span><strong>{{ summary.missing_package_games }}</strong> 款本地原包缺失</span>
      </div>
      <details v-if="summary.warnings?.length || summary.research?.length" class="reference-source-notes">
        <summary>案例研究与目录说明</summary>
        <p v-for="(warning, index) in summary.warnings || []" :key="index">{{ warning }}</p>
        <p>研究文档记录来源案例的方法与限制；选取需要的文档即可，案例结果不代表当前项目已通过验收。</p>
        <details v-for="item in summary.research || []" :key="item.reference_path" class="reference-research">
          <summary><strong>{{ item.name }}</strong> · {{ item.documents?.length || 0 }} 份可读文档 · {{ item.file_count }} 份本地文件</summary>
          <code>{{ item.reference_path }} · {{ formatBytes(item.bytes) }}</code>
          <ul v-if="item.documents?.length" class="reference-document-list">
            <li v-for="document in item.documents" :key="document.reference_path">
              <button type="button" class="reference-document-link" :title="document.reference_path" @click="openDocument(document)">{{ document.name }}</button>
              <button v-if="compact" type="button" class="reference-button" :disabled="selectedPaths.includes(document.reference_path)" @click="chooseDocument(document)">{{ selectedPaths.includes(document.reference_path) ? '已添加' : '添加参考' }}</button>
            </li>
          </ul>
        </details>
      </details>
    </template>
    <div class="reference-filters">
      <input v-model="query" type="search" aria-label="搜索公司游戏参考" placeholder="搜索游戏名、简介或编号" />
      <select v-model="category" aria-label="筛选参考游戏品类"><option value="">全部品类</option><option v-for="name in categories" :key="name" :value="name">{{ categoryLabel(name) }}</option></select>
      <select v-model="packageStatus" aria-label="筛选本地原包状态"><option value="">全部原包状态</option><option value="present">本地原包已提供</option><option value="missing">本地原包缺失</option></select>
    </div>
    <p class="reference-result-count">{{ filteredGames.length }} 款匹配</p>
    <div v-if="loading && !items.length" class="reference-empty" role="status">正在读取本地参考目录…</div>
    <div v-else-if="!filteredGames.length && !error" class="reference-empty">暂无匹配的游戏，请调整筛选条件。</div>
    <div class="reference-grid">
      <article v-for="item in filteredGames" :key="item.id" class="reference-game">
        <button type="button" class="reference-game-main" @click="openGame(item)">
          <img v-if="item.icon_url" :src="item.icon_url" :alt="`${item.name} 图标`" loading="lazy" />
          <span v-else class="reference-game-placeholder">🎮</span>
          <span class="reference-game-copy"><strong>{{ item.name }}</strong><small>{{ categoryLabel(item.category) }} · {{ item.id }}</small></span>
        </button>
        <p v-if="!compact" class="reference-description">{{ item.description || '暂无简介，查看游戏资料与商店素材。' }}</p>
        <div class="reference-card-foot">
          <span class="reference-package-status" :class="item.package_status">{{ item.package_status === 'present' ? '本地原包已提供' : '本地原包缺失' }}</span>
          <button v-if="compact" type="button" class="reference-button" :disabled="isSelected(item) || !item.reference_path" @click="chooseGame(item)">{{ isSelected(item) ? '已添加' : item.package_status === 'present' ? '添加资料与原包' : '仅添加资料' }}</button>
          <button v-else type="button" class="reference-button" @click="openGame(item)">查看资料</button>
        </div>
      </article>
    </div>
    <Teleport to="body">
      <div v-if="selectedDocument" class="reference-overlay" @click.self="closeDocument" @keydown.esc="closeDocument">
        <section class="reference-dialog" role="dialog" aria-modal="true" :aria-label="selectedDocument.name">
          <header class="reference-dialog-head"><h2>{{ selectedDocument.name }}</h2><button type="button" class="reference-button" autofocus aria-label="关闭研究文档" @click="closeDocument">关闭 ×</button></header>
          <div class="reference-detail-body">
            <div class="reference-paths"><code>{{ selectedDocument.reference_path }}</code></div>
            <p v-if="documentLoading" role="status">正在读取研究文档…</p>
            <p v-else-if="documentError" class="reference-error" role="alert">{{ documentError }}</p>
            <pre v-else class="reference-document-content">{{ selectedDocument.content }}</pre>
          </div>
          <footer v-if="compact" class="reference-dialog-foot"><button type="button" class="reference-button primary" :disabled="documentLoading || !!documentError || selectedPaths.includes(selectedDocument.reference_path)" @click="chooseDocument(selectedDocument)">{{ selectedPaths.includes(selectedDocument.reference_path) ? '已添加到参考资料' : '添加到参考资料' }}</button></footer>
        </section>
      </div>
      <div v-if="selectedGame" class="reference-overlay" @click.self="closeGame" @keydown.esc="closeGame">
        <section class="reference-dialog" role="dialog" aria-modal="true" :aria-label="selectedGame.name">
          <header class="reference-dialog-head"><div><h2>{{ selectedGame.name }}</h2><p>{{ categoryLabel(selectedGame.category) }} · {{ selectedGame.id }}</p></div><button type="button" class="reference-button" autofocus aria-label="关闭参考游戏详情" @click="closeGame">关闭 ×</button></header>
          <div class="reference-detail-body">
            <p v-if="detailLoading" role="status">正在读取游戏详情…</p>
            <p v-if="detailError" class="reference-error" role="alert">{{ detailError }}</p>
            <p class="reference-detail-description">{{ selectedGame.description }}</p>
            <p v-if="selectedGame.introduction && selectedGame.introduction !== selectedGame.description" class="reference-detail-description">{{ selectedGame.introduction }}</p>
            <p class="reference-package-note" :class="selectedGame.package_status">{{ selectedGame.package_note || (selectedGame.package_status === 'present' ? '本地目录存在原包；是否完整可运行需另行验证。' : '当前本地目录缺少原包，可浏览已有信息与素材。') }}</p>
            <p v-if="selectedGame.package">本地包：{{ selectedGame.package.name }} · {{ formatBytes(selectedGame.package.bytes) }}。添加参考时同时加入原包路径。</p>
            <p v-else>当前只能添加游戏信息；尚未提供可供 Agent 分析的原包。</p>
            <div class="reference-paths"><span>游戏信息路径</span><code>{{ selectedGame.reference_path }}</code><span>本地资料目录</span><code>{{ selectedGame.directory_reference_path }}</code></div>
            <template v-if="selectedGame.assets?.length">
              <h3>商店素材</h3>
              <div class="reference-assets"><button v-for="asset in selectedGame.assets" :key="asset.name" type="button" :class="{ selected: selectedAsset?.name === asset.name }" @click="selectedAsset = asset"><img :src="asset.url" :alt="assetLabel(asset)" loading="lazy" /><span>{{ assetLabel(asset) }}</span></button></div>
              <figure v-if="selectedAsset" class="reference-asset-preview"><img :src="selectedAsset.url" :alt="assetLabel(selectedAsset)" /><figcaption>{{ selectedAsset.name }} · {{ formatBytes(selectedAsset.bytes) }}</figcaption></figure>
            </template>
          </div>
          <footer v-if="compact" class="reference-dialog-foot"><button type="button" class="reference-button primary" :disabled="isSelected(selectedGame) || !selectedGame.reference_path" @click="chooseGame(selectedGame)">{{ isSelected(selectedGame) ? '已添加到参考资料' : '添加到参考资料' }}</button></footer>
        </section>
      </div>
    </Teleport>
  </section>
</template>

<style scoped>
.reference-library { --reference-bg: var(--bg-card, #fff); --reference-text: var(--text-primary, #334534); --reference-muted: var(--text-secondary, #6c7e63); --reference-border: var(--border-color, #dce3d4); color: var(--reference-text); }
.reference-research { margin-top: 12px; }
.reference-document-list { max-height: 260px; overflow-y: auto; list-style: none; padding: 0; }
.reference-document-list li { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 5px 0; }
.reference-document-link { min-width: 0; color: inherit; background: none; border: 0; text-align: left; font: inherit; text-decoration: underline; cursor: pointer; overflow-wrap: anywhere; }
.reference-document-content { white-space: pre-wrap; overflow-wrap: anywhere; font: inherit; line-height: 1.9; }
.reference-heading,.reference-card-foot,.reference-dialog-head,.reference-dialog-foot { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.reference-heading h2,.reference-dialog-head h2 { font-size: 19px; margin: 0; }
.reference-heading p,.reference-dialog-head p { font-size: 12px; line-height: 1.7; margin: 7px 0 0; color: var(--reference-muted); }
.reference-button { border: 1px solid var(--reference-border, #dce3d4); border-radius: 6px; padding: 7px 10px; color: inherit; font: inherit; font-size: 12px; background: var(--reference-bg, #fff); cursor: pointer; white-space: nowrap; }
.reference-button:disabled { opacity: .5; cursor: default; }.reference-button.primary { background: #3565d2; color: #fff; border-color: #3565d2; }
.reference-stats { display: flex; gap: 12px 24px; flex-wrap: wrap; margin: 20px 0; font-size: 12px; color: var(--reference-muted); }.reference-stats strong { color: var(--reference-text); font-size: 17px; }
.reference-source-notes { padding: 12px; margin-bottom: 15px; border: 1px solid var(--reference-border); border-radius: 6px; font-size: 12px; line-height: 1.7; }.reference-source-notes summary { cursor: pointer; }.reference-source-notes p { margin: 10px 0 0; }.reference-source-notes code { display: block; overflow-wrap: anywhere; color: var(--reference-muted); }
.reference-filters { display: flex; gap: 10px; flex-wrap: wrap; }.reference-filters input,.reference-filters select { margin: 0; font: inherit; font-size: 12px; line-height: 1.6; color: inherit; background: var(--reference-bg); border: 1px solid var(--reference-border); border-radius: 6px; padding: 9px 11px; width: auto; }.reference-filters input { flex: 1; min-width: 180px; }
.reference-result-count { margin: 12px 0; font-size: 12px; color: var(--reference-muted); }.reference-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr)); gap: 12px; }
.reference-game { border: 1px solid var(--reference-border); border-radius: 9px; background: var(--reference-bg); padding: 14px; min-width: 0; }.reference-game-main { display: flex; align-items: center; text-align: left; gap: 12px; width: 100%; color: inherit; border: 0; background: none; padding: 0; cursor: pointer; }.reference-game-main img,.reference-game-placeholder { width: 56px; height: 56px; object-fit: cover; border-radius: 12px; flex-shrink: 0; }.reference-game-placeholder { display: grid; place-items: center; background: #aabbaa20; font-size: 24px; }.reference-game-copy { min-width: 0; }.reference-game-copy strong { display: block; font-size: 14px; overflow-wrap: anywhere; }.reference-game-copy small { display: block; font-size: 11px; color: var(--reference-muted); margin-top: 6px; }
.reference-description { font-size: 12px; line-height: 1.7; color: var(--reference-muted); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 3.4em; margin: 12px 0; }.reference-card-foot { margin-top: 12px; }.reference-package-status { font-size: 11px; color: #aa8241; }.reference-package-status.present { color: #4b8a63; }
.reference-empty { text-align: center; color: var(--reference-muted); font-size: 13px; padding: 35px 15px; }.reference-error { color: #b8644e; font-size: 12px; line-height: 1.8; }.compact .reference-heading h2 { font-size: 14px; }.compact .reference-stats { margin: 12px 0; gap: 8px 18px; }.compact .reference-stats strong { font-size: 13px; }.compact .reference-grid { max-height: 330px; overflow-y: auto; padding-right: 3px; grid-template-columns: repeat(auto-fill, minmax(min(100%, 250px), 1fr)); }
.reference-overlay { position: fixed; z-index: 2000; inset: 0; background: #0008; display: flex; align-items: center; justify-content: center; padding: 20px; color: var(--text-primary, #334534); }.reference-dialog { --reference-bg: var(--bg-card, #fff); --reference-border: var(--border-color, #dce3d4); --reference-muted: var(--text-secondary, #6c7e63); background: var(--reference-bg); border: 1px solid var(--reference-border); border-radius: 12px; width: min(980px, 100%); max-height: 92vh; display: flex; flex-direction: column; }.reference-dialog-head { border-bottom: 1px solid var(--reference-border); padding: 20px; }.reference-detail-body { overflow-y: auto; padding: 20px; font-size: 13px; line-height: 1.8; }.reference-detail-description { white-space: pre-wrap; }.reference-package-note { padding: 10px 12px; border: 1px solid #c496493c; background: #c4964910; border-radius: 6px; }.reference-paths { display: grid; gap: 5px; padding: 12px 0; }.reference-paths span { color: var(--reference-muted); font-size: 11px; }.reference-paths code { overflow-wrap: anywhere; font-size: 11px; }.reference-assets { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 10px; }.reference-assets button { flex-shrink: 0; border: 1px solid var(--reference-border); border-radius: 6px; padding: 5px; background: var(--reference-bg); color: inherit; cursor: pointer; width: 100px; }.reference-assets button.selected { border-color: #4d81cd; }.reference-assets img { display: block; width: 88px; height: 76px; object-fit: contain; }.reference-assets span { display: block; overflow-wrap: anywhere; font-size: 11px; margin-top: 6px; }.reference-asset-preview { margin: 15px 0 0; text-align: center; border: 1px solid var(--reference-border); border-radius: 8px; padding: 12px; }.reference-asset-preview img { max-width: 100%; max-height: 470px; object-fit: contain; }.reference-asset-preview figcaption { color: var(--reference-muted); font-size: 11px; overflow-wrap: anywhere; }.reference-dialog-foot { justify-content: flex-end; padding: 15px 20px; border-top: 1px solid var(--reference-border); }
@media(max-width:600px) { .reference-heading { align-items: flex-start; }.reference-heading h2 { font-size: 16px; }.reference-stats { gap: 10px 16px; }.reference-filters select { flex: 1; min-width: 120px; }.reference-filters input { width: 100%; flex-basis: 100%; }.reference-overlay { padding: 8px; }.reference-dialog-head,.reference-detail-body { padding: 14px; }.reference-dialog-head h2 { font-size: 16px; } }
</style>
