// 登录验收使用真实账号接口，阻止生成和修改业务数据；密码通过环境变量传入。
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const base = process.env.APP_URL || 'http://127.0.0.1:24681'
const username = process.env.LOGIN_USERNAME || 'admin'
const password = process.env.LOGIN_PASSWORD
assert(password, '请通过 LOGIN_PASSWORD 提供验收账号密码')
const output = path.resolve(process.env.OUTPUT_DIR || 'logs/login')
await fs.mkdir(output, { recursive: true })
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] })
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
const page = await context.newPage()
const errors = [], unexpectedWrites = [], layouts = []
let failLoginOnce = false
page.on('pageerror', error => errors.push(error.message))
await context.route('**/api/**', async route => {
  const request = route.request(), pathname = new URL(request.url()).pathname
  if (!pathname.startsWith('/api/')) return route.continue()
  if (pathname === '/api/auth/login' && failLoginOnce) {
    failLoginOnce = false
    return route.fulfill({ status: 503, json: { detail: '登录服务暂不可用，请重试。' } })
  }
  if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method()) && !pathname.startsWith('/api/auth/')) {
    unexpectedWrites.push(pathname)
    return route.abort()
  }
  return route.continue()
})
const loginHeading = () => page.getByRole('heading', { name: '登录创作空间', exact: true })
async function signIn(value = password) {
  await page.getByLabel('用户名', { exact: true }).fill(username)
  await page.getByLabel('密码', { exact: true }).fill(value)
  await page.getByRole('button', { name: '登录', exact: true }).click()
}

try {
  const anonymous = await context.request.get(base + '/api/workflow/projects')
  assert.equal(anonymous.status(), 401)
  await page.goto(base)
  await loginHeading().waitFor()
  await page.getByLabel('用户名', { exact: true }).waitFor()
  assert.equal(await page.locator('.production-entry').count(), 0)
  assert(await page.getByRole('button', { name: '登录', exact: true }).isDisabled())
  await page.screenshot({ path: path.join(output, 'login-desktop.png') })
  await signIn('incorrect-password-for-validation')
  await page.getByRole('alert').filter({ hasText: '用户名或密码错误' }).waitFor()
  await page.getByRole('button', { name: '显示密码', exact: true }).click()
  assert.equal(await page.getByLabel('密码', { exact: true }).getAttribute('type'), 'text')
  await page.getByRole('button', { name: '隐藏密码', exact: true }).click()
  failLoginOnce = true
  await signIn()
  await page.getByRole('alert').filter({ hasText: '登录服务暂不可用' }).waitFor()
  await signIn()
  await page.locator('.production-entry').waitFor()
  assert.equal(await page.locator('.user-name').innerText(), username)
  const cookie = (await context.cookies()).find(item => item.name === 'game_agent_session')
  assert(cookie?.httpOnly)
  assert.equal(cookie.sameSite, 'Lax')
  assert(!(await page.evaluate(() => document.cookie)).includes('game_agent_session'))
  const localValues = await page.evaluate(() => Object.values(localStorage).join('\n'))
  assert(!localValues.includes(password))
  assert(!localValues.includes(cookie.value))
  const blockedWrite = await context.request.post(base + '/api/workflow/projects', { data: { name: '不应创建' } })
  assert.equal(blockedWrite.status(), 403)
  await page.reload()
  await page.locator('.production-entry').waitFor()
  await page.locator('.production-entry').click()
  await page.locator('.project-library').waitFor()
  assert.equal((await context.request.get(base + '/api/workflow/projects')).status(), 200)
  // 在另一标签页退出，当前工作台同步回到登录页，旧会话也应被后端撤销。
  const other = await context.newPage()
  other.on('pageerror', error => errors.push(error.message))
  await other.goto(base)
  await other.getByRole('button', { name: '退出登录', exact: true }).click()
  await loginHeading().waitFor()
  const replay = await fetch(base + '/api/auth/session', { headers: { Cookie: 'game_agent_session=' + cookie.value } })
  assert.equal(replay.status, 401)
  await other.close()
  // 重新登录后回到原模块，接口发现会话被撤销时也会触发登录入口。
  await signIn()
  await page.locator('.project-library').waitFor()
  await context.request.post(base + '/api/auth/logout', { headers: { 'X-Requested-With': 'GameAgent' } })
  await page.locator('.library-controls').getByRole('button', { name: '刷新', exact: true }).click()
  await loginHeading().waitFor()
  for (const width of [1440, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 })
    const layout = await page.evaluate(() => ({ width: innerWidth, scrollWidth: document.documentElement.scrollWidth }))
    assert(layout.scrollWidth <= width, `${width}px 登录页不应横向溢出`)
    layouts.push(layout)
  }
  await page.getByLabel('密码', { exact: true }).fill('')
  await page.setViewportSize({ width: 390, height: 844 })
  await page.screenshot({ path: path.join(output, 'login-mobile.png') })
  assert.deepEqual(errors, [])
  assert.deepEqual(unexpectedWrites, [])
  console.log('登录验收通过：' + JSON.stringify({ login: true, password_error: true, retry: true,
    session_refresh: true, server_logout: true, cross_tab_logout: true, unauthorized_api: 401,
    csrf_protection: 403, layouts, errors, unexpectedWrites }))
} finally {
  await context.request.post(base + '/api/auth/logout', { headers: { 'X-Requested-With': 'GameAgent' } }).catch(() => {})
  await browser.close()
}
