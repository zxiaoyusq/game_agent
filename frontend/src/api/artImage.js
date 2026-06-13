// 美术 Agent · AI 图片生成接口客户端
// 对应后端 backend/app/api/routes/art.py
//
// 直接走 fetch（不用通用 request 封装），因为：
//  - 入参是 multipart/form-data（多文件 + 多个同名 kb_refs）
//  - 默认响应是二进制 image/png（解析路径与 JSON 不同）
// 通过 ?json=1 也可以让后端返 base64 JSON，前端再 dataURL 渲染；这里默认走 blob，
// 与浏览器原生 <img src=blob:>、下载 a.download 都更友好。

const API_BASE = '/api'

/**
 * @param {object} opts
 * @param {string} opts.prompt
 * @param {string} opts.size       后端白名单内的尺寸字符串
 * @param {string} opts.quality    low / medium / high / auto
 * @param {File[]} [opts.references]  浏览器直传的参考图（PNG / JPEG）
 * @param {string[]} [opts.kbRefs]    已选知识库引用 key（file:..._ / folder:..._）
 * @param {AbortSignal} [opts.signal] 取消信号
 * @returns {Promise<Blob>} PNG Blob
 */
export async function generateImage({
  prompt,
  size,
  quality,
  references = [],
  kbRefs = [],
  signal,
} = {}) {
  const fd = new FormData()
  fd.append('prompt', prompt)
  fd.append('size', size)
  fd.append('quality', quality)
  for (const f of references) {
    if (f instanceof File || f instanceof Blob) {
      fd.append('references', f, f.name || 'reference.png')
    }
  }
  for (const key of kbRefs) {
    if (key) fd.append('kb_refs', key)
  }

  let resp
  try {
    resp = await fetch(`${API_BASE}/art/image/generate`, {
      method: 'POST',
      body: fd,
      signal,
    })
  } catch (e) {
    // 网络层失败：fetch 抛错（含 CORS / 服务未起 / 主动 abort）
    if (e.name === 'AbortError') throw e
    throw new Error(`网络请求失败：${e?.message || e}`)
  }

  if (!resp.ok) {
    // FastAPI 默认错误体：{detail: '...'}
    let detail = ''
    try {
      const ct = resp.headers.get('content-type') || ''
      if (ct.includes('application/json')) {
        const body = await resp.json()
        detail = body?.detail || body?.error || ''
      } else {
        detail = await resp.text()
      }
    } catch (_) {
      // 忽略解析失败，按状态文本兜底
    }
    throw new Error(`HTTP ${resp.status}: ${detail || resp.statusText}`)
  }

  // 默认返回 image/png 二进制
  return resp.blob()
}
