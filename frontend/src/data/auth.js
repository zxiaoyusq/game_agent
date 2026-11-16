import { reactive } from 'vue'
import { request } from '../api/http.js'

export const auth = reactive({ user: null, ready: false, busy: false, error: '' })

export async function restoreSession() {
  auth.error = ''
  try {
    const result = await request('/auth/session')
    auth.user = result.user
  } catch (cause) {
    auth.user = null
    if (cause.status !== 401) auth.error = '无法连接登录服务，请检查连接后重试。'
  } finally {
    auth.ready = true
  }
}

export async function login(username, password) {
  if (auth.busy) return
  auth.busy = true
  auth.error = ''
  try {
    const result = await request('/auth/login', { method: 'POST', body: { username: username.trim(), password } })
    auth.user = result.user
  } catch (cause) {
    auth.error = cause.status === 401 ? '用户名或密码错误，请重新输入。' : cause.message || '登录失败，请重试。'
  } finally {
    auth.busy = false
  }
}

export async function logout() {
  await request('/auth/logout', { method: 'POST' })
  auth.user = null
  auth.error = ''
  // 只广播退出事件，密码与会话令牌不进入浏览器存储。
  try { localStorage.setItem('game-agent-logout', String(Date.now())) } catch { /* 存储受限不影响退出。 */ }
}

export function expireSession() {
  auth.user = null
  auth.error = '登录已失效，请重新登录。'
}
