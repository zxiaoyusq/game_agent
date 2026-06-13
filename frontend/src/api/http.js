// 统一 fetch 封装。
// 后端响应外壳：{ success, data, error }，本工具会自动剥壳，
// 业务侧 await request(...) 拿到的是 data 字段。
// 出错时抛出带 status / message 的 Error，调用方 try/catch 即可。

const API_BASE = '/api'

// 解析后端响应壳，统一处理网络错误与业务错误
async function parseResponse(resp) {
  // FileResponse 等场景：非 JSON 直接返回原始 Response
  const ct = resp.headers.get('content-type') || ''
  if (!ct.includes('application/json')) {
    if (!resp.ok) {
      const text = await resp.text()
      throw new HttpError(text || resp.statusText, resp.status)
    }
    return resp
  }

  const body = await resp.json().catch(() => null)

  // FastAPI 默认错误返回 { detail: '...' } 而非外壳格式
  if (!resp.ok) {
    const msg = body?.error || body?.detail || resp.statusText
    throw new HttpError(typeof msg === 'string' ? msg : JSON.stringify(msg), resp.status)
  }

  // 业务壳：success=false 视为错误
  if (body && typeof body === 'object' && 'success' in body) {
    if (!body.success) {
      throw new HttpError(body.error || '请求失败', resp.status)
    }
    return body.data
  }
  return body
}

// 自定义错误类型，方便上层区分 4xx/5xx/网络错误
export class HttpError extends Error {
  constructor(message, status = 0) {
    super(message)
    this.name = 'HttpError'
    this.status = status
  }
}

// 通用 JSON 请求
export async function request(path, { method = 'GET', body, headers, ...rest } = {}) {
  const init = { method, headers: { ...(headers || {}) }, ...rest }
  if (body !== undefined && !(body instanceof FormData)) {
    init.headers['Content-Type'] = 'application/json'
    init.body = JSON.stringify(body)
  } else if (body instanceof FormData) {
    init.body = body
  }
  let resp
  try {
    resp = await fetch(API_BASE + path, init)
  } catch (e) {
    // 网络层失败（断网、CORS、proxy 未启动等）
    throw new HttpError(`网络请求失败：${e.message || e}`, 0)
  }
  return parseResponse(resp)
}

// 拼接下载 URL，<a href> 或 window.open 直接用
export function rawUrl(path) {
  return API_BASE + path
}
