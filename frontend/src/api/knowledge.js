// 知识库相关接口封装，对应后端 app/api/routes/knowledge.py

import { rawUrl, request } from './http.js'

// 拉取「模块 → 分类列表」结构，前端用于渲染分类下拉
export function fetchKbModules() {
  return request('/knowledge/modules')
}

// 跨模块汇总查询；可选按 module/category 过滤
export function fetchKbItems({ module, category } = {}) {
  const params = new URLSearchParams()
  if (module) params.set('module', module)
  if (category) params.set('category', category)
  const qs = params.toString()
  return request('/knowledge/items' + (qs ? `?${qs}` : ''))
}

// 单分类列表（管理界面切换分类时使用）
export function fetchCategoryItems(module, category) {
  return request(
    `/knowledge/${encodeURIComponent(module)}/${encodeURIComponent(category)}/items`
  )
}

// 上传单个文件；title/summary/tags 都是可选元信息
// folder：可选，目标文件夹相对路径，留空 = 根目录
export function uploadKbItem(
  module,
  category,
  { file, title = '', summary = '', tags = [], folder = '' }
) {
  const fd = new FormData()
  fd.append('file', file)
  if (title) fd.append('title', title)
  if (summary) fd.append('summary', summary)
  if (tags.length) fd.append('tags', tags.join(','))
  if (folder) fd.append('folder', folder)
  return request(
    `/knowledge/${encodeURIComponent(module)}/${encodeURIComponent(category)}/items`,
    { method: 'POST', body: fd }
  )
}

// 删除单条
export function deleteKbItem(module, category, itemId) {
  return request(
    `/knowledge/${encodeURIComponent(module)}/${encodeURIComponent(category)}/items/${encodeURIComponent(itemId)}`,
    { method: 'DELETE' }
  )
}

// ---- 文件夹相关 ----------------------------------------------------------

// 列出某分类下所有文件夹
export function fetchKbFolders(module, category) {
  return request(
    `/knowledge/${encodeURIComponent(module)}/${encodeURIComponent(category)}/folders`
  )
}

// 新建文件夹
export function createKbFolder(module, category, { path, desc = '' }) {
  return request(
    `/knowledge/${encodeURIComponent(module)}/${encodeURIComponent(category)}/folders`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, desc }),
    }
  )
}

// 删除文件夹（递归：连同其下全部子文件夹与文件一并删除）
export function deleteKbFolder(module, category, path) {
  const qs = `?path=${encodeURIComponent(path)}`
  return request(
    `/knowledge/${encodeURIComponent(module)}/${encodeURIComponent(category)}/folders${qs}`,
    { method: 'DELETE' }
  )
}

// 原始文件 URL。
// download=true 时附 ?download=1，由后端切换到 attachment 触发浏览器另存为；
// 默认 inline，方便 <img>/<video> 等标签直接展示。
export function kbRawUrl(module, category, itemId, { download = false } = {}) {
  const base = `/knowledge/${encodeURIComponent(module)}/${encodeURIComponent(category)}/items/${encodeURIComponent(itemId)}/raw`
  return rawUrl(base + (download ? '?download=1' : ''))
}
