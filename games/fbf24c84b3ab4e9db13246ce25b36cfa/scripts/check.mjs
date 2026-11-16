import { createServer } from 'node:http';
import { readFile, mkdir, writeFile, access } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { fileList, fingerprints } from './build.mjs';

const prefix = '/pipeline-star-check-20261109/';
const config = JSON.parse(await readFile('dist/assets/visual-config.json', 'utf8'));
const before = await fingerprints(await fileList('dist'));
const passed = [], errors = [], requests = [], animationFrames = [];
await mkdir('evidence/browser', { recursive: true });
const types = { html: 'text/html', js: 'text/javascript', css: 'text/css', json: 'application/json', svg: 'image/svg+xml' };
const server = createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    if (!pathname.startsWith(prefix)) { response.writeHead(404); response.end(); return; }
    const relative = pathname.slice(prefix.length) || 'index.html';
    if (relative.includes('..') || relative.includes('\\')) throw Error('拒绝越界');
    const bytes = await readFile(`dist/${relative}`);
    response.writeHead(200, { 'Content-Type': `${types[relative.split('.').pop()] || 'application/octet-stream'};charset=utf-8`, 'Cache-Control': 'no-store' }); response.end(bytes);
  } catch { response.writeHead(404); response.end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const url = `http://127.0.0.1:${server.address().port}${prefix}`;
let browser, browserVersion, failure;
function watch(page) {
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('request', request => {
    requests.push(request.url());
    if (!request.url().startsWith(url) && !request.url().startsWith('data:')) errors.push(`外部请求：${request.url()}`);
  });
  page.on('response', response => { if (response.status() >= 400) errors.push(`资源失败：${response.url()}`); });
  page.on('requestfailed', request => errors.push(`请求失败：${request.url()}`));
}
async function settled(page) {
  await page.waitForFunction(() => document.querySelector('#board').dataset.ready === 'true' && document.querySelector('#board').dataset.scale === '1');
}
async function count(page, expected) { assert.equal(await page.locator('#counter').innerText(), `${expected} / 5`); }
async function position(page, index) {
  const box = await page.locator('#board').boundingBox();
  const [x,y] = config.positions[index]; const inset = config.star.safeInsetCss;
  return { x: box.x + inset + x * (box.width - 2 * inset), y: box.y + inset + y * (box.height - 2 * inset) };
}
async function tap(page, index, touch = false) {
  await settled(page); const point = await position(page,index);
  if (touch) await page.touchscreen.tap(point.x,point.y); else await page.mouse.click(point.x,point.y);
}
async function win(page, touch = false, start = 0) {
  for (let index = start; index < 5; index++) { await tap(page,index,touch); await count(page,index+1); }
  assert.equal(await page.locator('#status').innerText(),'采集完成！');
}
async function restartGame(page) { await page.getByRole('button',{ name: '重开', exact: true }).click(); await settled(page); await count(page,0); }
async function layout(page) {
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),'水平溢出');
  const box = await page.locator('#board').boundingBox();
  assert(box.width >= 288 && box.height >= 360);
  for (let i = 0; i < 5; i++) {
    const point = await position(page,i);
    assert(point.x - box.x >= 40 && box.x + box.width - point.x >= 40);
    assert(point.y - box.y >= 40 && box.y + box.height - point.y >= 40);
  }
  assert((await page.locator('#restart').boundingBox()).height >= 44);
}
try {
  let executablePath = process.env.CHROMIUM_PATH;
  if (!executablePath) for (const path of ['/usr/bin/chromium','/usr/bin/chromium-browser','/opt/google/chrome/chrome']) {
    try { await access(path); executablePath = path; break; } catch {}
  }
  browser = await chromium.launch({ headless: true, executablePath, args: ['--no-sandbox'] });
  browserVersion = browser.version();
  const desktop = await browser.newContext({ viewport: { width:1280,height:800 }, recordVideo: { dir: 'evidence/browser', size: { width:1280,height:800 } } });
  const page = await desktop.newPage(); watch(page); await page.goto(url); await settled(page);
  await layout(page); await count(page,0); await page.screenshot({ path:'evidence/browser/desktop-initial.png' });
  // 采样真实rAF时间和实际绘制缩放，不冻结时间、不注入规则。
  await page.evaluate(() => {
    window.animationTrace = [];
    let until = performance.now() + 600;
    function sample(time) {
      window.animationTrace.push({ time, scale:Number(document.querySelector('#board').dataset.scale) });
      if (time < until) requestAnimationFrame(sample);
    }
    requestAnimationFrame(sample);
  });
  await page.getByRole('button',{ name:'重开',exact:true }).click();
  await page.waitForTimeout(650);
  animationFrames.push(...await page.evaluate(() => window.animationTrace));
  assert(animationFrames.some(frame => frame.scale < 0.98),'未捕获缩小阶段');
  assert(animationFrames.some(frame => frame.scale > 1.04),'未捕获放大阶段');
  assert.equal(animationFrames.at(-1).scale,1);
  passed.push('R7/A3：正常速度rAF缩放采样与桌面连续录像');
  const box = await page.locator('#board').boundingBox();
  await page.mouse.click(box.x+8,box.y+8); await count(page,0);
  const first = await position(page,0);
  await page.mouse.click(first.x,first.y,{ button:'right' }); await count(page,0);
  await page.mouse.move(first.x,first.y); await page.mouse.down();
  await page.mouse.move(first.x+60,first.y); await page.mouse.move(first.x,first.y); await page.mouse.up(); await count(page,0);
  await page.mouse.click(first.x,first.y); await count(page,1);
  const second = await position(page,1); await page.mouse.click(second.x,second.y); await count(page,1);
  await settled(page); await win(page,false,1);
  await page.screenshot({ path:'evidence/browser/desktop-won.png' });
  await tap(page,4); await count(page,5);
  await page.reload(); await settled(page); await count(page,5); assert.equal(await page.locator('#status').innerText(),'采集完成！');
  await restartGame(page); await page.reload(); await settled(page); await count(page,0);
  await tap(page,0); await tap(page,1); await count(page,2);
  await page.reload(); await settled(page); await count(page,2);
  await page.setViewportSize({ width:320,height:568 }); await settled(page); await layout(page); await tap(page,2); await count(page,3);
  await page.setViewportSize({ width:1280,height:800 }); await settled(page); await count(page,3);
  await tap(page,3); await settled(page); const last = await position(page,4);
  await page.mouse.move(last.x,last.y); await page.mouse.down();
  // 键盘重开不释放旧鼠标指针，随后释放必须无效。
  await page.locator('#restart').focus(); await page.keyboard.press('Enter'); await page.mouse.up(); await settled(page); await count(page,0);
  passed.push('R1–R6/R8：鼠标完整循环、空白/右键/拖出/动画锁、胜利重开、刷新与窗口调整、旧局释放');
  // 边界事件与生命周期为明确标记的DOM模拟；核心采集仍使用真实鼠标/触摸。
  const center = await position(page,0);
  await page.evaluate(({x,y}) => {
    const board = document.querySelector('#board');
    for (const type of ['pointerdown','pointerup']) board.dispatchEvent(new PointerEvent(type,{ pointerId:91,isPrimary:false,button:0,clientX:x,clientY:y,bubbles:true }));
  },center); await count(page,0);
  await page.mouse.move(center.x,center.y); await page.mouse.down();
  await page.evaluate(() => document.querySelector('#board').dispatchEvent(new PointerEvent('pointercancel',{ pointerId:1,bubbles:true })));
  await page.mouse.up(); await count(page,0);
  await tap(page,0);
  await page.evaluate(() => {
    Object.defineProperty(document,'hidden',{ configurable:true,value:true }); document.dispatchEvent(new Event('visibilitychange'));
    Object.defineProperty(document,'hidden',{ configurable:true,value:false }); document.dispatchEvent(new Event('visibilitychange'));
    delete document.hidden;
  }); await settled(page); await count(page,1); await tap(page,1); await count(page,2);
  passed.push('R2/R10：非主指针、取消及隐藏返回DOM边界模拟');
  await page.evaluate(() => localStorage.setItem('star-collection-v1','{broken')); await page.reload(); await settled(page); await count(page,0);
  assert.match(await page.locator('#warning').innerText(),/存档无效/);
  await page.evaluate(() => localStorage.setItem('star-collection-v1',JSON.stringify({ version:2,count:2,targetIndex:2,phase:'playing' })));
  await page.reload(); await settled(page); await count(page,0);
  await page.evaluate(() => { window.originalSetItem = Storage.prototype.setItem; Storage.prototype.setItem = function(){ throw new DOMException('模拟写入失败','QuotaExceededError'); }; });
  await tap(page,0); await count(page,1); assert.match(await page.locator('#warning').innerText(),/进度无法保存/);
  await page.waitForTimeout(220); assert.match(await page.locator('#warning').innerText(),/进度无法保存/);
  await page.screenshot({ path:'evidence/browser/storage-warning.png' });
  await tap(page,1); assert.match(await page.locator('#warning').innerText(),/进度无法保存/);
  await page.evaluate(() => { Storage.prototype.setItem = window.originalSetItem; });
  await tap(page,2); assert.equal(await page.locator('#warning').innerText(),'');
  await page.reload(); await settled(page); await count(page,3);
  passed.push('R9：损坏/版本存档回退与模拟写入失败，真实写成功后清除提示');
  await page.emulateMedia({ reducedMotion:'reduce' }); await restartGame(page); await win(page); await restartGame(page);
  passed.push('R7：减少动态效果立即可操作且再次完整获胜');
  await desktop.close();
  for (const viewport of [{ width:390,height:844 },{ width:320,height:568 }]) {
    const mobile = await browser.newContext({ viewport, isMobile:true, hasTouch:true, deviceScaleFactor:2, recordVideo: { dir:'evidence/browser',size:viewport } });
    const phone = await mobile.newPage(); watch(phone); await phone.goto(url); await settled(phone); await layout(phone);
    await phone.screenshot({ path:`evidence/browser/mobile-${viewport.width}-initial.png`,fullPage:true });
    await win(phone,true); await phone.screenshot({ path:`evidence/browser/mobile-${viewport.width}-won.png`,fullPage:true });
    await restartGame(phone); await win(phone,true); await mobile.close();
    passed.push(`R5/R6：${viewport.width}×${viewport.height} Chromium触摸五次获胜、重开与第二局`);
  }
  // 资源故障单独隔离，预期失败不计为正常场景控制台异常。
  const faultContext = await browser.newContext(); const faultPage = await faultContext.newPage();
  await faultPage.route('**/assets/star.svg',route => route.abort());
  await faultPage.goto(url); await faultPage.locator('#retry').waitFor({ state:'visible' });
  assert.equal(await faultPage.locator('#board').getAttribute('data-ready'),'false');
  await faultPage.unroute('**/assets/star.svg'); await faultPage.locator('#retry').click(); await settled(faultPage); await tap(faultPage,0); await count(faultPage,1);
  await faultContext.close(); passed.push('资源失败显示诊断，解除故障后真实重试可玩（独立故障场景）');
  assert.deepEqual(errors,[],'正常场景控制台或资源错误');
  assert(requests.some(request => request.endsWith('/assets/star.svg')));
  assert.equal((await fingerprints(await fileList('dist'))).sha256,before.sha256,'检查改动了最终dist');
  passed.push('R11：独立子路径最终dist、真实资源请求、零外部请求/控制台错误、构建不变');
} catch (error) { failure = error; }
finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
  const result = { result:failure ? '失败':'通过', browser:browserVersion, node:process.version, url, dist:before, passed, errors, animationFrames, limitations:['手机为Chromium视口/触摸模拟，非真机','取消、多指主标志、隐藏返回及存储故障为明确的DOM/API边界模拟','录像为正常运行速度；未进行真人体验或外网发布验收'], failure:failure?.stack };
  await writeFile('evidence/check.json',JSON.stringify(result,null,2)+'\n');
  console.log(`浏览器验收${failure ? '失败':'通过'}：${passed.length}组；静态服务已停止，证据 evidence/check.json。`);
}
if (failure) throw failure;
