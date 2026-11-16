// 纯事件回归：真实失败保留，工具错误通知与结果合并，不把后续进展当成原调用成功。
import assert from 'node:assert/strict'
import { runActivity } from '../src/utils/workflowActivity.js'

function fixture(withCallId) {
  const run = { id: 'archive-test', status: 'running', events: [] }
  function event(type, data) {
    run.events.push({
      seq: run.events.length + 1,
      time: `2026-11-09T10:39:0${run.events.length}Z`,
      type,
      message: '工具调用失败，已返回模型修正参数',
      data,
    })
  }
  event('graph_update', {
    message: {
      type: 'ai',
      id: 'request',
      tool_calls: [
        {
          id: 'bad-read',
          name: 'read_reference_archive',
          args: {
            path: 'Ludo.zip',
            member: 'game/assets/resources/config.f931b.json',
          },
        },
      ],
    },
  })
  event('tool_error', {
    tool: 'read_reference_archive',
    error: '包内不存在指定文件',
    ...(withCallId ? { call_id: 'bad-read' } : {}),
  })
  event('graph_update', {
    message: {
      type: 'tool',
      tool_call_id: 'bad-read',
      status: 'error',
      content: '工具调用错误：包内不存在指定文件。请检查路径。',
    },
  })
  return { run, event }
}

for (const withCallId of [true, false]) {
  const { run, event } = fixture(withCallId)
  let entries = runActivity(run)
  assert.equal(entries.length, 1, '新旧日志的同一失败均只能展示一次')
  assert.equal(entries[0].status, 'failed')
  assert.equal(
    entries[0].continued,
    false,
    '没有后续成功操作，不能标记流程已继续',
  )
  assert.match(
    entries[0].detail,
    /^game\/assets\/resources\/config.f931b.json\n参考包：Ludo.zip$/,
  )
  event('graph_update', {
    message: {
      type: 'ai',
      id: 'search',
      tool_calls: [
        {
          id: 'search-archive',
          name: 'list_reference_archive',
          args: { path: 'Ludo.zip', query: 'config.' },
        },
      ],
    },
  })
  assert.equal(runActivity(run)[0].continued, false, '只发起新调用不能算成功')
  event('graph_update', {
    message: {
      type: 'tool',
      tool_call_id: 'search-archive',
      status: 'success',
      content: '真实目录清单',
    },
  })
  entries = runActivity(run)
  assert.equal(entries.length, 2)
  assert.equal(
    entries[0].status,
    'failed',
    '历史失败仍保留，不能篡改为读取成功',
  )
  assert.equal(entries[0].continued, true)
  assert.equal(entries[1].status, 'completed')
}

const { run } = fixture(true)
run.events.pop()
assert.equal(
  runActivity(run)[0].status,
  'failed',
  '工具结果尚未同步时也能按调用 ID 展示失败',
)
run.events = [run.events[1]]
assert.equal(
  runActivity(run)[0].kind,
  'notice',
  '找不到对应请求的错误记录不能被吞掉',
)
// 自主决策按 AI 来源展示完整依据，不能冒充用户补充或阶段验收通过。
const autonomousRun = {
  id: 'autonomous-run', autonomous: true, status: 'running', events: [
    { seq: 1, type: 'graph_update', data: { message: { type: 'ai', tool_calls: [
      { id: 'choice', name: 'request_user_input', args: { question: '棋盘主题？' } },
    ] } } },
    { seq: 2, type: 'autonomous_decision', data: { question: '棋盘主题？', decision: '蓝色', reason: '符合已填冷色需求', source: 'ai' } },
  ],
}
const decisions = runActivity(autonomousRun)
assert.equal(decisions[0].title, '记录 AI 自主决策')
assert.equal(decisions[1].title, 'AI 自主决策')
assert.equal(decisions[1].status, 'autonomous')
assert.equal(decisions[1].text, '问题：棋盘主题？\n决定：蓝色\n理由：符合已填冷色需求')
autonomousRun.autonomous = false
assert.equal(runActivity(autonomousRun)[0].title, '请求补充信息')
console.log('活动记录回归通过：新旧错误去重、完整路径、失败状态与 AI 决策来源均正确。')
