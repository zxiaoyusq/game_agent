// 网页交互回归：只替换项目执行接口，不调用收费模型；真实 API 验收另存运行记录。
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const base = process.env.APP_URL || 'http://127.0.0.1:24681'
const temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'workflow-template-ui-'))
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
const errors = []
let project, creation, answers, starts = 0
const record = { id: 'ui-run', stage: 'prototype', status: 'awaiting_input', events: [], artifacts: [], provider: 'api-key', model: 'gpt-6.1-sol', interrupts: [{ id: 'question-1', value: { question: '验收界面的主题色？', context: '本条是网页回归夹具', options: ['青绿色', '金黄色'] } }] }
page.on('pageerror', error => errors.push(error.message))

// 其他请求保持只读真实服务，包括模板格式、Skill 及参考路径校验。
await page.route('**/api/workflow/projects**', async route => {
  const request = route.request(), url = new URL(request.url())
  let data
  if (url.pathname.endsWith('/projects') && request.method() === 'POST') {
    creation = request.postDataJSON()
    project = { ...creation, id: 'ui-project', workspace: 'games/ui-project', pipeline: { id: 'ui-pipeline', status: 'awaiting_input', run_id: record.id, current_stage: 'prototype' }, stages: ['prototype', 'art', 'code', 'test'].map(id => ({ id, status: 'pending' })) }
    project.stages[0] = { id: 'prototype', status: 'awaiting_input', run_id: record.id }; starts++
    data = project
  } else if (url.pathname.endsWith('/activity')) data = { project, runs: [record] }
  else if (url.pathname.endsWith('/projects')) data = project ? [project] : []
  else if (url.pathname.endsWith('/pipeline/start')) {
    starts++; project.pipeline = { id: 'ui-pipeline', status: 'awaiting_input', run_id: record.id, current_stage: 'prototype' }
    project.stages[0] = { id: 'prototype', status: 'awaiting_input', run_id: record.id }; data = project
  } else if (url.pathname.endsWith('/pipeline/cancel')) { project.pipeline.status = 'cancelled'; data = project }
  else if (url.pathname.endsWith('/pipeline/resume')) { project.pipeline.status = 'running'; data = project }
  else if (url.pathname.endsWith('/runs')) data = [record]
  else if (url.pathname.endsWith('/skill-selection')) data = { items: [], selected_paths: [], recommended_paths: [], recommended_items: [], warnings: [] }
  else data = project
  await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) })
})
await page.route('**/api/workflow/runs/ui-run**', async route => {
  if (route.request().url().endsWith('/answers')) {
    answers = route.request().postDataJSON().answers
    record.status = 'running'; record.interrupts = []; project.pipeline.status = 'running'
  }
  await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(record) })
})

try {
  await page.goto(base); await page.locator('.production-entry').click()
  await page.getByRole('button', { name: '＋ 创建新项目', exact: true }).click()
  await page.getByRole('button', { name: '使用 LUDO · 原版贴图与动画 模板', exact: true }).click()
  await page.waitForFunction(() => document.querySelector('[aria-label="品类方案"]').value === 'board-games')
  assert.equal(await page.getByLabel('技术方案', { exact: true }).inputValue(), 'canvas-web')
  assert.match(await page.getByLabel('美术需求与修改范围', { exact: true }).inputValue(), /逐格/)
  const start = page.getByRole('button', { name: '确认需求并开始全流程', exact: true })
  assert(await start.isDisabled())
  const downloadReady = page.waitForEvent('download')
  await page.getByRole('button', { name: '导出当前配置', exact: true }).click()
  const file = path.join(temporary, 'template.json'); await (await downloadReady).saveAs(file)
  const exported = JSON.parse(await fs.readFile(file, 'utf8'))
  assert(!('workspace' in exported)); assert(!('api_key' in exported))
  assert.equal(exported.production_plan.publish_slug, '')
  assert.equal(Object.keys(exported.production_plan.stages).length, 4)
  await page.locator('.import-label input').setInputFiles({ name: 'broken.json', mimeType: 'application/json', buffer: Buffer.from('{') })
  await page.getByRole('alert').filter({ hasText: '导入失败' }).waitFor()
  await page.locator('.import-label input').setInputFiles(file)
  await page.waitForFunction(() => !document.querySelector('.template-picker [role="alert"]'))
  await page.setViewportSize({ width: 390, height: 844 })
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
  await page.getByLabel(/我已确认玩法、美术、模型和交付设置/).check()
  await page.getByRole('tab', { name: /美术与参考/ }).click()
  await page.getByLabel('美术需求与修改范围', { exact: true }).fill(exported.production_plan.art_requirements + ' 保留原版比例。')
  assert(await start.isDisabled(), '修改需求后必须撤销之前的勾选')
  await page.getByLabel(/我已确认玩法、美术、模型和交付设置/).check(); await start.click()
  await page.getByRole('heading', { name: '需要你补充后继续', exact: true }).waitFor()
  assert.equal(starts, 1); assert.equal(creation.model_provider, 'api-key')
  assert.equal(creation.start_immediately, true)
  assert.equal(creation.model_id, 'gpt-6.1-sol'); assert(creation.request_id)
  assert(creation.production_plan.stages.art.skill_paths.includes('azure-image2-generation/SKILL.md'))
  assert.equal(await page.locator('.stage-chat,.review-panel').count(), 0)
  await page.reload(); await page.locator('.production-entry').click()
  await page.locator('.project-card').filter({ hasText: creation.name }).click()
  await page.getByRole('button', { name: '青绿色', exact: true }).click()
  await page.getByRole('button', { name: '提交回答并继续', exact: true }).click()
  await page.waitForFunction(() => !document.querySelector('.human-input'))
  assert.deepEqual(answers, { 'question-1': '青绿色' })
  await page.getByRole('button', { name: '取消全流程', exact: true }).click()
  await page.getByRole('button', { name: '继续全流程', exact: true }).click()
  await page.getByRole('button', { name: '取消全流程', exact: true }).waitFor()
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
  assert.deepEqual(errors, [])
  console.log('全流程网页回归通过：' + JSON.stringify({ passed: true, template_roundtrip: true, confirmation_reset: true, hitl_refresh_answer: true, cancel_resume: true, mobile: true, errors }))
} finally {
  await browser.close(); await fs.rm(temporary, { recursive: true, force: true })
}
