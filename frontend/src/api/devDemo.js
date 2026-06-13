// 研发 Agent - Demo 生成 SSE 客户端。
//
// 协议详见 backend/app/api/routes/dev_demo.py：每条事件都带 type 字段。
// 与 planning.js 风格一致，但事件类型更丰富，所以用单一 onEvent 回调透传整个 payload，
// 调用方按 payload.type 自行分流。

const API_BASE = '/api'

/**
 * 阶段 1：生成 Plan
 * @param {object} body { task_id?, model_id, requirement, template?, engine?, kb_refs }
 * @param {object} cb   { onEvent, onError, onDone }
 * @param {AbortSignal} signal
 */
export function streamDemoPlan(body, callbacks, signal) {
  return _streamSse('/dev/demo/plan', body, callbacks, signal)
}

/**
 * 阶段 2：按 Plan 生成代码工程
 * @param {object} body { task_id, model_id, requirement, template?, engine?, kb_refs, plan }
 * @param {object} cb   { onEvent, onError, onDone }
 * @param {AbortSignal} signal
 */
export function streamDemoGenerate(body, callbacks, signal) {
  return _streamSse('/dev/demo/generate', body, callbacks, signal)
}

// ---- 内部：通用 SSE POST 客户端 ---------------------------------------------

async function _streamSse(path, body, { onEvent, onError, onDone } = {}, signal) {
  let resp
  try {
    resp = await fetch(API_BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    })
  } catch (e) {
    onError?.(e?.message || '请求失败')
    onDone?.()
    return
  }

  if (!resp.ok || !resp.body) {
    let msg = `HTTP ${resp.status}`
    try {
      const t = await resp.text()
      if (t) msg += ' ' + t
    } catch (_) {
      /* 忽略：响应体读取失败时仅给出状态码 */
    }
    onError?.(msg)
    onDone?.()
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  // 跨 chunk 缓存未完整事件
  let buffer = ''
  let finished = false

  // 解析缓冲区中已成形的 `data: ...\n\n` 事件
  function drain() {
    let idx
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      // 多行 data: 拼回原文
      const lines = rawEvent.split('\n')
      const dataParts = []
      for (const line of lines) {
        if (line.startsWith('data:')) dataParts.push(line.slice(5).trimStart())
      }
      if (!dataParts.length) continue
      const dataStr = dataParts.join('\n')
      let payload
      try {
        payload = JSON.parse(dataStr)
      } catch (_) {
        // 兜底：不是合法 JSON 就当文本透传，让上层 onEvent 处理
        onEvent?.({ type: 'thinking', text: dataStr })
        continue
      }
      // 通用错误事件：直接走 onError
      if (payload.type === 'error') {
        onError?.(payload.message || '未知错误')
        continue
      }
      if (payload.type === 'done') {
        finished = true
        continue
      }
      onEvent?.(payload)
    }
  }

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      drain()
      if (finished) break
    }
    if (!finished && buffer.trim()) {
      buffer += '\n\n'
      drain()
    }
  } catch (e) {
    if (e.name !== 'AbortError') onError?.(e?.message || '流读取失败')
  } finally {
    onDone?.()
  }
}
