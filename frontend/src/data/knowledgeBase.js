// 知识库前端状态由首页和知识库页面共用，缓存条目、文件夹及模块信息。

import { reactive } from 'vue'
import { fetchKbFolders, fetchKbItems, fetchKbModules } from '../api/knowledge.js'

// 知识库模块的展示元数据（颜色/图标/排序），与后端 KB_MODULE_CATEGORIES 对应
export const KB_MODULES = [
  { id: 'selection', name: '选品分析', color: '#a78bfa', icon: '🔍' },
  { id: 'planning', name: '策划', color: '#58a6ff', icon: '📐' },
  { id: 'art',      name: '美术', color: '#f778ba', icon: '🎨' },
  { id: 'dev',      name: '程序', color: '#3fb950', icon: '⚙️' },
  { id: 'ops',      name: '运营', color: '#f0883e', icon: '📊' },
  { id: 'skill',    name: 'Skill', color: '#e3b341', icon: '🧩' },
  { id: 'genre',    name: '游戏品类', color: '#56c7bc', icon: '🎮' },
  { id: 'framework', name: '技术框架', color: '#8aabf0', icon: '🛠️' },
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

export function getKbModuleMeta(moduleId) {
  return KB_MODULES.find((m) => m.id === moduleId) || KB_MODULES[0]
}
