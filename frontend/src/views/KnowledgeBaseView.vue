<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  KB_MODULES,
  ensureKbLoaded,
  getCategoryLabel,
  getFoldersOf,
  getKbModuleMeta,
  kbStore,
  refreshKb,
} from '../data/knowledgeBase.js'
import {
  createKbFolder as apiCreateFolder,
  deleteKbFolder as apiDeleteFolder,
  deleteKbItem as apiDelete,
  kbRawUrl,
  uploadKbItem as apiUpload,
} from '../api/knowledge.js'

defineEmits(['navigate'])

// 当前选中的模块 / 分类 / 文件夹（默认策划 / docs / 根目录）
const activeModule = ref('planning')
const activeCategory = ref('docs')
// "" 表示分类根目录，与后端 KbItem.folder 语义一致
const activeFolder = ref('')

// 上传表单字段（单文件模式）
const uploadFile = ref(null)
const uploadTitle = ref('')
const uploadSummary = ref('')
const uploadTags = ref('')
// 目标文件夹：默认跟随 activeFolder，但可以在表单里独立切换
const uploadFolder = ref('')
const fileInputRef = ref(null)
const dirInputRef = ref(null)

// 批量（文件夹）模式：用户通过 webkitdirectory 选了整个目录
// 选中后切换 UI：隐藏单文件 title，列文件清单，提交按钮变"上传 N 份"
const batchFiles = ref([]) // [{ file: File, relPath: 'root/sub/leaf.png' }]
const batchRootName = ref('') // 选中的本地根目录名（如 'ART_DELIVERY_...'）
const batchProgress = ref({ done: 0, total: 0, failed: [] }) // 进度状态
// 单次上传请求并发上限：太大会触发浏览器并发连接上限 / 后端瞬时压力
const BATCH_CONCURRENCY = 4

// UI 状态
const uploading = ref(false)
const uploadError = ref('')
const opMessage = ref('') // 操作成功后短暂提示
let opTimer = null

// 当前是否在批量（文件夹）模式
const isBatchMode = computed(() => batchFiles.value.length > 0)

onMounted(() => {
  ensureKbLoaded()
})

// 当前模块允许的分类列表，从后端 modulesMap 拉
const categoriesOfActive = computed(() => {
  return kbStore.modulesMap[activeModule.value] || []
})

// 切换模块时，同步把 category / folder 锁回根，避免出现非法状态
function selectModule(modId) {
  activeModule.value = modId
  const cats = kbStore.modulesMap[modId] || []
  activeCategory.value = cats[0] || 'docs'
  activeFolder.value = ''
  resetUploadForm()
}

function selectCategory(cat) {
  activeCategory.value = cat
  activeFolder.value = ''
  resetUploadForm()
}

function selectFolder(path) {
  activeFolder.value = path || ''
  resetUploadForm()
}

// 当前分类下所有已注册文件夹（含多级）
const allFoldersOfCategory = computed(() =>
  getFoldersOf(activeModule.value, activeCategory.value)
)

// 当前列表：从全量 store 中过滤，匹配 module + category + 当前 folder
const currentItems = computed(() =>
  kbStore.items.filter(
    (it) =>
      it.moduleId === activeModule.value &&
      it.category === activeCategory.value &&
      it.folder === activeFolder.value
  )
)

// 当前 folder 直接子文件夹（即父路径恰好等于 activeFolder）
const childFolders = computed(() => {
  const parent = activeFolder.value
  return allFoldersOfCategory.value.filter((f) => {
    if (parent === '') {
      // 根目录的"子文件夹" = path 中不含 / 的那些
      return !f.path.includes('/')
    }
    const prefix = parent + '/'
    if (!f.path.startsWith(prefix)) return false
    // 直接子级：去掉前缀后不再含 /
    return !f.path.slice(prefix.length).includes('/')
  })
})

// 面包屑：根目录 + 各父级
const breadcrumbs = computed(() => {
  const out = [{ label: '(根目录)', path: '' }]
  if (!activeFolder.value) return out
  const segs = activeFolder.value.split('/')
  let acc = ''
  for (const s of segs) {
    acc = acc ? `${acc}/${s}` : s
    out.push({ label: s, path: acc })
  }
  return out
})

// 各模块各分类的条目计数（统计含所有 folder 的全量）
function moduleCount(modId) {
  return kbStore.items.filter((it) => it.moduleId === modId).length
}

function categoryCount(modId, cat) {
  return kbStore.items.filter(
    (it) => it.moduleId === modId && it.category === cat
  ).length
}

// 单个 folder 的递归条目数（含子文件夹），用于侧栏角标
function folderItemCount(folder) {
  const prefix = folder.path + '/'
  return kbStore.items.filter(
    (it) =>
      it.moduleId === folder.moduleId &&
      it.category === folder.category &&
      (it.folder === folder.path || it.folder.startsWith(prefix))
  ).length
}

// ---- 文件夹增删 ----------------------------------------------------------

const newFolderName = ref('')
const newFolderDesc = ref('')
const folderError = ref('')
const creatingFolder = ref(false)
const showNewFolder = ref(false)

function openNewFolder() {
  showNewFolder.value = true
  newFolderName.value = ''
  newFolderDesc.value = ''
  folderError.value = ''
}

function cancelNewFolder() {
  showNewFolder.value = false
}

async function submitNewFolder() {
  const seg = newFolderName.value.trim()
  if (!seg) {
    folderError.value = '请输入文件夹名'
    return
  }
  if (seg.includes('/') || seg.includes('\\')) {
    folderError.value = '文件夹名不能包含斜杠'
    return
  }
  // 在 activeFolder 下创建子文件夹（activeFolder 为根时直接用 seg）
  const fullPath = activeFolder.value ? `${activeFolder.value}/${seg}` : seg
  creatingFolder.value = true
  folderError.value = ''
  try {
    await apiCreateFolder(activeModule.value, activeCategory.value, {
      path: fullPath,
      desc: newFolderDesc.value.trim(),
    })
    await refreshKb()
    showNewFolder.value = false
    activeFolder.value = fullPath
    flashOpMessage('文件夹已创建')
  } catch (e) {
    folderError.value = e?.message || '创建失败'
  } finally {
    creatingFolder.value = false
  }
}

async function removeFolder(folder) {
  if (!confirm(`确认删除文件夹「${folder.name}」？\n该操作会一并删除其下全部子文件夹与文件，且无法恢复。`)) return
  try {
    await apiDeleteFolder(activeModule.value, activeCategory.value, folder.path)
    await refreshKb()
    flashOpMessage('文件夹已删除')
  } catch (e) {
    alert('删除失败：' + (e?.message || ''))
  }
}

// 文件大小友好显示
function formatSize(bytes) {
  if (bytes == null) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

function onPickFile(e) {
  const f = e.target.files?.[0]
  if (!f) return
  // 选了单文件即退出批量模式，避免两份输入彼此打架
  batchFiles.value = []
  batchRootName.value = ''
  uploadFile.value = f
  // 自动用文件名（不含扩展名）填充标题
  if (!uploadTitle.value) {
    const stem = f.name.replace(/\.[^.]+$/, '')
    uploadTitle.value = stem
  }
  uploadError.value = ''
}

// 选了一个本机文件夹：input.webkitdirectory 把目录里所有文件（含子目录）作为 FileList 给我们
// 每个 file.webkitRelativePath 形如 'MyRoot/sub/leaf.png'
function onPickDirectory(e) {
  const files = Array.from(e.target.files || [])
  if (!files.length) return

  // 切回批量模式：清掉单文件残留
  uploadFile.value = null
  uploadTitle.value = ''

  // 提取本机根目录名（所有 file.webkitRelativePath 共享同一个根）
  const firstRel = files[0].webkitRelativePath || files[0].name
  const rootName = firstRel.includes('/') ? firstRel.split('/')[0] : ''
  batchRootName.value = rootName

  // 过滤明显应该忽略的文件（隐藏文件 / .DS_Store 等）
  const filtered = files
    .map((f) => ({
      file: f,
      relPath: f.webkitRelativePath || f.name,
    }))
    .filter((x) => {
      const name = x.relPath.split('/').pop() || ''
      // 跳过任何路径段为隐藏（以 . 开头）的文件
      if (x.relPath.split('/').some((seg) => seg.startsWith('.'))) return false
      // 系统垃圾
      if (['Thumbs.db'].includes(name)) return false
      return true
    })

  if (!filtered.length) {
    uploadError.value = '该文件夹下没有可上传的文件（隐藏文件已被忽略）'
    return
  }

  batchFiles.value = filtered
  batchProgress.value = { done: 0, total: 0, failed: [] }
  uploadError.value = ''
}

function resetUploadForm() {
  uploadFile.value = null
  uploadTitle.value = ''
  uploadSummary.value = ''
  uploadTags.value = ''
  // 目标文件夹默认跟随当前侧栏定位，便于"在这个目录下接着上传"的工作流
  uploadFolder.value = activeFolder.value
  uploadError.value = ''
  // 批量模式状态一并清空
  batchFiles.value = []
  batchRootName.value = ''
  batchProgress.value = { done: 0, total: 0, failed: [] }
  if (fileInputRef.value) fileInputRef.value.value = ''
  if (dirInputRef.value) dirInputRef.value.value = ''
}

function flashOpMessage(msg) {
  opMessage.value = msg
  if (opTimer) clearTimeout(opTimer)
  opTimer = setTimeout(() => (opMessage.value = ''), 2200)
}

// 解析共享标签：批量上传时所有文件套同一份 tags / summary
function parsedTags() {
  return uploadTags.value
    .replace(/，/g, ',')
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
}

// 上传：单文件 / 批量两条分支
async function submitUpload() {
  if (isBatchMode.value) {
    return submitBatchUpload()
  }
  if (!uploadFile.value) {
    uploadError.value = '请先选择要上传的文件或文件夹'
    return
  }
  uploading.value = true
  uploadError.value = ''
  try {
    await apiUpload(activeModule.value, activeCategory.value, {
      file: uploadFile.value,
      title: uploadTitle.value.trim(),
      summary: uploadSummary.value.trim(),
      tags: parsedTags(),
      folder: uploadFolder.value,
    })
    await refreshKb()
    resetUploadForm()
    flashOpMessage('上传成功')
  } catch (e) {
    uploadError.value = e?.message || '上传失败'
  } finally {
    uploading.value = false
  }
}

// 把相对路径里的每段都按 _safe_folder_path 同款规则清洗，避免后端 400
// 后端允许：中英文 / 数字 / 下划线 / 连字符 / 点 / 空格；其它一律换成 _
function sanitizeFolderSegment(seg) {
  return seg.replace(/[^0-9A-Za-z_.\-一-龥 ]+/g, '_')
}

// 把 'root/sub/leaf.png' 拆成 ['root', 'sub']（去掉文件名段，保留目录段）
function dirSegmentsOf(relPath) {
  const parts = relPath.split('/')
  return parts.slice(0, parts.length - 1).map(sanitizeFolderSegment)
}

// 拼出一份 file 的目标后端 folder 路径
// 规则：uploadFolder + 本地根目录名 + 相对子目录（保留多级）
function targetFolderFor(relPath) {
  const segs = []
  if (uploadFolder.value) segs.push(uploadFolder.value)
  // 注意：dirSegmentsOf 已经把 root 也包含进来了，因为 webkitRelativePath
  // 第一段就是用户选中的本机根目录名
  segs.push(...dirSegmentsOf(relPath))
  return segs.filter(Boolean).join('/')
}

async function submitBatchUpload() {
  uploading.value = true
  uploadError.value = ''
  const all = batchFiles.value
  batchProgress.value = { done: 0, total: all.length, failed: [] }

  // 共享的元信息（批量上传场景下不一一填，留给用户在表单填一次）
  const sharedSummary = uploadSummary.value.trim()
  const sharedTags = parsedTags()

  // 简易并发池：循环 take 任务直到队列空
  let cursor = 0
  async function worker() {
    while (cursor < all.length) {
      const idx = cursor++
      const { file, relPath } = all[idx]
      try {
        await apiUpload(activeModule.value, activeCategory.value, {
          file,
          // 标题留空，让后端用 stem 作为 title
          title: '',
          summary: sharedSummary,
          tags: sharedTags,
          folder: targetFolderFor(relPath),
        })
        batchProgress.value.done++
      } catch (e) {
        batchProgress.value.failed.push({
          relPath,
          message: e?.message || '上传失败',
        })
        batchProgress.value.done++
      }
    }
  }

  const workers = Array.from(
    { length: Math.min(BATCH_CONCURRENCY, all.length) },
    () => worker()
  )
  await Promise.all(workers)

  await refreshKb()
  uploading.value = false

  const failed = batchProgress.value.failed.length
  if (failed === 0) {
    resetUploadForm()
    flashOpMessage(`上传成功：共 ${all.length} 份`)
  } else {
    flashOpMessage(`已上传 ${all.length - failed} / ${all.length}，${failed} 份失败`)
    // 失败时不重置，让用户看到失败列表
  }
}

async function removeItem(item) {
  if (!confirm(`确认删除「${item.title}」？`)) return
  try {
    await apiDelete(item.moduleId, item.category, item.id)
    await refreshKb()
    flashOpMessage('已删除')
  } catch (e) {
    alert('删除失败：' + (e?.message || ''))
  }
}

// 下载：附带 download=1，触发浏览器另存为
function downloadItem(item) {
  const url = kbRawUrl(item.moduleId, item.category, item.id, { download: true })
  // 用隐式 <a download> 而非 window.open，避免新标签页直接渲染（PNG 会被预览掉）
  const a = document.createElement('a')
  a.href = url
  a.download = item.filename || ''
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

// 是否图片类型：优先 contentType，回退看扩展名
const IMAGE_EXT_RE = /\.(png|jpe?g|gif|webp|bmp|svg|avif)$/i
function isImage(item) {
  if (item.contentType?.startsWith('image/')) return true
  return IMAGE_EXT_RE.test(item.filename || '')
}

// 拼 inline URL（缩略图 / lightbox 共用）
function inlineUrl(item) {
  return kbRawUrl(item.moduleId, item.category, item.id)
}

// Lightbox 浮层状态：null = 未打开
const previewItem = ref(null)

function openPreview(item) {
  previewItem.value = item
}

function closePreview() {
  previewItem.value = null
}
</script>

<template>
  <div class="kb-view">
    <header class="topbar">
      <button class="back" @click="$emit('navigate', 'home')">← 返回主界面</button>
      <div class="topbar-title">
        <span class="title-icon">📚</span>
        <span class="title-text">知识库管理</span>
        <span class="title-sub">所有 Agent 模块共享的物料与文档沉淀</span>
      </div>
      <button class="refresh" :disabled="kbStore.loading" @click="refreshKb()">
        {{ kbStore.loading ? '刷新中…' : '🔄 刷新' }}
      </button>
    </header>

    <div v-if="opMessage" class="op-toast">{{ opMessage }}</div>

    <main class="main">
      <!-- 左侧：模块 + 分类导航 -->
      <aside class="sidebar">
        <div
          v-for="mod in KB_MODULES"
          :key="mod.id"
          class="module-block"
          :class="{ active: activeModule === mod.id }"
        >
          <button
            class="module-head"
            :style="
              activeModule === mod.id
                ? { borderColor: mod.color, color: mod.color }
                : null
            "
            type="button"
            @click="selectModule(mod.id)"
          >
            <span class="module-icon">{{ mod.icon }}</span>
            <span class="module-name">{{ mod.name }}</span>
            <span class="module-count">{{ moduleCount(mod.id) }}</span>
          </button>
          <div v-if="activeModule === mod.id" class="cat-list">
            <button
              v-for="cat in kbStore.modulesMap[mod.id] || []"
              :key="cat"
              class="cat-item"
              :class="{ active: activeCategory === cat }"
              type="button"
              @click="selectCategory(cat)"
            >
              <span class="cat-name">{{ getCategoryLabel(cat) }}</span>
              <span class="cat-count">{{ categoryCount(mod.id, cat) }}</span>
            </button>
          </div>
        </div>
      </aside>

      <!-- 右侧：上传 + 列表 -->
      <section class="content">
        <!-- 面包屑 + 文件夹操作 -->
        <div class="folder-bar">
          <div class="crumbs-row">
            <span class="crumb-label">📁 当前位置：</span>
            <template v-for="(b, i) in breadcrumbs" :key="b.path">
              <button
                class="crumb-btn"
                :class="{ active: b.path === activeFolder }"
                type="button"
                @click="selectFolder(b.path)"
              >
                {{ b.label }}
              </button>
              <span v-if="i < breadcrumbs.length - 1" class="crumb-sep">/</span>
            </template>
          </div>
          <div class="folder-actions">
            <button class="ghost sm" type="button" @click="openNewFolder">
              + 新建文件夹
            </button>
          </div>
        </div>

        <!-- 新建文件夹表单（行内展开） -->
        <div v-if="showNewFolder" class="card folder-form">
          <div class="card-head">
            <strong>
              在「{{ activeFolder || '(根目录)' }}」下新建文件夹
            </strong>
            <span class="card-sub">最多 4 级深度，名字仅允许字母 / 数字 / 下划线 / 中文 / 短横</span>
          </div>
          <div class="form-grid">
            <label class="field">
              <span>文件夹名</span>
              <input
                v-model="newFolderName"
                class="text-input"
                placeholder="例如：character"
              />
            </label>
            <label class="field full">
              <span>描述（会带进提示词，便于模型理解用途）</span>
              <textarea
                v-model="newFolderDesc"
                class="text-input"
                rows="2"
                placeholder="例如：项目内所有角色立绘草图与定稿"
              />
            </label>
          </div>
          <div class="upload-actions">
            <span v-if="folderError" class="upload-error">⚠ {{ folderError }}</span>
            <button class="ghost" type="button" @click="cancelNewFolder">取消</button>
            <button
              class="primary"
              type="button"
              :disabled="creatingFolder || !newFolderName.trim()"
              @click="submitNewFolder"
            >
              {{ creatingFolder ? '创建中…' : '✓ 创建' }}
            </button>
          </div>
        </div>

        <!-- 子文件夹卡片列表 -->
        <div v-if="childFolders.length" class="card folders-card">
          <div class="card-head">
            <strong>文件夹</strong>
            <span class="card-sub">点击进入；引用 Agent 时也可整目录选中</span>
          </div>
          <div class="folder-grid">
            <div
              v-for="f in childFolders"
              :key="f.path"
              class="folder-tile"
            >
              <button
                class="folder-main"
                type="button"
                @click="selectFolder(f.path)"
              >
                <span class="folder-icon">📁</span>
                <span class="folder-body">
                  <strong>{{ f.name }}</strong>
                  <span class="folder-meta">
                    {{ folderItemCount(f) }} 份文件
                  </span>
                  <span v-if="f.desc" class="folder-desc">{{ f.desc }}</span>
                </span>
              </button>
              <button
                class="folder-x"
                type="button"
                title="删除文件夹（连同其下所有子文件夹与文件）"
                @click="removeFolder(f)"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <!-- 上传表单 -->
        <div class="card upload-card">
          <div class="card-head">
            <strong>
              上传到 {{ getKbModuleMeta(activeModule).name }} ·
              {{ getCategoryLabel(activeCategory) }}
              <span class="upload-loc">/ {{ uploadFolder || '(根目录)' }}</span>
            </strong>
            <span class="card-sub">支持文档、图片、视频等任意格式（单文件 ≤ 50MB）</span>
          </div>

          <div class="upload-row">
            <!-- 单文件选择 -->
            <label class="file-input-label">
              <input
                ref="fileInputRef"
                type="file"
                class="file-input"
                @change="onPickFile"
              />
              <span class="file-btn">
                {{ uploadFile ? '✏ 重新选择' : '📄 选择文件' }}
              </span>
            </label>
            <!-- 整目录选择：浏览器原生 webkitdirectory，会展平给我们一份 FileList -->
            <label class="file-input-label">
              <input
                ref="dirInputRef"
                type="file"
                class="file-input"
                webkitdirectory
                directory
                multiple
                @change="onPickDirectory"
              />
              <span class="file-btn">
                {{ isBatchMode ? '✏ 重新选择目录' : '📁 选择整个文件夹' }}
              </span>
            </label>
            <span v-if="uploadFile" class="file-meta">
              {{ uploadFile.name }} · {{ formatSize(uploadFile.size) }}
            </span>
            <span v-else-if="isBatchMode" class="file-meta">
              「{{ batchRootName || '(目录)' }}」共 {{ batchFiles.length }} 份文件
            </span>
            <span v-else class="file-placeholder">未选择</span>
          </div>

          <!-- 批量模式：列文件清单 + 进度 + 失败列表 -->
          <div v-if="isBatchMode" class="batch-panel">
            <div class="batch-summary">
              将上传到
              <strong>
                {{ uploadFolder || '(根目录)' }}/{{ batchRootName }}/…
              </strong>
              （保留本机目录结构）
            </div>
            <details class="batch-files">
              <summary>查看文件清单（{{ batchFiles.length }} 份）</summary>
              <ul>
                <li v-for="x in batchFiles.slice(0, 200)" :key="x.relPath">
                  {{ x.relPath }}
                  <span class="batch-size">{{ formatSize(x.file.size) }}</span>
                </li>
                <li v-if="batchFiles.length > 200" class="batch-more">
                  …还有 {{ batchFiles.length - 200 }} 份未展开
                </li>
              </ul>
            </details>
            <div v-if="uploading || batchProgress.total" class="batch-progress">
              进度：{{ batchProgress.done }} / {{ batchProgress.total }}
              <span v-if="batchProgress.failed.length" class="batch-failed-num">
                · {{ batchProgress.failed.length }} 份失败
              </span>
            </div>
            <details
              v-if="batchProgress.failed.length"
              class="batch-failed-list"
            >
              <summary>失败列表</summary>
              <ul>
                <li v-for="(f, i) in batchProgress.failed" :key="i">
                  {{ f.relPath }} — {{ f.message }}
                </li>
              </ul>
            </details>
          </div>

          <div class="form-grid">
            <label class="field">
              <span>目标文件夹</span>
              <select v-model="uploadFolder" class="text-input">
                <option value="">(根目录)</option>
                <option
                  v-for="f in allFoldersOfCategory"
                  :key="f.path"
                  :value="f.path"
                >
                  {{ f.path }}{{ f.desc ? ' — ' + f.desc : '' }}
                </option>
              </select>
            </label>
            <!-- 单文件模式才显示标题输入；批量模式下用每份文件的 stem 作为 title -->
            <label v-if="!isBatchMode" class="field">
              <span>标题</span>
              <input
                v-model="uploadTitle"
                class="text-input"
                placeholder="留空时使用文件名"
              />
            </label>
            <label class="field">
              <span>标签（逗号分隔）{{ isBatchMode ? '· 全部文件共享' : '' }}</span>
              <input
                v-model="uploadTags"
                class="text-input"
                placeholder="例如：UI,角色,SOP"
              />
            </label>
            <label class="field full">
              <span>摘要 / 描述{{ isBatchMode ? '· 全部文件共享' : '' }}</span>
              <textarea
                v-model="uploadSummary"
                class="text-input"
                rows="2"
                placeholder="一句话说明这份资料的用途，便于 RAG 检索"
              />
            </label>
          </div>

          <div class="upload-actions">
            <span v-if="uploadError" class="upload-error">⚠ {{ uploadError }}</span>
            <button class="ghost" type="button" @click="resetUploadForm">清空</button>
            <button
              class="primary"
              type="button"
              :disabled="uploading || (!uploadFile && !isBatchMode)"
              @click="submitUpload"
            >
              <template v-if="uploading">
                {{ isBatchMode
                  ? `上传中 ${batchProgress.done}/${batchProgress.total}…`
                  : '上传中…' }}
              </template>
              <template v-else-if="isBatchMode">
                ⬆ 上传 {{ batchFiles.length }} 份
              </template>
              <template v-else>⬆ 上传</template>
            </button>
          </div>
        </div>

        <!-- 列表 -->
        <div class="card list-card">
          <div class="card-head">
            <strong>已沉淀条目</strong>
            <span class="card-sub">
              当前位置共 {{ currentItems.length }} 条（不含子文件夹）
            </span>
          </div>

          <div v-if="kbStore.error" class="list-empty">⚠ {{ kbStore.error }}</div>
          <div v-else-if="kbStore.loading && !kbStore.loaded" class="list-empty">
            正在加载…
          </div>
          <div v-else-if="!currentItems.length" class="list-empty">
            该分类下暂无条目，使用上方表单上传第一份资料吧。
          </div>

          <div v-else class="list">
            <div v-for="item in currentItems" :key="item.id" class="row">
              <!-- 图片：展示缩略图，点击放大；非图片：展示文件类型图标 -->
              <button
                v-if="isImage(item)"
                class="row-thumb thumb-img"
                type="button"
                title="点击放大查看"
                @click="openPreview(item)"
              >
                <img :src="inlineUrl(item)" :alt="item.title" loading="lazy" />
              </button>
              <div v-else class="row-thumb thumb-icon">📄</div>

              <div class="row-main">
                <div class="row-title">
                  <span
                    class="row-mod"
                    :style="{
                      color: getKbModuleMeta(item.moduleId).color,
                      borderColor: getKbModuleMeta(item.moduleId).color,
                    }"
                  >
                    {{ getKbModuleMeta(item.moduleId).name }} ·
                    {{ getCategoryLabel(item.category) }}
                  </span>
                  <strong>{{ item.title }}</strong>
                </div>
                <div v-if="item.summary" class="row-summary">{{ item.summary }}</div>
                <div class="row-foot">
                  <span class="row-file">📎 {{ item.filename }}</span>
                  <span class="row-size">{{ formatSize(item.size) }}</span>
                  <span v-for="tag in item.tags" :key="tag" class="row-tag">
                    #{{ tag }}
                  </span>
                  <span class="row-time">更新 {{ item.updatedAt }}</span>
                </div>
              </div>
              <div class="row-actions">
                <button
                  v-if="isImage(item)"
                  class="ghost sm"
                  type="button"
                  @click="openPreview(item)"
                >
                  预览
                </button>
                <button class="ghost sm" type="button" @click="downloadItem(item)">
                  下载
                </button>
                <button class="danger sm" type="button" @click="removeItem(item)">
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Lightbox：图片全屏预览。背景点击 / Esc 不在此处理（保持简单），按按钮关闭 -->
    <Teleport to="body">
      <div v-if="previewItem" class="lb-overlay" @click.self="closePreview">
        <div class="lb-frame">
          <header class="lb-head">
            <strong>{{ previewItem.title }}</strong>
            <span class="lb-sub">
              {{ previewItem.filename }} · {{ formatSize(previewItem.size) }}
            </span>
            <button class="lb-close" type="button" @click="closePreview">×</button>
          </header>
          <div class="lb-body">
            <img :src="inlineUrl(previewItem)" :alt="previewItem.title" />
          </div>
          <footer class="lb-foot">
            <button class="ghost sm" type="button" @click="downloadItem(previewItem)">
              下载原图
            </button>
            <button class="ghost sm" type="button" @click="closePreview">关闭</button>
          </footer>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.kb-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 28px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.back,
.refresh {
  padding: 7px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.15s;
}

.back:hover,
.refresh:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.topbar-title {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex: 1;
}

.title-icon {
  font-size: 20px;
}

.title-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-sub {
  font-size: 12px;
  color: var(--text-tertiary);
}

.op-toast {
  position: fixed;
  top: 78px;
  right: 28px;
  padding: 8px 16px;
  background: rgba(63, 185, 80, 0.18);
  color: var(--accent-green);
  border: 1px solid rgba(63, 185, 80, 0.45);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  z-index: 30;
}

.main {
  flex: 1;
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 0;
  min-height: 0;
}

/* 左侧导航 */
.sidebar {
  border-right: 1px solid var(--border-color);
  background: var(--bg-secondary);
  padding: 16px 12px;
  overflow-y: auto;
}

.module-block {
  margin-bottom: 8px;
}

.module-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  text-align: left;
  transition: all 0.15s;
}

.module-head:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.module-block.active .module-head {
  background: var(--bg-tertiary);
}

.module-icon {
  font-size: 14px;
}

.module-name {
  flex: 1;
}

.module-count {
  font-size: 11px;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  padding: 1px 7px;
  border-radius: 999px;
}

.cat-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 6px;
  padding-left: 14px;
}

.cat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 12px;
  text-align: left;
  transition: all 0.12s;
}

.cat-item:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.cat-item.active {
  background: rgba(88, 166, 255, 0.08);
  border-color: rgba(88, 166, 255, 0.4);
  color: var(--accent-blue);
}

.cat-count {
  font-size: 10px;
  color: var(--text-tertiary);
  background: var(--bg-card);
  padding: 0 6px;
  border-radius: 999px;
}

/* 右侧内容 */
.content {
  padding: 20px 28px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  overflow-y: auto;
}

.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 18px 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.card-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 面包屑栏 */
.folder-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.crumbs-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.crumb-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-right: 4px;
}

.crumb-btn {
  padding: 3px 8px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 12px;
  transition: all 0.12s;
}

.crumb-btn:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.crumb-btn.active {
  background: rgba(88, 166, 255, 0.12);
  color: var(--accent-blue);
  border-color: rgba(88, 166, 255, 0.4);
}

.crumb-sep {
  color: var(--text-tertiary);
  font-size: 11px;
}

.folder-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

/* 子文件夹卡片 */
.folder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}

.folder-tile {
  position: relative;
  display: flex;
}

.folder-main {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  text-align: left;
  transition: all 0.15s;
}

.folder-main:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
}

.folder-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.folder-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.folder-body strong {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 600;
  word-break: break-all;
}

.folder-meta {
  font-size: 11px;
  color: var(--text-tertiary);
}

.folder-desc {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.folder-x {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-tertiary);
  font-size: 14px;
  line-height: 1;
}

.folder-x:hover {
  background: rgba(248, 81, 73, 0.15);
  color: var(--accent-red, #f85149);
  border-color: rgba(248, 81, 73, 0.4);
}

.folder-form {
  border-color: rgba(88, 166, 255, 0.4);
}

.upload-loc {
  color: var(--text-tertiary);
  font-weight: 400;
  margin-left: 4px;
  font-size: 13px;
}

/* 批量上传面板：在选择文件夹后展示文件清单与进度 */
.batch-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(88, 166, 255, 0.06);
  border: 1px solid rgba(88, 166, 255, 0.25);
  border-radius: var(--radius-md);
  font-size: 12px;
  color: var(--text-secondary);
}

.batch-summary strong {
  color: var(--accent-blue);
  word-break: break-all;
}

.batch-files,
.batch-failed-list {
  font-size: 11px;
}

.batch-files summary,
.batch-failed-list summary {
  cursor: pointer;
  color: var(--text-tertiary);
  user-select: none;
}

.batch-files ul,
.batch-failed-list ul {
  margin: 6px 0 0;
  padding-left: 18px;
  max-height: 180px;
  overflow-y: auto;
}

.batch-files li,
.batch-failed-list li {
  line-height: 1.5;
  word-break: break-all;
}

.batch-size {
  color: var(--text-tertiary);
  margin-left: 6px;
  font-size: 10px;
}

.batch-more {
  color: var(--text-tertiary);
  list-style: none;
}

.batch-progress {
  font-weight: 500;
  color: var(--text-primary);
}

.batch-failed-num {
  color: var(--accent-red, #f85149);
  font-weight: 500;
  margin-left: 6px;
}

.batch-failed-list li {
  color: var(--accent-red, #f85149);
}

.card-head strong {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.card-sub {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 上传表单 */
.upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-input-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.file-input {
  display: none;
}

.file-btn {
  padding: 8px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-primary);
  transition: all 0.15s;
}

.file-input-label:hover .file-btn {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.file-meta {
  font-size: 12px;
  color: var(--text-secondary);
  word-break: break-all;
}

.file-placeholder {
  font-size: 12px;
  color: var(--text-tertiary);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.field.full {
  grid-column: 1 / -1;
}

.text-input {
  padding: 7px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  font-family: inherit;
  resize: vertical;
}

.text-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.15);
}

.upload-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
}

.upload-error {
  font-size: 12px;
  color: var(--accent-red, #f85149);
  margin-right: auto;
}

.ghost {
  padding: 7px 14px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 12px;
}

.ghost:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.ghost.sm,
.danger.sm {
  padding: 5px 10px;
  font-size: 11px;
}

.danger.sm {
  background: transparent;
  color: var(--accent-red, #f85149);
  border: 1px solid rgba(248, 81, 73, 0.4);
  border-radius: var(--radius-sm);
}

.danger.sm:hover {
  background: rgba(248, 81, 73, 0.12);
}

.primary {
  padding: 7px 18px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  color: #fff;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(88, 166, 255, 0.3);
}

.primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* 列表 */
.list-empty {
  padding: 28px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.row {
  display: flex;
  gap: 14px;
  padding: 12px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  align-items: flex-start;
}

.row-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.row-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.row-title strong {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.row-mod {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.3px;
  padding: 1px 7px;
  border-radius: 999px;
  border: 1px solid;
  background: var(--bg-tertiary);
}

.row-summary {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.row-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 11px;
  color: var(--text-tertiary);
}

.row-file {
  color: var(--text-secondary);
  word-break: break-all;
}

.row-tag {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--text-tertiary);
}

.row-time {
  margin-left: auto;
}

.row-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

/* 缩略图 */
.row-thumb {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  display: grid;
  place-items: center;
  overflow: hidden;
  padding: 0;
}

.row-thumb.thumb-img {
  cursor: zoom-in;
  transition: border-color 0.15s, transform 0.15s;
}

.row-thumb.thumb-img:hover {
  border-color: var(--accent-blue);
  transform: scale(1.03);
}

.row-thumb.thumb-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.row-thumb.thumb-icon {
  font-size: 22px;
  color: var(--text-tertiary);
}

/* Lightbox */
.lb-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.82);
  display: grid;
  place-items: center;
  padding: 32px;
  backdrop-filter: blur(2px);
}

.lb-frame {
  width: min(1200px, 100%);
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
}

.lb-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}

.lb-head strong {
  color: var(--text-primary);
  font-size: 14px;
}

.lb-sub {
  color: var(--text-tertiary);
  font-size: 12px;
  flex: 1;
}

.lb-close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  font-size: 18px;
  line-height: 1;
}

.lb-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.lb-body {
  flex: 1;
  min-height: 0;
  display: grid;
  place-items: center;
  background: #0a0d12;
  overflow: auto;
  padding: 16px;
}

.lb-body img {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  display: block;
}

.lb-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 18px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}
</style>
