<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  KB_MODULES,
  countItemsInFolder,
  ensureKbLoaded,
  getCategoryLabel,
  getFoldersOf,
  getKbFolder,
  getKbItem,
  getKbModuleMeta,
  kbStore,
  makeKbFolderKey,
  makeKbKey,
  parseKbKey,
  ragSearch,
} from '../../data/knowledgeBase.js'
import { kbRawUrl } from '../../api/knowledge.js'

const props = defineProps({
  // 已选引用 key 列表，新版格式 `${module}:${category}:${itemId}`，
  // 兼容旧版 `${module}:${itemId}`（getKbItem 会回退查找）。
  modelValue: { type: Array, default: () => [] },
  // 紧凑样式（在窄面板中使用，例如策划 InputPanel 内嵌）
  dense: { type: Boolean, default: false },
  // 标题色，默认深色主题文本
  accent: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const showPicker = ref(false)
const searchQuery = ref('')
// null = 还未触发 RAG；[] = 触发但无命中；非空 = 命中列表
const ragHits = ref(null)

// ---- 分级导航状态 ----
// nav 是当前所在路径：null = 主页（4 个模块卡片）
// 单层结构：{ moduleId, category?, folder? }
//   只填 moduleId            → 第 1 级，列分类
//   moduleId + category      → 第 2 级，分类根目录
//   三者全填                 → 第 3+ 级，子文件夹（folder 是相对 category 的路径）
const nav = ref(null)

function navHome() {
  nav.value = null
}
function navToModule(moduleId) {
  nav.value = { moduleId }
}
function navToCategory(moduleId, category) {
  nav.value = { moduleId, category, folder: '' }
}
function navToFolder(moduleId, category, folderPath) {
  nav.value = { moduleId, category, folder: folderPath || '' }
}

// 计算当前导航层级：home / module / folder
const navLevel = computed(() => {
  if (!nav.value) return 'home'
  if (!nav.value.category) return 'module'
  return 'folder'
})

// 当前导航位置可显示的"模块卡片" / "分类卡片" / "文件夹卡片" / "文件卡片"
// 模块层
const homeModules = computed(() => KB_MODULES)

// 模块下分类（带计数）
const moduleCategories = computed(() => {
  if (navLevel.value !== 'module') return []
  const moduleId = nav.value.moduleId
  const cats = kbStore.modulesMap[moduleId] || []
  return cats.map((cat) => ({
    moduleId,
    category: cat,
    label: getCategoryLabel(cat),
    fileCount: kbStore.items.filter(
      (it) => it.moduleId === moduleId && it.category === cat
    ).length,
    folderCount: getFoldersOf(moduleId, cat).length,
  }))
})

// 当前位置直接子文件夹（path 中相对于当前 folder 没有再下一级 /）
const childFolders = computed(() => {
  if (navLevel.value !== 'folder') return []
  const { moduleId, category, folder } = nav.value
  const all = getFoldersOf(moduleId, category)
  if (!folder) {
    return all.filter((f) => !f.path.includes('/'))
  }
  const prefix = folder + '/'
  return all.filter((f) => {
    if (!f.path.startsWith(prefix)) return false
    return !f.path.slice(prefix.length).includes('/')
  })
})

// 当前位置直属文件（folder 完全等于当前 nav.folder）
const directFiles = computed(() => {
  if (navLevel.value !== 'folder') return []
  const { moduleId, category, folder } = nav.value
  return kbStore.items.filter(
    (it) =>
      it.moduleId === moduleId &&
      it.category === category &&
      it.folder === folder
  )
})

// 面包屑：home → module → category → 各级 folder
const breadcrumbs = computed(() => {
  const out = [{ kind: 'home', label: '📚 全部' }]
  if (!nav.value) return out
  const meta = getKbModuleMeta(nav.value.moduleId)
  out.push({ kind: 'module', label: meta.name, moduleId: nav.value.moduleId })
  if (nav.value.category) {
    out.push({
      kind: 'category',
      label: getCategoryLabel(nav.value.category),
      moduleId: nav.value.moduleId,
      category: nav.value.category,
    })
    if (nav.value.folder) {
      const segs = nav.value.folder.split('/')
      let acc = ''
      for (const s of segs) {
        acc = acc ? `${acc}/${s}` : s
        out.push({
          kind: 'folder',
          label: s,
          moduleId: nav.value.moduleId,
          category: nav.value.category,
          folder: acc,
        })
      }
    }
  }
  return out
})

// 是否搜索模式：搜索框非空时切到扁平搜索结果
const inSearchMode = computed(() => searchQuery.value.trim().length > 0)

// 把已选 key 还原为可渲染的条目（file -> KbItem，folder -> KbFolder）
// 每条多带一个 _kind 字段方便模板分支
const selectedRefs = computed(() => {
  const out = []
  for (const key of props.modelValue) {
    const parsed = parseKbKey(key)
    if (!parsed) continue
    if (parsed.kind === 'file') {
      const it = getKbItem(key)
      if (it) out.push({ _kind: 'file', _key: key, ...it })
    } else {
      const f = getKbFolder(key)
      if (f) {
        const cnt = countItemsInFolder(f.moduleId, f.category, f.path)
        out.push({ _kind: 'folder', _key: key, _count: cnt, ...f })
      }
    }
  }
  return out
})

// 已选区里图片 / 文档 / 文件夹分组
const selectedImages = computed(() =>
  selectedRefs.value.filter((it) => it._kind === 'file' && isImage(it))
)
const selectedDocs = computed(() =>
  selectedRefs.value.filter((it) => it._kind === 'file' && !isImage(it))
)
const selectedFolders = computed(() =>
  selectedRefs.value.filter((it) => it._kind === 'folder')
)

// 搜索模式下的扁平结果（folder + file 跨全库）
// 不搜索时返回空，模板里会改走分级 UI
const searchEntries = computed(() => {
  if (!inSearchMode.value) return []
  const q = searchQuery.value.trim().toLowerCase()
  let folderPool = []
  for (const list of Object.values(kbStore.folders)) {
    for (const f of list) folderPool.push({ _kind: 'folder', ...f })
  }
  let filePool = kbStore.items.map((it) => ({ _kind: 'file', ...it }))
  folderPool = folderPool.filter(
    (f) =>
      f.name.toLowerCase().includes(q) ||
      f.path.toLowerCase().includes(q) ||
      (f.desc || '').toLowerCase().includes(q)
  )
  filePool = filePool.filter(
    (it) =>
      it.title.toLowerCase().includes(q) ||
      (it.summary || '').toLowerCase().includes(q) ||
      (it.tags || []).some((t) => t.toLowerCase().includes(q))
  )
  return [...folderPool, ...filePool]
})

// 当前导航位置如果是 folder 层（含 category 根），生成一个 "当前位置作为整目录" 的伪条目
// 用于侧栏顶部的"引用当前文件夹"按钮 —— folder='' 即等同选整个分类
const currentFolderEntry = computed(() => {
  if (navLevel.value !== 'folder') return null
  const { moduleId, category, folder } = nav.value
  return {
    _kind: 'folder',
    moduleId,
    category,
    path: folder,
    name: folder ? folder.split('/').pop() : `${getCategoryLabel(category)} 根目录`,
    desc: folder
      ? (getKbFolder(makeKbFolderKey(moduleId, category, folder))?.desc || '')
      : `${getKbModuleMeta(moduleId).name} · ${getCategoryLabel(category)} 全部内容`,
  }
})

function entryKey(entry) {
  if (entry._kind === 'folder') {
    return makeKbFolderKey(entry.moduleId, entry.category, entry.path)
  }
  return makeKbKey(entry)
}

function isSelected(entry) {
  return props.modelValue.includes(entryKey(entry))
}

function toggleSelect(entry) {
  const key = entryKey(entry)
  const next = isSelected(entry)
    ? props.modelValue.filter((k) => k !== key)
    : [...props.modelValue, key]
  emit('update:modelValue', next)
}

function removeRef(key) {
  emit('update:modelValue', props.modelValue.filter((k) => k !== key))
}

function clearAll() {
  emit('update:modelValue', [])
}

// 触发 RAG 检索：选取 Top 3 自动加入引用，便于演示效果
function runRag() {
  const hits = ragSearch(searchQuery.value, 3)
  ragHits.value = hits
  const next = [...props.modelValue]
  for (const it of hits) {
    const key = makeKbKey(it)
    if (!next.includes(key)) next.push(key)
  }
  emit('update:modelValue', next)
}

function openPicker() {
  showPicker.value = true
  ragHits.value = null
  // 每次打开 picker 都从主页起步，避免上次点到的层级残留
  nav.value = null
  searchQuery.value = ''
}

function closePicker() {
  showPicker.value = false
}

// 是否图片：优先 contentType，回退按扩展名
const IMAGE_EXT_RE = /\.(png|jpe?g|gif|webp|bmp|svg|avif)$/i
function isImage(item) {
  if (!item) return false
  if (item.contentType?.startsWith('image/')) return true
  return IMAGE_EXT_RE.test(item.filename || '')
}

// 拼 inline URL，缩略图与 lightbox 共用
function inlineUrl(item) {
  return kbRawUrl(item.moduleId, item.category, item.id)
}

// Lightbox：null = 关闭
const previewItem = ref(null)
function openPreview(item) {
  previewItem.value = item
}
function closePreview() {
  previewItem.value = null
}
</script>

<template>
  <div class="kb-ref" :class="{ dense }">
    <div class="kb-head">
      <span class="kb-title">📚 知识库引用</span>
      <span class="kb-count" :class="{ has: selectedRefs.length }">
        {{ selectedRefs.length }}
      </span>
      <div class="kb-actions">
        <button
          v-if="selectedRefs.length"
          class="kb-link-btn"
          type="button"
          @click="clearAll"
        >
          清空
        </button>
        <button class="kb-add-btn" type="button" @click="openPicker">
          + 选择 / 检索
        </button>
      </div>
    </div>

    <div v-if="selectedRefs.length" class="kb-selected">
      <!-- 已选文件夹：以 chip 形式呈现，标注递归文件数 -->
      <div v-if="selectedFolders.length" class="kb-chips">
        <span
          v-for="f in selectedFolders"
          :key="f._key"
          class="kb-chip kb-chip-folder"
          :style="{
            borderColor: getKbModuleMeta(f.moduleId).color,
            color: getKbModuleMeta(f.moduleId).color,
          }"
          :title="f.desc"
        >
          <span class="kb-chip-icon">📁</span>
          <span class="kb-chip-mod">{{ getKbModuleMeta(f.moduleId).name }}</span>
          <span class="kb-chip-sep">·</span>
          <span class="kb-chip-name">
            {{ f.path || '(根目录)' }}
            <em class="kb-chip-num">{{ f._count }} 份</em>
          </span>
          <button
            class="kb-chip-x"
            type="button"
            title="移除引用"
            @click="removeRef(f._key)"
          >
            ×
          </button>
        </span>
      </div>

      <!-- 图片缩略图（点击放大）-->
      <div v-if="selectedImages.length" class="kb-thumbs">
        <div
          v-for="item in selectedImages"
          :key="item._key"
          class="kb-thumb"
          :style="{ borderColor: getKbModuleMeta(item.moduleId).color }"
          :title="item.title + (item.summary ? ' — ' + item.summary : '')"
        >
          <img
            :src="inlineUrl(item)"
            :alt="item.title"
            loading="lazy"
            @click="openPreview(item)"
          />
          <span
            class="kb-thumb-mod"
            :style="{ background: getKbModuleMeta(item.moduleId).color }"
          >
            {{ getKbModuleMeta(item.moduleId).icon }}
          </span>
          <button
            class="kb-thumb-x"
            type="button"
            title="移除引用"
            @click="removeRef(item._key)"
          >
            ×
          </button>
          <div class="kb-thumb-cap">{{ item.title }}</div>
        </div>
      </div>

      <!-- 非图片：文字 chip -->
      <div v-if="selectedDocs.length" class="kb-chips">
        <span
          v-for="item in selectedDocs"
          :key="item._key"
          class="kb-chip"
          :style="{
            borderColor: getKbModuleMeta(item.moduleId).color,
            color: getKbModuleMeta(item.moduleId).color,
          }"
          :title="item.summary"
        >
          <span class="kb-chip-icon">{{ getKbModuleMeta(item.moduleId).icon }}</span>
          <span class="kb-chip-mod">{{ getKbModuleMeta(item.moduleId).name }}</span>
          <span class="kb-chip-sep">·</span>
          <span class="kb-chip-name">{{ item.title }}</span>
          <button
            class="kb-chip-x"
            type="button"
            title="移除引用"
            @click="removeRef(item._key)"
          >
            ×
          </button>
        </span>
      </div>
    </div>
    <div v-else-if="kbStore.loading" class="kb-empty">正在加载知识库…</div>
    <div v-else-if="kbStore.error" class="kb-empty kb-error">
      ⚠ {{ kbStore.error }}
    </div>
    <div v-else class="kb-empty">
      未引用任何知识。可手动从 4 个模块的知识库选择，或输入关键词触发 RAG 自动检索。
    </div>

    <!-- 浮层选择器：脱离当前列宽限制 -->
    <Teleport to="body">
      <div v-if="showPicker" class="kb-overlay" @click.self="closePicker">
        <div class="kb-picker">
          <header class="kb-picker-head">
            <div>
              <strong>从知识库添加引用</strong>
              <span class="kb-picker-sub">
                支持人工筛选与基于关键词的 RAG 自动检索（Top 3）
              </span>
            </div>
            <button class="kb-close" type="button" @click="closePicker">×</button>
          </header>

          <div class="kb-search-row">
            <input
              v-model="searchQuery"
              class="kb-search"
              placeholder="🔍 输入关键词进行筛选 / 触发 RAG 检索…"
              @keyup.enter="runRag"
            />
            <button
              class="kb-rag-btn"
              type="button"
              :disabled="!searchQuery.trim()"
              title="基于关键词在 4 个模块的知识库中智能检索 Top 3 并自动加入引用"
              @click="runRag"
            >
              🔮 RAG 检索
            </button>
          </div>

          <div
            v-if="ragHits && ragHits.length"
            class="kb-rag-banner"
          >
            <span class="kb-rag-tag">RAG</span>
            <span>
              已自动加入
              <strong>{{ ragHits.length }}</strong>
              条相关知识：
              <span
                v-for="(r, i) in ragHits"
                :key="r.id"
                class="kb-rag-hit"
                :style="{ color: getKbModuleMeta(r.moduleId).color }"
              >
                {{ i > 0 ? '、' : '' }}{{ r.title }}
                <em>({{ getKbModuleMeta(r.moduleId).name }})</em>
              </span>
            </span>
          </div>
          <div
            v-else-if="ragHits && !ragHits.length"
            class="kb-rag-banner empty"
          >
            <span class="kb-rag-tag">RAG</span>
            未命中相关知识，可调整关键词重试，或在下方人工挑选。
          </div>

          <!-- 面包屑导航 -->
          <div v-if="!inSearchMode" class="kb-crumbs">
            <template v-for="(b, i) in breadcrumbs" :key="i">
              <button
                class="kb-crumb"
                :class="{ active: i === breadcrumbs.length - 1 }"
                type="button"
                @click="
                  b.kind === 'home' ? navHome() :
                  b.kind === 'module' ? navToModule(b.moduleId) :
                  b.kind === 'category' ? navToCategory(b.moduleId, b.category) :
                  navToFolder(b.moduleId, b.category, b.folder)
                "
              >
                {{ b.label }}
              </button>
              <span v-if="i < breadcrumbs.length - 1" class="kb-crumb-sep">/</span>
            </template>
          </div>

          <div class="kb-list">
            <div v-if="kbStore.loading" class="kb-list-empty">正在加载…</div>
            <div v-else-if="kbStore.error" class="kb-list-empty">
              ⚠ {{ kbStore.error }}
            </div>

            <!-- 搜索模式：扁平结果（folder + file 跨全库） -->
            <template v-else-if="inSearchMode">
              <div v-if="!searchEntries.length" class="kb-list-empty">
                未匹配到内容，可调整关键词或清空搜索回到分级浏览
              </div>
              <button
                v-for="entry in searchEntries"
                :key="entryKey(entry)"
                class="kb-item"
                :class="{
                  selected: isSelected(entry),
                  'kb-item-folder': entry._kind === 'folder',
                }"
                type="button"
                @click="toggleSelect(entry)"
              >
                <span class="kb-item-check" :class="{ on: isSelected(entry) }">
                  {{ isSelected(entry) ? '✓' : '' }}
                </span>
                <span
                  v-if="entry._kind === 'folder'"
                  class="kb-item-icon"
                  :style="{ color: getKbModuleMeta(entry.moduleId).color }"
                >
                  📁
                </span>
                <span v-else-if="isImage(entry)" class="kb-item-thumb">
                  <img :src="inlineUrl(entry)" :alt="entry.title" loading="lazy" />
                </span>
                <span
                  v-else
                  class="kb-item-icon"
                  :style="{ color: getKbModuleMeta(entry.moduleId).color }"
                >
                  {{ getKbModuleMeta(entry.moduleId).icon }}
                </span>
                <div class="kb-item-body">
                  <div class="kb-item-title">
                    <strong>
                      {{ entry._kind === 'folder' ? entry.path || '(根目录)' : entry.title }}
                    </strong>
                    <span
                      class="kb-item-mod"
                      :style="{
                        color: getKbModuleMeta(entry.moduleId).color,
                        borderColor: getKbModuleMeta(entry.moduleId).color,
                      }"
                    >
                      {{ getKbModuleMeta(entry.moduleId).name }} · {{ entry.category }}
                      <template v-if="entry._kind === 'folder'">· 文件夹</template>
                    </span>
                  </div>
                  <div class="kb-item-summary">
                    <template v-if="entry._kind === 'folder'">
                      {{ entry.desc || '（无描述）' }}
                    </template>
                    <template v-else>{{ entry.summary }}</template>
                  </div>
                  <div class="kb-item-foot">
                    <template v-if="entry._kind === 'folder'">
                      <span class="kb-tag">
                        📦 含 {{ countItemsInFolder(entry.moduleId, entry.category, entry.path) }} 份文件
                      </span>
                    </template>
                    <template v-else>
                      <span v-for="tag in entry.tags" :key="tag" class="kb-tag">#{{ tag }}</span>
                      <span class="kb-item-time">更新 {{ entry.updatedAt }}</span>
                    </template>
                  </div>
                </div>
              </button>
            </template>

            <!-- 第 0 级：4 个模块卡片 -->
            <template v-else-if="navLevel === 'home'">
              <div class="kb-section-title">选择一个模块进入</div>
              <button
                v-for="m in homeModules"
                :key="m.id"
                class="kb-nav-card"
                type="button"
                :style="{ borderLeftColor: m.color }"
                @click="navToModule(m.id)"
              >
                <span class="kb-nav-icon" :style="{ color: m.color }">{{ m.icon }}</span>
                <span class="kb-nav-body">
                  <strong>{{ m.name }}</strong>
                  <span class="kb-nav-sub">
                    共 {{ kbStore.items.filter((it) => it.moduleId === m.id).length }} 份文件
                  </span>
                </span>
                <span class="kb-nav-go">›</span>
              </button>
            </template>

            <!-- 第 1 级：分类卡片 -->
            <template v-else-if="navLevel === 'module'">
              <div class="kb-section-title">
                {{ getKbModuleMeta(nav.moduleId).name }} 的分类
              </div>
              <button
                v-for="c in moduleCategories"
                :key="c.category"
                class="kb-nav-card"
                type="button"
                :style="{ borderLeftColor: getKbModuleMeta(nav.moduleId).color }"
                @click="navToCategory(c.moduleId, c.category)"
              >
                <span
                  class="kb-nav-icon"
                  :style="{ color: getKbModuleMeta(nav.moduleId).color }"
                >📂</span>
                <span class="kb-nav-body">
                  <strong>{{ c.label }}</strong>
                  <span class="kb-nav-sub">
                    {{ c.fileCount }} 份文件 · {{ c.folderCount }} 个文件夹
                  </span>
                </span>
                <span class="kb-nav-go">›</span>
              </button>
              <div v-if="!moduleCategories.length" class="kb-list-empty">
                当前模块下未配置任何分类
              </div>
            </template>

            <!-- 第 2+ 级：文件夹层 -->
            <template v-else>
              <!-- 引用当前位置整目录的快捷按钮 -->
              <div
                v-if="currentFolderEntry"
                class="kb-current-folder"
                :class="{ selected: isSelected(currentFolderEntry) }"
              >
                <div class="kb-current-info">
                  <span class="kb-current-icon">📌</span>
                  <div>
                    <strong>引用当前位置整目录</strong>
                    <div class="kb-current-sub">
                      {{ currentFolderEntry.desc }}
                      · 递归
                      {{ countItemsInFolder(
                        currentFolderEntry.moduleId,
                        currentFolderEntry.category,
                        currentFolderEntry.path
                      ) }}
                      份文件
                    </div>
                  </div>
                </div>
                <button
                  class="kb-current-btn"
                  type="button"
                  @click="toggleSelect(currentFolderEntry)"
                >
                  {{ isSelected(currentFolderEntry) ? '✓ 已选' : '+ 选取' }}
                </button>
              </div>

              <!-- 子文件夹卡片 -->
              <div v-if="childFolders.length" class="kb-section-title">
                子文件夹（{{ childFolders.length }}）
              </div>
              <div
                v-for="f in childFolders"
                :key="f.path"
                class="kb-nav-card kb-nav-folder"
                :style="{ borderLeftColor: getKbModuleMeta(f.moduleId).color }"
              >
                <button
                  class="kb-nav-main"
                  type="button"
                  @click="navToFolder(f.moduleId, f.category, f.path)"
                >
                  <span
                    class="kb-nav-icon"
                    :style="{ color: getKbModuleMeta(f.moduleId).color }"
                  >📁</span>
                  <span class="kb-nav-body">
                    <strong>{{ f.name }}</strong>
                    <span class="kb-nav-sub">
                      {{ countItemsInFolder(f.moduleId, f.category, f.path) }} 份文件
                      <template v-if="f.desc">· {{ f.desc }}</template>
                    </span>
                  </span>
                </button>
                <button
                  class="kb-nav-add"
                  type="button"
                  :class="{ on: isSelected({ _kind: 'folder', ...f }) }"
                  :title="isSelected({ _kind: 'folder', ...f }) ? '已引用整目录' : '引用整目录'"
                  @click="toggleSelect({ _kind: 'folder', ...f })"
                >
                  {{ isSelected({ _kind: 'folder', ...f }) ? '✓' : '+' }}
                </button>
              </div>

              <!-- 当前位置直属文件 -->
              <div v-if="directFiles.length" class="kb-section-title">
                当前位置文件（{{ directFiles.length }}）
              </div>
              <button
                v-for="item in directFiles"
                :key="item.id"
                class="kb-item"
                :class="{ selected: isSelected({ _kind: 'file', ...item }) }"
                type="button"
                @click="toggleSelect({ _kind: 'file', ...item })"
              >
                <span
                  class="kb-item-check"
                  :class="{ on: isSelected({ _kind: 'file', ...item }) }"
                >
                  {{ isSelected({ _kind: 'file', ...item }) ? '✓' : '' }}
                </span>
                <span v-if="isImage(item)" class="kb-item-thumb">
                  <img :src="inlineUrl(item)" :alt="item.title" loading="lazy" />
                </span>
                <span
                  v-else
                  class="kb-item-icon"
                  :style="{ color: getKbModuleMeta(item.moduleId).color }"
                >
                  {{ getKbModuleMeta(item.moduleId).icon }}
                </span>
                <div class="kb-item-body">
                  <div class="kb-item-title">
                    <strong>{{ item.title }}</strong>
                  </div>
                  <div class="kb-item-summary">{{ item.summary }}</div>
                  <div class="kb-item-foot">
                    <span v-for="tag in item.tags" :key="tag" class="kb-tag">#{{ tag }}</span>
                    <span class="kb-item-time">更新 {{ item.updatedAt }}</span>
                  </div>
                </div>
              </button>

              <div
                v-if="!childFolders.length && !directFiles.length"
                class="kb-list-empty"
              >
                此位置暂无子文件夹与直属文件，可去「知识库管理」上传内容
              </div>
            </template>
          </div>

          <footer class="kb-picker-foot">
            <span>
              已选择
              <strong>{{ selectedRefs.length }}</strong>
              条引用
            </span>
            <button class="kb-done" type="button" @click="closePicker">
              完成
            </button>
          </footer>
        </div>
      </div>
    </Teleport>

    <!-- 图片放大预览 -->
    <Teleport to="body">
      <div v-if="previewItem" class="kb-lb" @click.self="closePreview">
        <div class="kb-lb-frame">
          <header class="kb-lb-head">
            <strong>{{ previewItem.title }}</strong>
            <span class="kb-lb-sub">{{ previewItem.filename }}</span>
            <button class="kb-close" type="button" @click="closePreview">×</button>
          </header>
          <div class="kb-lb-body">
            <img :src="inlineUrl(previewItem)" :alt="previewItem.title" />
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.kb-ref {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.kb-ref.dense {
  padding: 10px;
}

.kb-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kb-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

.kb-count {
  display: inline-grid;
  place-items: center;
  min-width: 22px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--bg-card);
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 600;
  border: 1px solid var(--border-color);
}

.kb-count.has {
  background: rgba(63, 185, 80, 0.15);
  color: var(--accent-green);
  border-color: rgba(63, 185, 80, 0.4);
}

.kb-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.kb-link-btn {
  font-size: 11px;
  color: var(--text-tertiary);
  background: transparent;
  border: none;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  transition: color 0.15s;
}

.kb-link-btn:hover {
  color: var(--text-primary);
}

.kb-add-btn {
  font-size: 12px;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  font-weight: 500;
  transition: all 0.15s;
}

.kb-add-btn:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.kb-selected {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kb-thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.kb-thumb {
  position: relative;
  width: 64px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 3px;
  overflow: visible;
}

.kb-ref.dense .kb-thumb {
  width: 56px;
}

.kb-thumb img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 3px;
  cursor: zoom-in;
  display: block;
  background: var(--bg-tertiary);
}

.kb-thumb-mod {
  position: absolute;
  top: 1px;
  left: 1px;
  width: 16px;
  height: 16px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-size: 9px;
  color: #fff;
  box-shadow: 0 0 0 1px var(--bg-card);
  pointer-events: none;
}

.kb-thumb-x {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  font-size: 12px;
  line-height: 1;
  display: grid;
  place-items: center;
}

.kb-thumb-x:hover {
  background: var(--accent-red, #f85149);
  color: #fff;
  border-color: transparent;
}

.kb-thumb-cap {
  font-size: 10px;
  line-height: 1.2;
  color: var(--text-secondary);
  text-align: center;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  word-break: break-all;
}

.kb-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.kb-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  padding: 3px 6px 3px 8px;
  font-size: 11px;
  background: var(--bg-card);
  border: 1px solid;
  border-radius: 999px;
  line-height: 1.2;
}

.kb-chip-icon {
  font-size: 11px;
}

.kb-chip-mod {
  font-weight: 600;
  font-size: 10px;
  letter-spacing: 0.2px;
}

.kb-chip-sep {
  opacity: 0.5;
}

.kb-chip-name {
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}

.kb-chip-x {
  width: 16px;
  height: 16px;
  display: inline-grid;
  place-items: center;
  border-radius: 50%;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 14px;
  line-height: 1;
  border: none;
  margin-left: 2px;
}

.kb-chip-x:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* 文件夹 chip：在标题旁补一条文件数 */
.kb-chip-num {
  font-style: normal;
  opacity: 0.7;
  font-size: 10px;
  margin-left: 4px;
}

.kb-chip-folder .kb-chip-name {
  max-width: 220px;
}

/* picker 列表中文件夹行：背景轻微着色，便于和文件区分 */
.kb-item.kb-item-folder {
  background: rgba(255, 196, 0, 0.04);
}

.kb-item.kb-item-folder:hover {
  background: rgba(255, 196, 0, 0.08);
}

.kb-empty {
  font-size: 11px;
  color: var(--text-tertiary);
  line-height: 1.5;
  padding: 4px 0 2px;
}

.kb-empty.kb-error {
  color: var(--accent-red, #f85149);
}

/* 浮层 */
.kb-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(5, 8, 12, 0.65);
  display: grid;
  place-items: center;
  padding: 24px;
  backdrop-filter: blur(2px);
}

.kb-picker {
  width: min(720px, 100%);
  max-height: 86vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.55);
  overflow: hidden;
}

.kb-picker-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}

.kb-picker-head strong {
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 600;
}

.kb-picker-sub {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.kb-close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  font-size: 18px;
  line-height: 1;
}

.kb-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.kb-search-row {
  display: flex;
  gap: 8px;
  padding: 14px 20px 8px;
}

.kb-search {
  flex: 1;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.kb-search:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.15);
}

.kb-rag-btn {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid transparent;
  transition: all 0.15s;
  white-space: nowrap;
}

.kb-rag-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(188, 140, 255, 0.3);
}

.kb-rag-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.kb-rag-banner {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0 20px 8px;
  padding: 8px 12px;
  background: rgba(188, 140, 255, 0.08);
  border: 1px solid rgba(188, 140, 255, 0.3);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.kb-rag-banner.empty {
  background: var(--bg-card);
  border-color: var(--border-color);
  color: var(--text-tertiary);
}

.kb-rag-tag {
  flex-shrink: 0;
  padding: 1px 8px;
  background: rgba(188, 140, 255, 0.2);
  border: 1px solid rgba(188, 140, 255, 0.4);
  color: var(--accent-purple);
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  align-self: center;
}

.kb-rag-hit em {
  font-style: normal;
  opacity: 0.7;
  font-size: 11px;
}

.kb-tabs {
  display: flex;
  gap: 6px;
  padding: 4px 20px 10px;
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
}

.kb-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  color: var(--text-secondary);
  font-size: 12px;
  transition: all 0.15s;
}

.kb-tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.kb-tab.active {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
  background: rgba(88, 166, 255, 0.08);
}

.kb-tab-num {
  font-size: 10px;
  opacity: 0.6;
  background: var(--bg-tertiary);
  padding: 0 6px;
  border-radius: 999px;
  line-height: 1.6;
}

/* 分级导航：面包屑 */
.kb-crumbs {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 20px 10px;
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
}

.kb-crumb {
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  padding: 3px 10px;
  font-size: 12px;
  color: var(--text-secondary);
  transition: all 0.12s;
}

.kb-crumb:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.kb-crumb.active {
  background: rgba(88, 166, 255, 0.12);
  color: var(--accent-blue);
  border-color: rgba(88, 166, 255, 0.4);
}

.kb-crumb-sep {
  color: var(--text-tertiary);
  font-size: 11px;
}

/* 分级导航：通用卡片（模块/分类/文件夹） */
.kb-section-title {
  font-size: 11px;
  color: var(--text-tertiary);
  letter-spacing: 0.4px;
  margin: 4px 4px 2px;
  text-transform: uppercase;
}

.kb-nav-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-left-width: 3px;
  border-radius: var(--radius-md);
  text-align: left;
  transition: all 0.12s;
  width: 100%;
}

.kb-nav-card:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
}

.kb-nav-folder {
  padding: 0;
  overflow: hidden;
}

.kb-nav-main {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: transparent;
  border: none;
  text-align: left;
  color: inherit;
}

.kb-nav-main:hover {
  background: var(--bg-hover);
}

.kb-nav-add {
  width: 38px;
  flex-shrink: 0;
  background: var(--bg-tertiary);
  border: none;
  border-left: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 16px;
  font-weight: 600;
  align-self: stretch;
  transition: all 0.12s;
}

.kb-nav-add:hover {
  background: var(--accent-blue);
  color: #fff;
}

.kb-nav-add.on {
  background: var(--accent-green);
  color: #fff;
}

.kb-nav-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.kb-nav-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.kb-nav-body strong {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 600;
  word-break: break-all;
}

.kb-nav-sub {
  font-size: 11px;
  color: var(--text-tertiary);
  line-height: 1.4;
}

.kb-nav-go {
  color: var(--text-tertiary);
  font-size: 18px;
  margin-left: 6px;
}

/* 当前位置整目录引用条 */
.kb-current-folder {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(63, 185, 80, 0.08);
  border: 1px dashed rgba(63, 185, 80, 0.45);
  border-radius: var(--radius-md);
  margin-bottom: 4px;
}

.kb-current-folder.selected {
  background: rgba(63, 185, 80, 0.18);
}

.kb-current-info {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.kb-current-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.kb-current-info strong {
  font-size: 12px;
  color: var(--accent-green);
  letter-spacing: 0.3px;
}

.kb-current-sub {
  margin-top: 2px;
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.5;
  word-break: break-all;
}

.kb-current-btn {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  background: var(--accent-green);
  color: #fff;
  border: none;
  font-size: 12px;
  font-weight: 500;
}

.kb-current-btn:hover {
  filter: brightness(1.1);
}

.kb-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.kb-list-empty {
  padding: 32px 12px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
}

.kb-item {
  display: grid;
  grid-template-columns: 24px 32px 1fr;
  gap: 10px;
  padding: 10px 12px;
  text-align: left;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  transition: all 0.12s;
  align-items: flex-start;
}

.kb-item:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
}

.kb-item.selected {
  border-color: var(--accent-green);
  background: rgba(63, 185, 80, 0.06);
}

.kb-item-check {
  width: 22px;
  height: 22px;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  display: grid;
  place-items: center;
  font-size: 13px;
  color: transparent;
  margin-top: 1px;
}

.kb-item-check.on {
  background: var(--accent-green);
  border-color: var(--accent-green);
  color: #fff;
}

.kb-item-icon {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  font-size: 16px;
}

.kb-item-thumb {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  display: block;
  margin-top: -4px; /* 让缩略图和 22px 的图标列在视觉上居中对齐 */
}

.kb-item-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.kb-item-body {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.kb-item-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.kb-item-title strong {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.kb-item-mod {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.3px;
  padding: 1px 6px;
  border-radius: 999px;
  border: 1px solid;
  background: var(--bg-tertiary);
}

.kb-item-summary {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.kb-item-foot {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 2px;
}

.kb-tag {
  font-size: 10px;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  padding: 1px 6px;
  border-radius: 4px;
}

.kb-item-time {
  font-size: 10px;
  color: var(--text-tertiary);
  margin-left: auto;
}

.kb-picker-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  font-size: 12px;
  color: var(--text-secondary);
}

.kb-picker-foot strong {
  color: var(--accent-green);
}

.kb-done {
  padding: 7px 16px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  color: #fff;
  font-size: 12px;
  font-weight: 500;
}

.kb-done:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(88, 166, 255, 0.25);
}

/* Lightbox */
.kb-lb {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.82);
  display: grid;
  place-items: center;
  padding: 32px;
  backdrop-filter: blur(2px);
}

.kb-lb-frame {
  width: min(1100px, 100%);
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
}

.kb-lb-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}

.kb-lb-head strong {
  color: var(--text-primary);
  font-size: 14px;
}

.kb-lb-sub {
  color: var(--text-tertiary);
  font-size: 12px;
  flex: 1;
}

.kb-lb-body {
  flex: 1;
  min-height: 0;
  display: grid;
  place-items: center;
  background: #0a0d12;
  overflow: auto;
  padding: 16px;
}

.kb-lb-body img {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  display: block;
}
</style>
