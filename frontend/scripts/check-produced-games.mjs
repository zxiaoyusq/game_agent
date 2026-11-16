// 验收真实目录与浏览器输入；仅失败/空列表用例替换响应，不注入游戏状态。
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const base = process.env.APP_URL || 'http://127.0.0.1:24681'
const evidence = path.resolve(import.meta.dirname, '../../docs/produced-games')
await fs.mkdir(evidence, { recursive: true })
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] })
const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } })
const page = await context.newPage()
const errors = []
const missingResources = []
const checks = []
page.on('pageerror', error => errors.push(error.message))
page.on('response', response => {
  if (response.url().includes('/play/') && response.status() >= 400) missingResources.push(response.url())
})
async function selectAndPlay(id) {
  const item = catalog.items.find(game => game.id === id)
  await page.getByRole('button', { name: `选择 ${item.name}`, exact: true }).click()
  await page.getByRole('button', { name: '▶ 开始游戏', exact: true }).click()
  await page.locator('iframe').waitFor()
  return page.frames().find(frame => frame.url().includes(`/produced-games/${id}/play/`))
    || await new Promise(resolve => page.once('framenavigated', resolve))
}
let catalog
try {
  const response = await context.request.get(`${base}/api/produced-games`)
  assert.equal(response.status(), 200)
  catalog = await response.json()
  assert.ok(catalog.items.length >= 3, '当前三款游戏必须全部出现在目录中')
  await page.goto(base)
  const entry = page.getByRole('button', { name: '产出游戏，选择并运行游戏' })
  await entry.waitFor()
  await page.waitForFunction(total => document.querySelector('.game-entry .stat-num')?.textContent === String(total), catalog.total)
  await entry.click()
  assert.equal(await page.locator('.game-card').count(), catalog.total)
  await page.screenshot({ path: path.join(evidence, 'library-desktop.png'), fullPage: true })
  checks.push('首页产出游戏入口显示真实数量，全部运行包出现在游戏库')

  // 左侧滚动及滚动到底后继续操作，都不能推动运行区域或整页。
  const screenBeforeScroll = await page.locator('.game-screen').boundingBox()
  const gameList = page.locator('.game-list')
  await gameList.hover()
  await page.mouse.wheel(0, 5000)
  await page.waitForFunction(() => document.querySelector('.game-list').scrollTop > 0)
  assert.deepEqual(await page.locator('.game-screen').boundingBox(), screenBeforeScroll)
  await page.mouse.wheel(0, 1000)
  await page.locator('.game-card').last().getByRole('button', { name: /^选择 / }).click()
  assert.equal(await page.evaluate(() => scrollY), 0)
  assert.equal(await page.evaluate(() => document.documentElement.scrollHeight <= innerHeight), true)
  assert.equal((await page.locator('.play-panel').boundingBox()).y, (await page.locator('.library-layout').boundingBox()).y)
  checks.push('左侧列表可独立滚动到最后一款，运行区域固定且整页不滚动')

  await page.getByRole('searchbox', { name: '搜索产出游戏' }).fill('彩球')
  assert.equal(await page.locator('.game-card').count(), 1)
  await page.getByRole('searchbox').fill('不存在的游戏名称')
  await page.getByText('没有找到匹配的游戏', { exact: true }).waitFor()
  await page.getByRole('button', { name: '清空搜索' }).click()
  assert.equal(await page.locator('.game-card').count(), catalog.total)
  checks.push('游戏名称搜索、无匹配反馈和清空搜索可用')

  // 游戏列表使用完整高度，操作区放在右侧；预览缩放后仍保持 720×1600 的内部视口。
  let frame = await selectAndPlay('one-connect')
  await frame.waitForFunction(() => window.cr_getC2Runtime?.()?.running_layout)
  assert.equal(await page.locator('.game-details .play-actions').count(), 1)
  assert.equal(await page.locator('.game-picker .play-actions').count(), 0)
  assert.equal(await page.locator('.play-panel .play-actions').count(), 0)
  for (const viewport of [{ width: 1440, height: 1100 }, { width: 1280, height: 720 }, { width: 1920, height: 1080 }]) {
    await page.setViewportSize(viewport)
    await frame.waitForFunction(() => {
      const runtime = cr_getC2Runtime()
      return innerWidth === 720 && innerHeight === 1600 && runtime.width === 720 && runtime.height === 1600
    })
    await page.waitForFunction(() => {
      const player = document.querySelector('.play-panel').getBoundingClientRect()
      const frame = document.querySelector('.game-screen > iframe').getBoundingClientRect()
      const height = Math.min(player.height - 4, (player.width - 4) * 1600 / 720, 1600)
      return Math.abs(frame.height - height) < 1
    })
    const player = await page.locator('.play-panel').boundingBox()
    const screen = await page.locator('.game-screen > iframe').boundingBox()
    assert.ok(Math.abs(screen.width / screen.height - 720 / 1600) < .001)
    assert.ok(screen.x >= player.x && screen.y >= player.y)
    assert.ok(screen.x + screen.width <= player.x + player.width)
    assert.ok(screen.y + screen.height <= player.y + player.height)
    assert.ok((await gameList.boundingBox()).height >= viewport.height * .75)
    assert.ok((await page.locator('.game-details').boundingBox()).x >= player.x + player.width)
    assert.equal(await page.evaluate(() => scrollY), 0)
  }
  await page.setViewportSize({ width: 1440, height: 1100 })
  checks.push('列表获得完整高度，操作区位于右侧，游戏按固定 720×1600 手机视口等比预览')

  frame = await selectAndPlay('amber-caravan')
  await frame.locator('[data-action="start"]').click()
  await frame.locator('#roll-button').click()
  await frame.waitForFunction(() => window.amberCaravan.snapshot().game.stats.rolls > 0)
  const playingScreen = await page.locator('.game-screen').boundingBox()
  await gameList.hover()
  await page.mouse.wheel(0, 1000)
  await page.waitForFunction(() => document.querySelector('.game-list').scrollTop > 0)
  assert.deepEqual(await page.locator('.game-screen').boundingBox(), playingScreen)
  assert.equal(await frame.evaluate(() => window.amberCaravan.snapshot().game.stats.rolls > 0), true)
  await page.screenshot({ path: path.join(evidence, 'playing-desktop.png'), fullPage: true })
  checks.push('琥珀商路在内嵌窗口真实开局并完成掷骰')
  const previousFrame = frame
  await page.getByRole('button', { name: '↻ 重新运行', exact: true }).click()
  await page.frameLocator('iframe').locator('[data-action="start"]').waitFor()
  assert.equal(previousFrame.isDetached(), true)
  checks.push('重新运行销毁旧实例并加载新实例')

  frame = await selectAndPlay('amber-caravan-api')
  await frame.locator('#start').click()
  await frame.locator('#tutorial-skip').click()
  await frame.locator('#roll').waitFor()
  const revision = await frame.locator('.amber-game').getAttribute('data-revision')
  await frame.locator('#roll').click()
  await frame.waitForFunction(previous => document.querySelector('.amber-game')?.dataset.revision !== previous, revision)
  checks.push('琥珀商路 API 版本可开局并操作骰子')

  frame = await selectAndPlay('ball-sort-fusion')
  await frame.waitForFunction(() => Boolean(window.ballSortGame))
  const state = await frame.evaluate(() => window.ballSortGame.getState())
  const engine = await frame.evaluate(() => window.ballSortGame.getEngineInfo())
  assert.equal(engine.graphicsApi, 'WEBGL2')
  assert.ok(engine.drawCalls > 0)
  await frame.locator('canvas').scrollIntoViewIfNeeded()
  const rect = await frame.locator('canvas').boundingBox()
  const scale = Math.min(rect.width / 540, rect.height / 960)
  for (const index of state.solution[0]) {
    const point = state.tubePositions[index]
    await page.mouse.click(rect.x + (rect.width - 540 * scale) / 2 + (270 + point.x) * scale,
      rect.y + (rect.height - 960 * scale) / 2 + (480 - point.y) * scale)
  }
  await frame.waitForFunction(moves => window.ballSortGame.getState().moves > moves, state.moves)
  checks.push('彩球融境真实运行 Cocos WebGL，点击完成一次合法移动')

  const popupPromise = context.waitForEvent('page')
  await page.getByRole('link', { name: '新窗口打开 ↗' }).click()
  const popup = await popupPromise
  await popup.waitForFunction(() => Boolean(window.ballSortGame))
  assert.equal(await page.locator('iframe').count(), 0)
  assert.equal(await popup.evaluate(() => window.opener), null)
  await popup.close()
  checks.push('新窗口可独立运行，同时关闭原内嵌实例')

  await page.setViewportSize({ width: 390, height: 844 })
  await page.evaluate(() => window.scrollTo(0, 0))
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)
  await page.screenshot({ path: path.join(evidence, 'library-mobile.png'), fullPage: true })
  frame = await selectAndPlay('amber-caravan')
  await frame.locator('[data-action="start"]').click()
  await frame.locator('#roll-button').click()
  await frame.waitForFunction(() => window.amberCaravan.snapshot().game.stats.rolls > 0)
  await page.screenshot({ path: path.join(evidence, 'playing-mobile.png'), fullPage: true })
  await page.getByRole('button', { name: '结束试玩', exact: true }).click()
  assert.equal(await page.locator('iframe').count(), 0)
  checks.push('390px 手机布局无页面横向溢出，可选择、游玩和结束游戏')

  // 请求异常有真实提示且可重试；列表为空时有工作台入口，不保留旧游戏。
  await page.route('**/api/produced-games', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: '目录服务暂时不可用' }) }))
  await page.getByRole('button', { name: '↻ 刷新列表', exact: true }).click()
  await page.getByRole('alert').getByText('目录服务暂时不可用').waitFor()
  await page.unroute('**/api/produced-games')
  await page.getByRole('button', { name: '重新加载', exact: true }).click()
  await page.waitForFunction(() => !document.querySelector('[role="alert"]'))
  await page.route('**/api/produced-games', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ total: 0, items: [] }) }))
  await page.getByRole('button', { name: '↻ 刷新列表', exact: true }).click()
  await page.getByText('第一款作品，等待登场', { exact: true }).waitFor()
  assert.equal(await page.locator('iframe').count(), 0)
  await page.unroute('**/api/produced-games')
  await page.getByRole('button', { name: '← 返回首页', exact: true }).click()
  await page.getByRole('button', { name: '产出游戏，选择并运行游戏' }).waitFor()
  checks.push('目录失败可恢复、空目录有引导，返回首页正常')

  assert.deepEqual(errors, [])
  assert.deepEqual(missingResources, [])
  const result = { status: 'passed', games: catalog.items.map(item => item.id), checks, page_errors: errors, missing_resources: missingResources }
  await fs.writeFile(path.join(evidence, 'browser-results.json'), JSON.stringify(result, null, 2) + '\n')
  console.log(JSON.stringify(result, null, 2))
} finally {
  await browser.close()
}
