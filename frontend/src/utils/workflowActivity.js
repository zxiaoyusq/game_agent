// 活动视图只整理已有事件；工具成功必须有对应结果，不能从阶段状态猜测。
const toolNames = {
  read_file: '读取文件',
  write_file: '写入文件',
  edit_file: '修改文件',
  ls: '查看目录',
  glob: '查找文件',
  grep: '搜索代码',
  write_todos: '更新制作计划',
  read_skill: '阅读 Skill',
  read_skill_resource: '阅读技能资料',
  read_knowledge: '阅读项目知识',
  read_game_knowledge: '阅读项目知识',
  read_reference: '研究参考资料',
  run_validation: '执行构建与测试',
  generate_image: '生成美术资源',
  generate_art_image: '生成美术资源',
  process_art_image: '处理游戏贴图',
  prepare_web_runtime: '准备游戏运行环境',
  inspect_assets: '检查美术资源',
  ask_user: '请求补充信息',
  request_user_input: '请求补充信息',
  list_reference_archive: '检查参考包',
  read_reference_archive: '读取参考工程',
  copy_reference_asset: '提取参考素材',
  extract_reference_asset: '提取参考素材',
}

export function messageText(content) {
  if (typeof content === 'string') return content
  if (!Array.isArray(content)) return ''
  return content
    .filter((block) => ['text', 'output_text'].includes(block?.type))
    .map((block) => block.text || '')
    .join('\n')
}

function toolDetail(call) {
  const args = call.args || {}
  if (args.member) return `${args.member}\n参考包：${args.path || '见调用记录'}`
  if (Array.isArray(args.todos))
    return args.todos
      .map(
        (item) => `${item.status === 'completed' ? '✓' : '○'} ${item.content}`,
      )
      .join('\n')
  return (
    args.file_path ||
    args.path ||
    args.command ||
    args.output_path ||
    args.query ||
    args.pattern ||
    args.directory ||
    ''
  )
}

export function runActivity(run) {
  const entries = [],
    calls = new Map(),
    messages = new Set()
  const events = run.events || []
  let latestSuccess = 0
  for (const event of events) {
    const id = `${run.id}:${event.seq}`,
      data = event.data || {}
    if (event.type === 'graph_update') {
      const message = data.message || {}
      const text = messageText(message.content)
      if (message.type === 'ai') {
        const messageKey = message.id || `${event.seq}`
        if (messages.has(messageKey)) continue
        messages.add(messageKey)
        if (text.trim())
          entries.push({ id, kind: 'message', text, time: event.time })
        for (const [index, call] of (message.tool_calls || []).entries()) {
          const callId = call.id || `${id}:${index}`
          if (calls.has(callId)) continue
          const entry = {
            id: `${id}:${callId}`,
            kind: 'tool',
            title: call.name === 'request_user_input' && run.autonomous
              ? '记录 AI 自主决策'
              : toolNames[call.name] || call.name,
            name: call.name,
            detail: toolDetail(call),
            status: 'running',
            time: event.time,
            output: '',
          }
          calls.set(callId, entry)
          entries.push(entry)
        }
      } else if (message.type === 'tool') {
        const call = calls.get(message.tool_call_id)
        if (call) {
          call.status = message.status === 'error' ? 'failed' : 'completed'
          call.output = text
          call.finishedAt = event.time
          call.finishedSeq = event.seq
          if (call.status === 'completed')
            latestSuccess = Math.max(latestSuccess, event.seq)
        }
      }
    } else if (event.type === 'tool_error') {
      // 新日志直接使用调用 ID；旧日志通过真实错误响应配对，避免同一次失败显示两遍。
      const response =
        !data.call_id &&
        events.find(
          (item) =>
            item.seq > event.seq &&
            item.data?.message?.type === 'tool' &&
            item.data.message.status === 'error' &&
            messageText(item.data.message.content).includes(
              (data.error || '').slice(0, 120),
            ) &&
            calls.get(item.data.message.tool_call_id)?.name === data.tool,
        )
      const call = calls.get(
        data.call_id || response?.data.message.tool_call_id,
      )
      if (call) {
        call.status = 'failed'
        call.output = data.error || ''
        call.finishedAt = event.time
        call.finishedSeq = event.seq
      } else {
        entries.push({
          id,
          kind: 'notice',
          title: event.message,
          text: data.error || '',
          status: 'failed',
          time: event.time,
        })
      }
    } else if (event.type === 'autonomous_decision') {
      entries.push({
        id, kind: 'notice', title: 'AI 自主决策', status: 'autonomous', time: event.time,
        text: [`问题：${data.question || ''}`, `决定：${data.decision || ''}`, `理由：${data.reason || ''}`].join('\n'),
      })
    } else if (
      [
        'failed',
        'model_error',
        'cancelled',
        'interrupted',
        'resumed',
        'confirmed',
        'game_published',
      ].includes(event.type)
    ) {
      entries.push({
        id,
        kind: 'notice',
        title: event.message,
        text: data.error || data.url || '',
        status: ['failed', 'tool_error', 'model_error'].includes(event.type)
          ? 'failed'
          : event.type,
        time: event.time,
      })
    }
  }
  // 尚未返回的调用在中断后保持“未完成”，不把取消或提问显示成成功。
  for (const call of calls.values()) {
    // 只表明流程后续有成功操作，原失败保留，不宣称该次读取已经修复。
    if (call.status === 'failed')
      call.continued = latestSuccess > (call.finishedSeq || 0)
    if (
      call.status === 'running' &&
      !['running', 'queued'].includes(run.status)
    )
      call.status =
        run.status === 'awaiting_input' ? 'awaiting_input' : 'unfinished'
  }
  if (
    run.summary &&
    !entries.some(
      (entry) => entry.kind === 'message' && entry.text === run.summary,
    )
  )
    entries.push({
      id: `${run.id}:summary`,
      kind: 'message',
      text: run.summary,
      time: run.updated_at,
    })
  return entries
}

export function currentActivity(run) {
  if (!run) return '正在同步制作记录'
  if (run.status === 'awaiting_input') return '需要你的补充，回答后继续制作'
  if (!['running', 'queued'].includes(run.status)) return ''
  const events = run.events || [],
    last = events.at(-1)
  if (last?.type === 'validation_started')
    return `正在执行 ${last.data?.command || '构建与测试'}`
  const active = runActivity(run).filter(
    (item) => item.kind === 'tool' && item.status === 'running',
  )
  if (active.length)
    return `${active.at(-1).title}${active.length > 1 ? ` · ${active.length} 项处理中` : ''}`
  const model = [...events]
    .reverse()
    .find((item) =>
      ['model_started', 'model_completed', 'model_error'].includes(item.type),
    )
  if (model?.type === 'model_started') return '正在分析需求与执行结果'
  return run.status === 'queued'
    ? '任务已排队，准备开始'
    : '正在整理结果并继续制作'
}

export function elapsedTime(start, end) {
  const seconds = Math.max(
    0,
    Math.floor((new Date(end).getTime() - new Date(start).getTime()) / 1000),
  )
  if (!Number.isFinite(seconds)) return '—'
  if (seconds < 60) return `${seconds} 秒`
  return `${Math.floor(seconds / 60)} 分 ${seconds % 60} 秒`
}
