// 实时工作台验收：模拟事件到达与构建换版，只在浏览器拦截接口，不创建收费任务。
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'
import {
  currentActivity,
  messageText,
  runActivity,
} from '../src/utils/workflowActivity.js'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const base = process.env.APP_URL || 'http://127.0.0.1:24681'
const output = path.resolve(process.env.OUTPUT_DIR || 'logs/run-workspace')
await fs.mkdir(output, { recursive: true })
const run = {
  id: 'live-run',
  stage: 'code',
  status: 'running',
  created_at: new Date(Date.now() - 60000).toISOString(),
  updated_at: new Date().toISOString(),
  model: 'gpt-6.1-sol',
  provider: 'api-key',
  events: [],
  artifacts: [],
}
const project = {
  id: 'live-ui',
  name: '实时工作台交互验收',
  model_provider: 'api-key',
  model_id: 'gpt-6.1-sol',
  workspace: 'games/live-ui',
  brief: { idea: '验证 Agent 制作记录与游戏预览同步。' },
  production_plan: {},
  pipeline: { status: 'running', run_id: run.id, current_stage: 'code' },
  stages: ['prototype', 'art', 'code', 'test'].map((id, index) => ({
    id,
    status: index < 2 ? 'completed' : index === 2 ? 'running' : 'pending',
    run_id: index === 2 ? run.id : null,
  })),
  preview: { status: 'waiting', reason: '等待首个游戏构建' },
}
function event(type, data = {}, message = '验收执行事件') {
  run.updated_at = new Date().toISOString()
  run.events.push({
    seq: run.events.length + 1,
    time: run.updated_at,
    type,
    data,
    message,
  })
}
function build(revision) {
  project.preview = {
    status: 'ready',
    revision,
    url: '/api/workflow/projects/live-ui/preview/index.html',
    updated_at: new Date().toISOString(),
  }
}
event('graph_update', {
  message: {
    type: 'ai',
    id: 'm1',
    content: '开始实现棋盘与走子动画。',
    tool_calls: [
      { id: 'c1', name: 'write_file', args: { file_path: 'src/game.js' } },
    ],
  },
})
assert.equal(currentActivity(run), '写入文件')
event('graph_update', {
  message: {
    type: 'tool',
    tool_call_id: 'c1',
    status: 'error',
    content: '写入路径错误',
  },
})
assert.equal(
  runActivity(run).find((item) => item.kind === 'tool').status,
  'failed',
)
assert.equal(
  messageText([
    { type: 'reasoning', text: '内部块' },
    { type: 'text', text: '面向用户的说明' },
  ]),
  '面向用户的说明',
)
event('model_started')
assert.equal(currentActivity(run), '正在分析需求与执行结果')

const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox'],
})
const page = await browser.newPage({
  viewport: { width: 1440, height: 960 },
  reducedMotion: 'reduce',
})
const errors = [],
  layouts = []
let failBuild = false,
  frameLoads = 0,
  submittedAnswers = null,
  unexpectedWrites = 0
page.on('pageerror', (error) => errors.push(error.message))
page.on('framenavigated', (frame) => {
  if (frame !== page.mainFrame() && frame.url().includes('/preview/'))
    frameLoads++
})
await page.route('**/api/workflow/projects**', async (route) => {
  const request = route.request(),
    url = new URL(request.url())
  if (url.pathname.includes('/preview/')) {
    if (failBuild)
      return route.fulfill({ status: 503, body: '验收中的构建更新' })
    return route.fulfill({
      status: 200,
      contentType: 'text/html',
      headers: { 'Cache-Control': 'no-store' },
      body: `<!doctype html><meta charset="utf-8"><body style="background:#173c34;color:white"><h1>交互验收构建 ${project.preview.revision}</h1><button id="play">操作次数 0</button><script>let count=0;document.querySelector('#play').onclick=event=>event.target.textContent='操作次数 '+(++count)</script>`,
    })
  }
  if (
    request.method() !== 'GET' &&
    !url.pathname.endsWith('/skill-selection')
  ) {
    unexpectedWrites++
    return route.fulfill({ status: 400, body: '{}' })
  }
  const data = url.pathname.endsWith('/projects')
    ? [project]
    : url.pathname.endsWith('/activity')
      ? { project, runs: [run] }
      : url.pathname.endsWith('/runs')
        ? [run]
        : url.pathname.endsWith('/skill-selection')
          ? {
              items: [],
              recommended_items: [],
              selected_paths: [],
              recommended_paths: [],
              warnings: [],
            }
          : project
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(data),
  })
})
await page.route('**/api/workflow/runs/live-run**', async (route) => {
  if (route.request().url().endsWith('/answers')) {
    submittedAnswers = route.request().postDataJSON().answers
    run.status = 'running'
    run.interrupts = []
    project.pipeline.status = 'running'
    event('model_started')
  }
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(run),
  })
})

try {
  await page.goto(base)
  await page.locator('.production-entry').click()
  await page.locator('.project-card').filter({ hasText: project.name }).click()
  await page
    .getByRole('heading', { name: '你的游戏，正在这里诞生。' })
    .waitFor()
  assert.equal(await page.locator('iframe').count(), 0)
  build('v1')
  const frame = page.frameLocator('.live-preview iframe')
  await frame.getByRole('heading', { name: '交互验收构建 v1' }).waitFor()
  await frame.getByRole('button', { name: '操作次数 0' }).click()
  const firstLoads = frameLoads
  event('graph_update', {
    message: {
      type: 'ai',
      id: 'm2',
      content: '走子动画已加入，接下来检查规则。',
    },
  })
  await page
    .getByText('走子动画已加入，接下来检查规则。', { exact: true })
    .waitFor()
  assert.equal(frameLoads, firstLoads, '普通事件更新不能重载游戏')
  assert(await frame.getByRole('button', { name: '操作次数 1' }).isVisible())
  await page.getByRole('button', { name: '手机预览', exact: true }).click()
  assert(await frame.getByRole('button', { name: '操作次数 1' }).isVisible())
  assert.equal(frameLoads, firstLoads, '切换设备尺寸不能丢失试玩状态')

  build('v2')
  await frame.getByRole('heading', { name: '交互验收构建 v2' }).waitFor()
  assert.equal(frameLoads, firstLoads + 1)
  await page.getByLabel('自动加载新版本').uncheck()
  build('v3')
  await page.getByText('新的游戏版本已准备好').waitFor()
  assert(
    await frame.getByRole('heading', { name: '交互验收构建 v2' }).isVisible(),
  )
  await page.getByRole('button', { name: '加载新版本', exact: true }).click()
  await frame.getByRole('heading', { name: '交互验收构建 v3' }).waitFor()
  await page.getByLabel('自动加载新版本').check()
  failBuild = true
  build('v4')
  await page.locator('.preview-error').waitFor()
  assert(
    await frame.getByRole('heading', { name: '交互验收构建 v3' }).isVisible(),
    '新构建不可用时保留原游戏',
  )
  failBuild = false
  await page
    .locator('.preview-error')
    .getByRole('button', { name: '重试' })
    .click()
  await frame.getByRole('heading', { name: '交互验收构建 v4' }).waitFor()

  // 查看历史时不自动抢走滚动位置；用户可显式回到最新记录。
  for (let index = 0; index < 22; index++)
    event('graph_update', {
      message: {
        type: 'ai',
        id: `history-${index}`,
        content: `历史进展 ${index}：检查游戏界面与操作反馈。`,
      },
    })
  await page
    .getByText('历史进展 21：检查游戏界面与操作反馈。', { exact: true })
    .waitFor()
  await page.locator('.activity-feed').evaluate((element) => {
    element.scrollTop = 0
    element.dispatchEvent(new Event('scroll'))
  })
  event('graph_update', {
    message: {
      type: 'ai',
      id: 'latest',
      content: '新增执行记录，不打断历史阅读。',
    },
  })
  await page.getByRole('button', { name: '查看最新进展' }).waitFor()
  assert.equal(
    await page
      .locator('.activity-feed')
      .evaluate((element) => element.scrollTop),
    0,
  )
  await page.getByRole('button', { name: '查看最新进展' }).click()

  run.status = 'awaiting_input'
  project.pipeline.status = 'awaiting_input'
  run.interrupts = [
    {
      id: 'color-question',
      value: {
        question: '棋盘使用什么主题？',
        options: ['原版色彩', '木质棋盘'],
      },
    },
  ]
  await page
    .getByRole('heading', { name: '需要你补充后继续', exact: true })
    .waitFor()
  await page
    .getByLabel('棋盘使用什么主题？', { exact: true })
    .fill('保留原版色彩与贴图')
  event('human_input_requested')
  await page.waitForTimeout(2300)
  assert.equal(
    await page.getByLabel('棋盘使用什么主题？', { exact: true }).inputValue(),
    '保留原版色彩与贴图',
  )
  await page
    .getByRole('button', { name: '提交回答并继续', exact: true })
    .click()
  await page.locator('.human-input').waitFor({ state: 'hidden' })
  assert.deepEqual(submittedAnswers, { 'color-question': '保留原版色彩与贴图' })

  for (const width of [1920, 1440, 1024, 768, 700, 390, 320]) {
    await page.setViewportSize({ width, height: 900 })
    const layout = await page.evaluate(() => ({
      width: innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      height: innerHeight,
      scrollHeight: document.documentElement.scrollHeight,
    }))
    assert(layout.scrollWidth <= width, `${width}px 不应横向溢出`)
    assert(layout.scrollHeight <= 901, `${width}px 应由分栏内部滚动`)
    layouts.push(layout)
    if (width === 390) {
      await page.getByRole('tab', { name: /游戏预览/ }).click()
      assert(
        await frame
          .getByRole('heading', { name: '交互验收构建 v4' })
          .isVisible(),
      )
      await page.getByRole('tab', { name: /制作进展/ }).click()
      assert(
        await page
          .getByRole('region', { name: '制作进展', exact: true })
          .isVisible(),
      )
    }
  }
  assert.equal(unexpectedWrites, 0)
  assert.deepEqual(errors, [])
  const report = {
    passed: true,
    layouts,
    automatic_versions: true,
    stable_play_state: true,
    preview_failure_recovery: true,
    history_scroll: true,
    hitl: true,
    unexpectedWrites,
    errors,
  }
  await fs.writeFile(
    path.join(output, 'live-ui-validation.json'),
    JSON.stringify(report, null, 2),
  )
  console.log('实时制作台验收通过：' + JSON.stringify(report))
} finally {
  await browser.close()
}
