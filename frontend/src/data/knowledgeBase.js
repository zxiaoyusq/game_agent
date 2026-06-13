// 知识库前端 store：从后端拉取条目 + 文件夹并缓存为响应式数据，
// 给 KnowledgeRefBlock / KnowledgeBaseView 共用，避免重复请求。
//
// 引用 key 协议（与后端 services/kb_context.py 保持一致）：
//   - 文件：   `file:${module}:${category}:${itemId}`
//             兼容旧版 `${module}:${category}:${itemId}` 三段式
//   - 文件夹： `folder:${module}:${category}:${folderPath}`
//             folderPath 用 / 分隔，"" 表示该分类根目录（递归整个分类）

import { reactive } from 'vue'
import { fetchKbFolders, fetchKbItems, fetchKbModules } from '../api/knowledge.js'

// 四个角色模块的展示元数据（颜色/图标/排序），与后端 KB_MODULE_CATEGORIES 对应
export const KB_MODULES = [
  { id: 'planning', name: '策划', color: '#58a6ff', icon: '📐' },
  { id: 'art',      name: '美术', color: '#f778ba', icon: '🎨' },
  { id: 'dev',      name: '程序', color: '#3fb950', icon: '⚙️' },
  { id: 'ops',      name: '运营', color: '#f0883e', icon: '📊' },
]

// 模块下分类的中文展示名
const CATEGORY_LABELS = {
  docs: '文档',
  images: '图片',
  videos: '视频',
  motion: '动捕',
  facial: '表情',
}

export function getCategoryLabel(category) {
  return CATEGORY_LABELS[category] || category
}

// 响应式 store：所有视图共享同一份数据
// items：扁平的全部条目
// folders：{ "<moduleId>:<category>": [folder, ...] }，按 module+category 索引
// modulesMap：来自后端的 { planning: ['docs'], art: ['docs', 'images', ...] }
export const kbStore = reactive({
  loading: false,
  loaded: false,
  error: '',
  items: [],
  folders: {},
  modulesMap: {},
})

// 内部：把后端 KbItem 适配为前端展示模型
// 标准化字段：id、moduleId、category、folder、title、summary、tags、updatedAt
function normalizeItem(raw) {
  return {
    id: raw.id,
    moduleId: raw.module,
    category: raw.category,
    folder: raw.folder || '',
    title: raw.title,
    summary: raw.summary || '',
    tags: raw.tags || [],
    updatedAt: (raw.updated_at || '').slice(0, 10), // 仅保留日期部分用于展示
    filename: raw.filename,
    size: raw.size,
    contentType: raw.content_type || '',
  }
}

// 内部：把后端 KbFolder 适配为前端展示模型，附带 moduleId/category 便于展示
function normalizeFolder(raw, moduleId, category) {
  return {
    moduleId,
    category,
    path: raw.path,
    name: raw.name,
    desc: raw.desc || '',
    updatedAt: (raw.updated_at || '').slice(0, 10),
  }
}

// 拉取全量条目 + 模块/分类元数据 + 全部分类的文件夹列表，组件首次挂载时调用
let _loadPromise = null
export function ensureKbLoaded() {
  if (kbStore.loaded) return Promise.resolve()
  if (_loadPromise) return _loadPromise
  _loadPromise = (async () => {
    kbStore.loading = true
    kbStore.error = ''
    try {
      const [modulesResp, itemsResp] = await Promise.all([
        fetchKbModules(),
        fetchKbItems(),
      ])
      kbStore.modulesMap = modulesResp?.modules || {}
      kbStore.items = (itemsResp?.items || []).map(normalizeItem)

      // 按 (module, category) 笛卡儿积逐个拉文件夹列表，
      // 数据量小（每分类几个 folder），并发拉取性能足够
      const tasks = []
      for (const [moduleId, cats] of Object.entries(kbStore.modulesMap)) {
        for (const cat of cats) {
          tasks.push(
            fetchKbFolders(moduleId, cat)
              .then((resp) => {
                const list = (resp?.folders || []).map((f) =>
                  normalizeFolder(f, moduleId, cat)
                )
                kbStore.folders[`${moduleId}:${cat}`] = list
              })
              .catch(() => {
                // 单个分类拉失败不影响整体加载，留空数组
                kbStore.folders[`${moduleId}:${cat}`] = []
              })
          )
        }
      }
      await Promise.all(tasks)

      kbStore.loaded = true
    } catch (e) {
      kbStore.error = e?.message || '加载知识库失败'
    } finally {
      kbStore.loading = false
      _loadPromise = null
    }
  })()
  return _loadPromise
}

// 强制刷新：上传 / 删除 / 创建文件夹后调用，保持 store 与后端一致
export async function refreshKb() {
  kbStore.loaded = false
  return ensureKbLoaded()
}

// 按模块分组返回（用于 Tab 计数与列表）
export function getItemsByModule(moduleId) {
  return kbStore.items.filter((it) => it.moduleId === moduleId)
}

// 取某分类下所有文件夹
export function getFoldersOf(moduleId, category) {
  return kbStore.folders[`${moduleId}:${category}`] || []
}

// 解析引用 key，返回 {kind, moduleId, category, locator}；非法返回 null
export function parseKbKey(key) {
  if (!key || typeof key !== 'string') return null
  const parts = key.split(':')
  if (parts[0] === 'file' && parts.length >= 4) {
    return {
      kind: 'file',
      moduleId: parts[1],
      category: parts[2],
      locator: parts.slice(3).join(':'),
    }
  }
  if (parts[0] === 'folder' && parts.length >= 3) {
    return {
      kind: 'folder',
      moduleId: parts[1],
      category: parts[2],
      locator: parts.length > 3 ? parts.slice(3).join(':') : '',
    }
  }
  // 兼容旧三段式 module:category:itemId
  if (parts.length === 3) {
    return {
      kind: 'file',
      moduleId: parts[0],
      category: parts[1],
      locator: parts[2],
    }
  }
  // 兼容更老的两段式 module:itemId
  if (parts.length === 2) {
    return {
      kind: 'file',
      moduleId: parts[0],
      category: '',
      locator: parts[1],
    }
  }
  return null
}

// 按 key 拿条目（仅 file ref 有效，folder ref 返回 null）
export function getKbItem(key) {
  const parsed = parseKbKey(key)
  if (!parsed || parsed.kind !== 'file') return null
  const { moduleId, category, locator } = parsed
  if (category) {
    return (
      kbStore.items.find(
        (it) =>
          it.moduleId === moduleId &&
          it.category === category &&
          it.id === locator
      ) || null
    )
  }
  // 老两段 key：仅靠 moduleId + id 查找
  return (
    kbStore.items.find((it) => it.moduleId === moduleId && it.id === locator) ||
    null
  )
}

// 按 key 拿文件夹（仅 folder ref 有效；返回组合好的展示对象）
// locator 为 "" 时表示该分类根目录这一虚拟节点，name 用 "(根目录)"
export function getKbFolder(key) {
  const parsed = parseKbKey(key)
  if (!parsed || parsed.kind !== 'folder') return null
  const { moduleId, category, locator } = parsed
  if (locator === '') {
    return {
      moduleId,
      category,
      path: '',
      name: '(根目录)',
      desc: '',
    }
  }
  return (
    getFoldersOf(moduleId, category).find((f) => f.path === locator) || {
      moduleId,
      category,
      path: locator,
      name: locator.split('/').pop(),
      desc: '',
    }
  )
}

// 生成 file ref（兼容旧调用：传入 item 即可）
export function makeKbKey(item) {
  return `file:${item.moduleId}:${item.category}:${item.id}`
}

// 生成 folder ref
export function makeKbFolderKey(moduleId, category, path) {
  return `folder:${moduleId}:${category}:${path || ''}`
}

// 统计某 folder ref 实际包含的文件数（递归）
// folderPath = '' 表示该分类下全部文件
export function countItemsInFolder(moduleId, category, folderPath) {
  const prefix = folderPath ? folderPath + '/' : ''
  return kbStore.items.filter(
    (it) =>
      it.moduleId === moduleId &&
      it.category === category &&
      (folderPath === ''
        ? true
        : it.folder === folderPath || it.folder.startsWith(prefix))
  ).length
}

// 简化版 RAG：在 title/summary/tags 上做加权打分；
// 后端独立 RAG 接口后再切。当前完全在已加载的 kbStore.items 上做。
export function ragSearch(query, topK = 3) {
  const q = (query || '').trim().toLowerCase()
  if (!q) return []
  const tokens = q.split(/\s+/).filter((t) => t.length >= 2)
  const out = []
  for (const it of kbStore.items) {
    const titleL = it.title.toLowerCase()
    const sumL = (it.summary || '').toLowerCase()
    const tagsL = (it.tags || []).map((t) => t.toLowerCase())
    let score = 0
    if (titleL.includes(q)) score += 5
    if (sumL.includes(q)) score += 3
    if (tagsL.some((t) => t.includes(q))) score += 2
    for (const tok of tokens) {
      if (titleL.includes(tok)) score += 1
      if (sumL.includes(tok)) score += 0.5
      if (tagsL.some((t) => t.includes(tok))) score += 0.5
    }
    if (score > 0) out.push({ ...it, _score: score })
  }
  out.sort((a, b) => b._score - a._score)
  return out.slice(0, topK)
}

export function getKbModuleMeta(moduleId) {
  return KB_MODULES.find((m) => m.id === moduleId) || KB_MODULES[0]
}
