import { reactive } from 'vue'
import { request } from '../api/http.js'

// 首页数量与游戏列表共用真实目录，重新进入时刷新，不保存虚构的示例游戏。
export const producedGames = reactive({ items: [], loaded: false, loading: false, error: '' })
let pending
let revision = 0

export function loadProducedGames() {
  if (pending) return pending
  producedGames.loading = true
  producedGames.error = ''
  const version = revision
  pending = request('/produced-games').then((data) => {
    if (version !== revision) return
    producedGames.items = data.items
    producedGames.loaded = true
  }).catch((error) => {
    if (version === revision) producedGames.error = error.message || '游戏列表加载失败，请重试。'
  }).finally(() => {
    producedGames.loading = false
    pending = null
  })
  return pending
}

export async function refreshGamesAfterDeletion(deletedIds) {
  // 删除后忽略此前尚未完成的列表响应，避免旧条目短暂重新出现。
  revision++
  const deleted = new Set(deletedIds)
  producedGames.items = producedGames.items.filter((game) => !deleted.has(game.id))
  await pending
  await loadProducedGames()
}

export async function deleteProducedGame(identifier) {
  const result = await request(`/produced-games/${encodeURIComponent(identifier)}`, { method: 'DELETE' })
  await refreshGamesAfterDeletion(result.deleted_ids)
  return result
}
