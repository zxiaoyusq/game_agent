// 自主执行勾选验收：创建与模板校验请求在浏览器中拦截，不启动真实生成任务。
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const output = path.resolve(process.env.OUTPUT_DIR || 'logs/workflow-autonomy')
const liveReads = process.env.USE_LIVE_READS === '1'
await fs.mkdir(output, { recursive: true })
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
page.setDefaultTimeout(12000)
const errors = [], creations = [], unexpectedWrites = []
const templateDirectory = new URL('../../resources/workflow-templates/', import.meta.url)
const templates = await Promise.all((await fs.readdir(templateDirectory)).filter(name => name.endsWith('.json'))
  .sort().map(async name => JSON.parse(await fs.readFile(new URL(name, templateDirectory), 'utf8'))))
let project
page.on('pageerror', error => errors.push(error.message))
await page.route('**/api/**', async route => {
  const request = route.request(), pathname = new URL(request.url()).pathname
  // Vite 源码也包含 /src/api/ 路径，仅拦截服务端接口，不能替换前端模块。
  if (!pathname.startsWith('/api/')) return route.continue()
  if (pathname.endsWith('/templates/validate')) {
    if (liveReads) return route.continue()
    const template = request.postDataJSON()
    // 字段格式与后端契约一致；完整模板验证由后端测试覆盖。
    template.production_plan.autonomous = template.production_plan.autonomous === true
    return route.fulfill({ json: template })
  }
  if (pathname.endsWith('/projects') && request.method() === 'POST') {
    const payload = request.postDataJSON()
    creations.push(payload)
    project = { ...payload, id: `autonomy-ui-${creations.length}`, workspace: `games/autonomy-ui-${creations.length}`,
      pipeline: { id: 'ui-pipeline', status: 'running' },
      stages: ['prototype', 'art', 'code', 'test'].map(id => ({ id, status: 'pending' })),
    }
    return route.fulfill({ status: 201, json: project })
  }
  if (pathname.endsWith('/skill-selection')) return route.fulfill({ json: { items: [], selected_paths: [], recommended_paths: [], recommended_items: [], warnings: [] } })
  if (request.method() !== 'GET') {
    unexpectedWrites.push(pathname)
    return route.abort()
  }
  if (pathname.endsWith('/activity')) return route.fulfill({ json: { project, runs: [] } })
  if (pathname.endsWith('/projects')) return route.fulfill({ json: project ? [project] : [] })
  if (liveReads) return route.continue()
  if (pathname.endsWith('/templates')) return route.fulfill({ json: templates })
  if (pathname.endsWith('/runtime')) return route.fulfill({ json: { available: true, configured: true, ready: true, models: [{ id: 'gpt-6.1-sol', name: 'GPT 6.1 Sol' }] } })
  if (pathname.endsWith('/catalog')) return route.fulfill({ json: {
    genres: [{ id: 'general', label: '通用游戏', knowledge_paths: [] }, { id: 'board-games', label: '棋盘游戏', knowledge_paths: [] }],
    frameworks: [{ id: 'canvas-web', label: 'Canvas 2D · Web / H5', knowledge_paths: [] }], documents: [],
  } })
  if (pathname.endsWith('/skills')) return route.fulfill({ json: [] })
  if (pathname.endsWith('/knowledge/modules')) return route.fulfill({ json: { modules: {} } })
  if (pathname.endsWith('/produced-games') || pathname.endsWith('/knowledge/items')) return route.fulfill({ json: { items: [] } })
  if (pathname.endsWith('/cover')) return route.fulfill({ path: new URL('../public/studio/ludo-board.png', import.meta.url).pathname })
  return route.fulfill({ json: [] })
})
const autonomy = () => page.getByRole('checkbox', { name: 'AI 自主决策，全流程免提问', exact: true })
const consent = () => page.getByLabel(/我已确认玩法、美术、模型和交付设置/)
const start = () => page.getByRole('button', { name: '确认需求并开始全流程', exact: true })
async function chooseTemplate() {
  const validated = page.waitForResponse(response => new URL(response.url()).pathname.endsWith('/templates/validate'))
  await page.getByRole('button', { name: '使用 LUDO · 原版贴图与动画 模板', exact: true }).click()
  await validated
  await page.waitForFunction(() => document.querySelector('[aria-label="项目名称"]').value === 'LUDO · 原版美术复现')
}
async function importTemplate(template) {
  const validated = page.waitForResponse(response => new URL(response.url()).pathname.endsWith('/templates/validate'))
  await page.getByLabel('导入 JSON 模板', { exact: true }).setInputFiles({
    name: 'autonomy-template.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(template)),
  })
  await validated
  await page.waitForFunction(() => !document.querySelector('.template-picker .template-loading'))
}

try {
  await page.goto(process.env.APP_URL || 'http://127.0.0.1:24681')
  await page.locator('.production-entry').click()
  await page.getByRole('button', { name: '＋ 创建新项目', exact: true }).click()
  await autonomy().waitFor()
  await page.waitForFunction(() => !document.querySelector('.creation-autonomy input').disabled)
  assert.equal(await autonomy().isChecked(), false)
  await autonomy().check()
  await chooseTemplate()
  assert(await autonomy().isChecked(), '切换内置模板保留用户已勾选的自主模式')
  await consent().check()
  await autonomy().uncheck()
  assert.equal(await consent().isChecked(), false, '切换模式必须撤销执行确认')
  assert(await start().isDisabled())
  await autonomy().check()
  assert(await page.getByText('四阶段自动衔接，AI 自主决策并记录理由，全程不因提问暂停。', { exact: true }).isVisible())
  const downloaded = page.waitForEvent('download')
  await page.getByRole('button', { name: '导出当前配置', exact: true }).click()
  const file = path.join(output, 'autonomous-template.json')
  await (await downloaded).saveAs(file)
  const template = JSON.parse(await fs.readFile(file, 'utf8'))
  assert.equal(template.production_plan.autonomous, true)
  await autonomy().uncheck()
  await importTemplate(template)
  assert(await autonomy().isChecked(), '导入时恢复自主模式')
  const legacy = structuredClone(template)
  delete legacy.production_plan.autonomous
  await importTemplate(legacy)
  assert.equal(await autonomy().isChecked(), false, '旧模板未声明该字段时保持人工补充')
  await autonomy().check()
  await page.locator('.sidebar-create').click()
  assert.equal(await autonomy().isChecked(), false, '新项目默认不启用自主模式')
  await chooseTemplate()
  await autonomy().check()
  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 })
    await page.evaluate(() => window.scrollTo(0, 0))
    const layout = await page.evaluate(() => {
      const bounds = document.querySelector('.creation-autonomy').getBoundingClientRect()
      return { scrollWidth: document.documentElement.scrollWidth, left: bounds.left, right: bounds.right }
    })
    assert(layout.scrollWidth <= width && layout.left >= 0 && layout.right <= width, `勾选区域不应溢出：${JSON.stringify(layout)}`)
    if (width === 1440 || width === 390) await page.screenshot({ path: path.join(output, `autonomous-${width}.png`) })
  }
  await page.setViewportSize({ width: 1440, height: 1000 })
  await consent().check()
  await start().click()
  await page.getByRole('region', { name: '游戏实时制作工作台', exact: true }).waitFor()
  assert.equal(creations.length, 1)
  assert.equal(creations[0].production_plan.autonomous, true)
  assert.equal(creations[0].start_immediately, true)
  await page.getByRole('button', { name: '返回我的项目', exact: true }).click()
  await page.getByRole('button', { name: '＋ 创建新项目', exact: true }).click()
  await chooseTemplate()
  assert.equal(await autonomy().isChecked(), false)
  await consent().check()
  await start().click()
  await page.getByRole('region', { name: '游戏实时制作工作台', exact: true }).waitFor()
  assert.equal(creations[1].production_plan.autonomous, false)
  assert.deepEqual(unexpectedWrites, [])
  assert.deepEqual(errors, [])
  console.log('自主执行勾选验收通过：' + JSON.stringify({ passed: true, modes: creations.map(item => item.production_plan.autonomous), default_off: true, template_roundtrip: true, confirmation_reset: true, responsive: true, unexpectedWrites, errors }))
} finally {
  await browser.close()
}
