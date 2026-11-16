// 对上传包的真实画面和输入做验收，读取引擎状态仅用于断言，不注入局面或调用通关函数。
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const base = process.env.APP_URL || 'http://127.0.0.1:24681'
const root = path.resolve(import.meta.dirname, '../..')
const ids = ['arrow-out-puzzle-lite', 'crazy-knifes', 'solitaire-klondike-classic']
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] })
const results = []
const origin = new URL(base).origin
try {
  for (const id of ids) {
    const context = await browser.newContext({ viewport: { width: 500, height: 900 } })
    const errors = [], missing = [], external = []
    // 验收禁止访问第三方广告或统计，任何远端依赖都会被记录，不能静默当成离线成功。
    await context.route('**/*', route => {
      const url = new URL(route.request().url())
      if (url.protocol.startsWith('http') && url.origin !== origin) { external.push(url.href); return route.abort() }
      return route.continue()
    })
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(error.message))
    page.on('response', response => {
      if (response.url().includes('/produced-games/') && response.status() >= 400) missing.push(response.url())
    })
    const catalog = await (await context.request.get(`${base}/api/produced-games`)).json()
    const item = catalog.items.find(game => game.id === id)
    assert.ok(item?.available)
    await page.goto(base)
    await page.getByRole('button', { name: '产出游戏，选择并运行游戏' }).click()
    await page.getByRole('button', { name: `选择 ${item.name}`, exact: true }).click()
    await page.getByRole('button', { name: '▶ 开始游戏', exact: true }).click()
    await page.waitForFunction(() => document.querySelector('.game-screen > iframe')?.contentDocument?.querySelector('#iframe')?.contentDocument?.querySelector('canvas'))
    const frame = page.frames().find(value => value.url().includes(`/${id}/play/game/index.html`))
    assert.ok(frame)
    // 手机页面的播放器位于列表下方，先滚动外层页面，再操作嵌套游戏中的控件。
    await page.locator('.game-screen > iframe').scrollIntoViewIfNeeded()
    const checks = []
    const evidence = path.join(root, 'games', id, 'evidence')
    await fs.mkdir(evidence, { recursive: true })

    if (id === 'arrow-out-puzzle-lite') {
      await frame.waitForFunction(() => {
        const node = window.cc?.find('Canvas/View/UIVMain/mapNode/ArrowPuzzzle')
        const cells = node?.getComponentsInChildren('ArrowCell').filter(cell => cell.node.activeInHierarchy) || []
        return node?.getComponent('ArrowPuzzzle')?.isInputEnabled && cells.length > 0 && cells.every(cell => cell.headSprite)
      })
      const target = await frame.evaluate(() => {
        const node = cc.find('Canvas/View/UIVMain/mapNode/ArrowPuzzzle')
        const cells = node.getComponentsInChildren('ArrowCell').filter(cell => cell.headSprite && cell.node.activeInHierarchy)
        // 教程箭头的头部图片会跳动，点击稳定的箭身起点，避免把动画坐标当命中区。
        const points = cells.map(cell => cell.node.convertToWorldSpaceAR(cc.v2(0, 0)))
        const highest = points.sort((a, b) => b.y - a.y)[0]
        const size = cc.view.getVisibleSize()
        return { count: cells.length, x: highest.x / size.width, y: 1 - highest.y / size.height }
      })
      await page.locator('.game-screen > iframe').screenshot({ path: path.join(evidence, 'desktop-lobby.jpg'), type: 'jpeg', quality: 85 })
      await frame.locator('canvas').scrollIntoViewIfNeeded()
      const box = await frame.locator('canvas').boundingBox()
      await page.mouse.click(box.x + box.width * target.x, box.y + box.height * target.y)
      await frame.waitForFunction(count => cc.find('Canvas/View/UIVMain/mapNode/ArrowPuzzzle').getComponentsInChildren('ArrowCell').filter(cell => cell.headSprite && cell.node.activeInHierarchy).length < count, target.count)
      checks.push('Cocos 场景可见，真实点击移出第一根箭头')
    } else if (id === 'crazy-knifes') {
      await frame.waitForFunction(() => window.Game?.instance?.controlsEnabled && window.Knife?.instance)
      await page.locator('.game-screen > iframe').screenshot({ path: path.join(evidence, 'desktop-lobby.jpg'), type: 'jpeg', quality: 85 })
      const before = await frame.evaluate(() => ({ firstJump: Game.instance.firstJump, x: Knife.instance.entity.getPosition().x }))
      assert.equal(before.firstJump, true)
      // 使用画布在页面上的实际位置点击，适配固定手机视口的等比缩放。
      const box = await frame.locator('canvas').boundingBox()
      await page.mouse.click(box.x + box.width * .45, box.y + box.height * .4)
      await frame.waitForFunction(() => Game.instance.firstJump === false)
      await frame.waitForFunction(x => Knife.instance.entity.getPosition().x !== x, before.x)
      checks.push('PlayCanvas 和物理资源正常，真实点击使飞刀跳跃并移动')
    } else {
      await frame.getByRole('button', { name: 'Skip for now', exact: true }).click()
      await frame.waitForFunction(() => window.game?.scene.getScenes(true).some(scene => scene.gameplay?.boardGame?.stock?.cards.length > 0 && !scene.gameplay.boardGame.isDealing()))
      await page.locator('.game-screen > iframe').screenshot({ path: path.join(evidence, 'desktop-lobby.jpg'), type: 'jpeg', quality: 85 })
      const before = await frame.evaluate(() => {
        const scene = game.scene.getScenes(true).find(scene => scene.gameplay?.boardGame)
        const board = scene.gameplay.boardGame
        const box = board.stock.slot.getBounds()
        // 纸牌场景使用相机缩放，将牌堆的世界坐标换算到实际可见区域。
        const view = scene.cameras.main.worldView
        return { cards: board.stock.cards.length, moves: board.moves, x: (box.centerX - view.x) / view.width, y: (box.centerY - view.y) / view.height }
      })
      await frame.locator('canvas').scrollIntoViewIfNeeded()
      const box = await frame.locator('canvas').boundingBox()
      await page.mouse.click(box.x + box.width * before.x, box.y + box.height * before.y)
      await frame.waitForFunction(count => game.scene.getScenes(true).find(scene => scene.gameplay?.boardGame).gameplay.boardGame.stock.cards.length < count, before.cards)
      const reward = await frame.evaluate(() => SolitairePlatform.showReward())
      assert.equal(reward.rewarded, false)
      await frame.waitForFunction(() => document.documentElement.dataset.platformGamePaused !== 'true')
      checks.push('Phaser 纸牌界面正常，真实点击牌堆完成发牌；广告不可用时不发奖励且恢复游戏')
    }
    await page.locator('.game-screen > iframe').screenshot({ path: path.join(evidence, 'interaction.png') })
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)
    await page.getByRole('button', { name: '结束试玩', exact: true }).click()
    assert.equal(await page.locator('.game-screen > iframe').count(), 0)
    assert.deepEqual(errors, [])
    assert.deepEqual(missing, [])
    assert.deepEqual(external, [])
    results.push({ id, status: 'passed', checks, page_errors: errors, missing_resources: missing, external_requests: external })
    console.log(JSON.stringify(results.at(-1)))
    await context.close()
  }

  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } })
  await page.goto(base)
  await page.getByRole('button', { name: '产出游戏，选择并运行游戏' }).click()
  await page.getByRole('button', { name: '选择 口袋西洋跳棋 · Checkers Pocket', exact: true }).click()
  assert.equal(await page.getByRole('button', { name: '待补全运行包', exact: true }).isDisabled(), true)
  assert.equal(await page.getByRole('link', { name: '新窗口打开 ↗' }).count(), 0)
  assert.equal(await page.locator('.game-screen > iframe').count(), 0)
  await page.getByText('还缺少游戏内容', { exact: true }).waitFor()
  await page.screenshot({ path: path.join(root, 'docs/produced-games/imported-library.png'), fullPage: true })
  results.push({ id: 'checkers-pocket', status: 'missing_game_content', checks: ['原包仅有广告示例，条目显示原因并禁用运行，不把测试按钮当成游戏'] })
  await fs.writeFile(path.join(root, 'docs/produced-games/imported-results.json'), JSON.stringify({ playable: 3, incomplete: 1, items: results }, null, 2) + '\n')
  console.log('上传包验收完成：3 款可玩，1 款缺少游戏内容。')
} finally {
  await browser.close()
}
