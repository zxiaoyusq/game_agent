// 策划 Agent 流式接口客户端（POST + SSE）。
//
// 由于 EventSource 只支持 GET，这里用 fetch + ReadableStream 自己解 SSE 帧。
// 协议：每条事件以 `data: <json>\n\n` 结束，json 形如：
//   {"delta": "..."}   token 片段
//   {"error": "..."}   出错
//   {"done": true}     结束

const API_BASE = '/api'

/**
 * 调用 /api/planning/stream，逐 token 通过 onDelta 回调推给上层。
 *
 * @param {object} body  请求体：{ user_input, model_id, sub_module, project_brief, kb_refs }
 *                       kb_refs 为前端选中的三段式 key 数组（module:category:item_id），
 *                       后端会自行读取知识库内容（含图片 base64，按 vision provider 注入）
 * @param {object} cb    回调：{ onDelta, onError, onDone }
 * @param {AbortSignal} signal  可选，外部取消请求
 */
export async function streamPlanning(body, { onDelta, onError, onDone } = {}, signal) {
  let resp
  try {
    resp = await fetch(API_BASE + '/planning/stream', {
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
    } catch (_) {}
    onError?.(msg)
    onDone?.()
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = '' // 跨 chunk 缓存未完整的事件
  let finished = false

  // 解析 SSE 缓冲区中已经成形的 `data: ...\n\n` 事件
  function drain() {
    let idx
    // \n\n 是事件边界
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      // 一条事件可能含多行，每行可能是 data:/event:/id: 等；当前后端只发 data:
      const lines = rawEvent.split('\n')
      const dataParts = []
      for (const line of lines) {
        if (line.startsWith('data:')) {
          dataParts.push(line.slice(5).trimStart())
        }
      }
      if (!dataParts.length) continue
      const dataStr = dataParts.join('\n')
      let payload
      try {
        payload = JSON.parse(dataStr)
      } catch (_) {
        // 非 JSON 帧直接当成纯文本 delta 兜底
        onDelta?.(dataStr)
        continue
      }
      if (payload.error) {
        onError?.(payload.error)
      } else if (payload.delta != null) {
        onDelta?.(payload.delta)
      }
      if (payload.done) {
        finished = true
      }
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
    // 流结束后再 flush 一次，处理最后一条无 \n\n 的事件
    if (!finished && buffer.trim()) {
      buffer += '\n\n'
      drain()
    }
  } catch (e) {
    if (e.name !== 'AbortError') {
      onError?.(e?.message || '流读取失败')
    }
  } finally {
    onDone?.()
  }
}
