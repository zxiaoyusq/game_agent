// 任务控制验收：拦截写接口验证路由、等待状态与竞态，不停止用户任务或触发模型计费。
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const output = path.resolve(process.env.OUTPUT_DIR || 'logs/workflow-controls')
await fs.mkdir(output, { recursive: true })
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
page.setDefaultTimeout(10000)
const errors = [], requests = [], unexpectedWrites = []
const projects = ['pipeline-control', 'manual-control'].map((id, index) => ({
  id, name: index ? '手动阶段控制验收' : '全流程控制验收', brief: { idea: '验证停止与继续' },
  ...(index ? {} : { production_plan: {}, pipeline: { id: 'pipeline-id', status: 'running', run_id: `${id}-run` } }),
  stages: ['prototype', 'art', 'code', 'test'].map((stage, i) => ({
    id: stage, status: i < 2 ? 'completed' : i === 2 ? 'running' : 'pending',
    run_id: i === 2 ? `${id}-run` : null,
  })),
  preview: { status: 'ready', revision: 'v1', url: `/api/workflow/projects/${id}/preview/index.html` },
}))
const runs = projects.map(project => ({
  id: `${project.id}-run`, stage: 'code', status: 'running',
  created_at: new Date().toISOString(), updated_at: new Date().toISOString(), events: [], artifacts: [],
}))
let failNext = false, holdNext = false, release, frameLoads = 0
page.on('pageerror', error => errors.push(error.message))
page.on('framenavigated', frame => { if (frame !== page.mainFrame()) frameLoads++ })
function setStatus(index, status) {
  runs[index].status = status
  runs[index].updated_at = new Date().toISOString()
  projects[index].stages[2].status = status
  if (projects[index].pipeline) projects[index].pipeline.status = status
}
await page.route('**/api/workflow/**', async route => {
  const request = route.request(), pathname = new URL(request.url()).pathname
  const index = pathname.includes('manual-control') ? 1 : 0
  if (pathname.endsWith('/skill-selection')) return route.fulfill({ json: { items: [], recommended_items: [], selected_paths: [] } })
  if (request.method() === 'POST') {
    if (!/^\/api\/workflow\/(projects\/(pipeline-control|manual-control)\/pipeline|runs\/(pipeline-control|manual-control)-run)\/(cancel|resume)$/.test(pathname)) {
      unexpectedWrites.push(pathname)
      return route.abort()
    }
    requests.push(pathname)
    if (holdNext) {
      holdNext = false
      await new Promise(resolve => { release = resolve })
      release = null
    }
    if (failNext) {
      failNext = false
      return route.fulfill({ status: 409, json: { detail: '验收用错误：请稍后重试' } })
    }
    setStatus(index, pathname.endsWith('/cancel') ? 'cancelled' : 'running')
    return route.fulfill({ json: pathname.includes('/pipeline/') ? projects[index] : runs[index] })
  }
  if (pathname.includes('/preview/')) return route.fulfill({ contentType: 'text/html', body: '<!doctype html><title>试玩状态验收</title><button onclick="this.textContent=\'游戏已开始\'">开始游戏</button>' })
  if (pathname.endsWith('/projects')) return route.fulfill({ json: projects })
  if (pathname.endsWith('/activity')) return route.fulfill({ json: { project: projects[index], runs: [runs[index]] } })
  if (pathname.includes('/projects/')) return route.fulfill({ json: projects[index] })
  return route.continue()
})
const stop = () => page.getByRole('button', { name: '停止生成', exact: true })
const resume = () => page.getByRole('button', { name: '继续任务', exact: true })
async function openProject(index) {
  await page.locator('.project-card').filter({ hasText: projects[index].name }).click()
  await page.locator('.task-controls').waitFor()
}

try {
  await page.goto(process.env.APP_URL || 'http://127.0.0.1:24681')
  await page.locator('.production-entry').click()
  await openProject(0)
  const frame = page.frameLocator('.live-preview iframe')
  await frame.getByRole('button', { name: '开始游戏' }).click()
  const initialFrameLoads = frameLoads
  // 错误保持可见，轮询不能把失败的停止伪装成成功。
  failNext = true
  await stop().click()
  await page.locator('.task-control-error').waitFor()
  await page.waitForTimeout(2200)
  assert(await page.locator('.task-control-error').isVisible())
  assert(await stop().isEnabled())
  holdNext = true
  await stop().click()
  await page.getByRole('button', { name: '正在停止…', exact: true }).waitFor()
  assert(await page.getByRole('button', { name: '正在停止…', exact: true }).isDisabled())
  assert.equal(await resume().count(), 0)
  const pendingCount = requests.length
  await page.getByRole('button', { name: '正在停止…', exact: true }).evaluate(button => button.click())
  assert.equal(requests.length, pendingCount, '停止请求未结束时不得重复提交')
  release()
  await resume().waitFor()
  assert(await page.getByText('生成任务已停止', { exact: true }).isVisible())
  assert.equal(requests.at(-1), '/api/workflow/projects/pipeline-control/pipeline/cancel')
  await page.screenshot({ path: path.join(output, 'stopped.png') })
  // 刷新后从服务端状态重建继续入口；继续请求与停止请求使用同一项目。
  await page.reload()
  await page.locator('.production-entry').click()
  await openProject(0)
  await resume().waitFor()
  holdNext = true
  await resume().click()
  await page.getByRole('button', { name: '正在继续…', exact: true }).waitFor()
  release()
  await stop().waitFor()
  assert.equal(requests.at(-1), '/api/workflow/projects/pipeline-control/pipeline/resume')
  const restoredLoads = frameLoads
  // 手动阶段使用具体运行 ID；不能误调用全流程接口。
  await page.getByRole('button', { name: '返回我的项目', exact: true }).click()
  await openProject(1)
  await stop().click()
  await resume().waitFor()
  assert.equal(requests.at(-1), '/api/workflow/runs/manual-control-run/cancel')
  failNext = true
  await resume().click()
  await page.locator('.task-control-error').waitFor()
  assert(await resume().isEnabled())
  await resume().click()
  await stop().waitFor()
  assert.equal(requests.at(-1), '/api/workflow/runs/manual-control-run/resume')
  for (const [width, height] of [[1440, 720], [1024, 768], [390, 844], [320, 740]]) {
    await page.setViewportSize({ width, height })
    const layout = await page.evaluate(() => ({
      width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight,
      button: document.querySelector('.task-action-button').getBoundingClientRect().bottom,
    }))
    assert(layout.width <= width && layout.height <= height + 1 && layout.button <= height, `任务控制不得溢出：${JSON.stringify(layout)}`)
  }
  await page.screenshot({ path: path.join(output, 'mobile-running.png') })
  await page.setViewportSize({ width: 1440, height: 900 })
  // 请求发出后切换项目，旧项目响应不能把新工作台覆盖掉。
  holdNext = true
  await stop().click()
  await page.getByRole('button', { name: '正在停止…', exact: true }).waitFor()
  await page.getByRole('button', { name: '返回我的项目', exact: true }).click()
  await openProject(0)
  release()
  await page.waitForTimeout(500)
  assert(await page.getByRole('heading', { name: projects[0].name, exact: true }).isVisible())
  assert(await stop().isEnabled())
  const beforeControl = frameLoads
  await frame.getByRole('button', { name: '开始游戏' }).click()
  await stop().click()
  await resume().waitFor()
  assert.equal(frameLoads, beforeControl, '停止不能重载正在试玩的游戏')
  assert(await frame.getByRole('button', { name: '游戏已开始' }).isVisible())
  await resume().click()
  await stop().waitFor()
  assert.equal(frameLoads, beforeControl, '继续不能重载已有试玩版本')
  setStatus(0, 'awaiting_input')
  await page.getByText('任务正在等待你的补充', { exact: true }).waitFor()
  await stop().click()
  await resume().waitFor()
  setStatus(0, 'completed')
  await page.locator('.task-controls').waitFor({ state: 'hidden' })
  assert.deepEqual(errors, [])
  assert.deepEqual(unexpectedWrites, [])
  console.log('任务控制验收通过：' + JSON.stringify({ requests, initialFrameLoads, restoredLoads, errors, unexpectedWrites }))
} finally {
  release?.()
  await browser.close()
}
