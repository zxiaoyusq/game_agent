// LLM 可选模型清单接口；前端进入 agent 工作台时拉一次

import { reactive } from 'vue'
import { request } from './http.js'

// 全局 reactive 缓存：跨组件共享同一份模型清单
export const modelStore = reactive({
  loading: false,
  loaded: false,
  error: '',
  list: [],
})

let _loadPromise = null

// 拉取模型清单；多次调用会复用同一个 promise，避免重复请求
export function ensureModelsLoaded() {
  if (modelStore.loaded) return Promise.resolve()
  if (_loadPromise) return _loadPromise
  _loadPromise = (async () => {
    modelStore.loading = true
    modelStore.error = ''
    try {
      const data = await request('/models')
      modelStore.list = Array.isArray(data) ? data : []
      modelStore.loaded = true
    } catch (e) {
      modelStore.error = e?.message || '加载模型清单失败'
    } finally {
      modelStore.loading = false
      _loadPromise = null
    }
  })()
  return _loadPromise
}
