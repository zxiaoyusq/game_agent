// 创作页验收：响应式布局、键盘操作和隐藏字段校验，不启动模型任务。
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const base = process.env.APP_URL || 'http://127.0.0.1:24681'
const output = path.resolve(process.env.OUTPUT_DIR || 'logs/creation-redesign')
await fs.mkdir(output, { recursive: true })
const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox'],
})
const page = await browser.newPage({
  viewport: { width: 1440, height: 1050 },
  reducedMotion: 'reduce',
})
const errors = []
const layouts = []
let executionRequests = 0
page.on('pageerror', (error) => errors.push(error.message))
page.on('console', (message) => {
  if (message.type() === 'error') errors.push(message.text())
})

// 原生校验应当拦截无效输入；若意外提交，阻止请求到达真实执行器。
await page.route('**/api/workflow/projects', async (route) => {
  if (route.request().method() === 'POST') {
    executionRequests++
    await route.fulfill({
      status: 400,
      contentType: 'application/json',
      body: '{"detail":"验收脚本禁止创建项目"}',
    })
  } else await route.continue()
})

async function capture(name, fullPage = true) {
  await page.screenshot({ path: path.join(output, `${name}.png`), fullPage })
}

try {
  await page.goto(base)
  await page.locator('.production-entry').click()
  await page.getByRole('button', { name: '＋ 创建新项目', exact: true }).click()
  await page
    .getByRole('button', {
      name: '使用 LUDO · 原版贴图与动画 模板',
      exact: true,
    })
    .waitFor()
  await page.locator('.showcase-games img').first().scrollIntoViewIfNeeded()
  await page.waitForFunction(() =>
    [
      ...document.querySelectorAll('.template-card img,.showcase-games img'),
    ].every((image) => image.complete && image.naturalWidth > 0),
  )
  await page.evaluate(() => {
    window.scrollTo(0, 0)
    return document.fonts.ready
  })
  await capture('desktop-initial')
  await capture('desktop-first-screen', false)

  // 包括侧栏折叠临界值，避免只验证常见设备宽度而漏掉布局缝隙。
  for (const width of [1920, 1440, 1051, 1050, 1024, 768, 760, 390, 320]) {
    await page.setViewportSize({ width, height: 900 })
    await page.waitForFunction(
      () =>
        document.querySelector('#creation-sidebar').inert === innerWidth <= 760,
    )
    const layout = await page.evaluate(() => {
      const sidebar = document
        .querySelector('#creation-sidebar')
        .getBoundingClientRect()
      const main = document
        .querySelector('.studio-main')
        .getBoundingClientRect()
      return {
        width: innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        sidebarRight: sidebar.right,
        mainLeft: main.left,
      }
    })
    assert(layout.scrollWidth <= width, `${width}px 页面不应横向溢出`)
    if (width > 760)
      assert(
        layout.mainLeft >= layout.sidebarRight,
        `${width}px 侧栏不应覆盖正文`,
      )
    layouts.push(layout)
    if (width === 390) {
      await page.evaluate(() => window.scrollTo(0, 0))
      await capture('mobile')
    }
  }

  // 手机导航抽屉关闭后退出焦点顺序；打开时支持循环焦点和 Escape。
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: '打开导航', exact: true }).click()
  const drawer = page.getByRole('dialog', { name: '创作空间导航' })
  await drawer.getByRole('button').first().waitFor()
  await page.waitForFunction(
    () =>
      document.querySelector('#creation-sidebar button') ===
      document.activeElement,
  )
  await page.keyboard.press('Shift+Tab')
  assert.equal(
    await page.evaluate(() => document.activeElement.textContent.trim()),
    '返回首页',
  )
  await page.keyboard.press('Escape')
  await page.waitForFunction(
    () => document.querySelector('#creation-sidebar').inert,
  )
  assert.equal(
    await page.evaluate(() =>
      document.activeElement.getAttribute('aria-label'),
    ),
    '打开导航',
  )
  assert.notEqual(
    await page.evaluate(() => document.body.style.overflow),
    'hidden',
  )

  await page.setViewportSize({ width: 1440, height: 1050 })
  await page
    .getByRole('button', {
      name: '使用 LUDO · 原版贴图与动画 模板',
      exact: true,
    })
    .click()
  await page.waitForFunction(
    () =>
      document.querySelector('[aria-label="项目名称"]').value ===
      'LUDO · 原版美术复现',
  )
  await page.locator('.toast').waitFor({ state: 'hidden' })
  const projectTab = page.getByRole('tab', { name: '项目设定', exact: true })
  await projectTab.focus()
  await page.keyboard.press('ArrowRight')
  assert.equal(
    await page
      .getByRole('tab', { name: /美术与参考/ })
      .getAttribute('aria-selected'),
    'true',
  )
  assert(
    await page.getByLabel('美术需求与修改范围', { exact: true }).isVisible(),
  )
  await page.evaluate(() => window.scrollTo(0, 0))
  await capture('desktop-art')
  await page.getByRole('tab', { name: /美术与参考/ }).focus()
  await page.keyboard.press('End')
  assert.equal(
    await page
      .getByRole('tab', { name: '执行与交付', exact: true })
      .getAttribute('aria-selected'),
    'true',
  )
  await page.keyboard.press('Home')
  assert.equal(await projectTab.getAttribute('aria-selected'), 'true')

  // 切换模型来源只调整配置，不触发制作；两个入口都必须保持可选。
  const provider = page.getByLabel('项目模型来源', { exact: true })
  await provider.selectOption('codex-login')
  assert.equal(await provider.inputValue(), 'codex-login')
  await provider.selectOption('api-key')
  await page.waitForFunction(() =>
    document.querySelector('.creation-runtime:not(.unavailable)'),
  )

  // 必填字段藏在其他页签时，提交要自动展开并聚焦错误，不能悄悄失败。
  await page.getByLabel('项目名称', { exact: true }).fill('')
  await page.getByRole('tab', { name: /美术与参考/ }).click()
  await page.getByLabel(/我已确认玩法、美术、模型和交付设置/).check()
  await page
    .getByRole('button', { name: '确认需求并开始全流程', exact: true })
    .click()
  await page.waitForFunction(
    () => document.activeElement.getAttribute('aria-label') === '项目名称',
  )
  assert.equal(await projectTab.getAttribute('aria-selected'), 'true')
  assert.equal(executionRequests, 0)
  assert.deepEqual(errors, [])
  const report = {
    passed: true,
    layouts,
    keyboard_tabs: true,
    mobile_navigation: true,
    hidden_validation: true,
    model_sources: true,
    executionRequests,
    errors,
  }
  await fs.writeFile(
    path.join(output, 'layout-report.json'),
    JSON.stringify(report, null, 2),
  )
  console.log('创作页视觉与交互验收通过：' + JSON.stringify(report))
} finally {
  await browser.close()
}
