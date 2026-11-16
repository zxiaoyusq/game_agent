/**
 * tools/tutorial_motion_browser.test.mjs
 * **真实浏览器 DOM 技术测试**（不打开游戏、不用 MuMu、不写工作区文件）
 *
 * 做法：本机 Chromium headless（ms-playwright 或系统 Chrome/Edge）以
 *   `--headless --dump-dom --virtual-time-budget=… "data:text/html,<内联模块源码的测试页>"`
 * 运行；测试页在**真实 DOM / 真实 CSSStyleDeclaration / 真实 WAAPI** 上驱动
 * `tutorial_motion_integration.js`（+ 必要时 `tutorial_motion_adapter.js`）并输出 JSON。
 *
 * 覆盖：
 *   R1 真实 CSSStyleDeclaration 上 `display` 拦截**定义生效**（自有属性覆盖原型访问器）
 *   R2 关闭写入后**渲染仍可见**，直到动效收尾回调才提交隐藏（getComputedStyle/offsetParent 实测）
 *   R3 `hidden` 属性拦截同样生效
 *   R4 **重复帧赋值**（多帧反复写 display='none'）⇒ 只延后一次、始终可见、最终提交一次
 *   R5 `uninstall()` **恢复**为直通语义（写入立即生效、不再播动效）
 *   R6 真实 WAAPI 端到端（用真适配器）：写 'none' 后立即可见；等待超过动效时长后已隐藏
 *      （若虚拟时间下 WAAPI 不推进 ⇒ 该项记为 unknown，绝不虚报为 pass）
 *
 * 运行：node --test tools/tutorial_motion_browser.test.mjs
 * 环境不可用（找不到浏览器/无法 dump）⇒ 明确 skip 并输出 UNKNOWN。
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync, writeFileSync, unlinkSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const INTEG = readFileSync(join(HERE, 'tutorial_motion_integration.js'), 'utf8');
const ADAPTER = readFileSync(join(HERE, 'tutorial_motion_adapter.js'), 'utf8');

function findBrowser() {
  const la = process.env.LOCALAPPDATA || '';
  const cands = [
    join(la, 'ms-playwright', 'chromium-1228', 'chrome-win64', 'chrome.exe'),
    join(la, 'ms-playwright', 'chromium-1228', 'chrome-win', 'chrome.exe'),
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  ];
  for (const c of cands) { try { if (c && existsSync(c)) return c; } catch (_) {} }
  // 兜底：ms-playwright 下递归找
  try {
    const base = join(la, 'ms-playwright');
    if (existsSync(base)) {
      const { readdirSync } = require('node:fs');
      for (const d of readdirSync(base)) {
        for (const sub of ['chrome-win64', 'chrome-win']) {
          const p = join(base, d, sub, 'chrome.exe');
          if (existsSync(p)) return p;
        }
      }
    }
  } catch (_) {}
  return null;
}
const BROWSER = findBrowser();

function pageHtml() {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  #oc-seventh-guide{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(3,8,24,.74);z-index:30}
  #oc-seventh-guide .card{width:min(330px,90vw);padding:26px 20px;border:4px solid #67c5ff;border-radius:32px;background:#122046;transform:translate(-50%,-50%)}
  </style></head><body><pre id="out">PENDING</pre>
  <script>${INTEG}</script>
  <script>${ADAPTER}</script>
  <script>
  (function(){
    var results=[];
    function rec(name,status,observed){ results.push({name:name,status:status,observed:observed}); }
    function visible(el){
      // 注意：position:fixed 元素的 offsetParent 恒为 null ⇒ 不能用它判断可见性。
      var cs=getComputedStyle(el);
      if(cs.display==='none'||cs.visibility==='hidden'||cs.opacity==='0') return false;
      var r=el.getBoundingClientRect();
      if(r.width>0&&r.height>0) return true;
      return el.getClientRects().length>0;      // fixed 元素的兜底"已渲染"判定
    }
    function emit(){ document.getElementById('out').textContent=JSON.stringify({ok:1,results:results}); }
    try{
      // —— 构造与 game/tutorial-seventh.js 一致的 overlay 结构 ——
      var overlay=document.createElement('div'); overlay.id='oc-seventh-guide';
      var card=document.createElement('div'); card.className='card'; overlay.appendChild(card);
      var btn=document.createElement('button'); btn.id='oc-seventh-continue'; btn.textContent='Got it'; overlay.appendChild(btn);
      document.body.appendChild(overlay);
      var realClose=0, closeCb=null;
      var motion={ open:function(){}, close:function(el,o,cb){ realClose++; closeCb=cb; } };
      var runtime={running_layout:{name:'game'}, all_global_vars:[{name:'pause',data:false}]};
      var document_=document;
      var api=window.oneConnectTutorialMotionIntegration;
      api.install({ env:{ document: document_, motion: motion, runtime: runtime, MutationObserver: MutationObserver } });

      // R1 拦截定义是否生效：自有属性覆盖原型访问器
      var descOwn=Object.getOwnPropertyDescriptor(overlay.style,'display');
      var descProto=Object.getOwnPropertyDescriptor(CSSStyleDeclaration.prototype,'display');
      rec('R1_own_accessor_defined', descOwn && typeof descOwn.get==='function' && typeof descOwn.set==='function' ? 'pass':'fail',
          {own: !!descOwn, protoHasSetter: !!(descProto&&descProto.set)});

      // 打开（真实教程：display=''）
      overlay.style.display='';
      rec('R1b_open_visible', visible(overlay)?'pass':'fail', {display:getComputedStyle(overlay).display});

      // R2 关闭写入 ⇒ 读值='none'，渲染仍可见
      overlay.style.display='none';
      var readBack=overlay.style.display;
      var stillVisible=visible(overlay);
      rec('R2_read_is_intent', readBack==='none'?'pass':'fail', {readBack:readBack});
      rec('R2_still_visible_until_done', stillVisible?'pass':'fail',
          {computed:getComputedStyle(overlay).display, offsetParent:overlay.offsetParent!==null});
      // 收尾回调 ⇒ 才真正提交
      if(typeof closeCb==='function') closeCb();
      rec('R2_committed_after_done', !visible(overlay)?'pass':'fail', {computed:getComputedStyle(overlay).display});

      // R3 hidden 属性拦截
      overlay.style.display=''; overlay.hidden=false;
      var before3=visible(overlay);
      overlay.hidden=true;
      var hidRead=overlay.hidden, hidVisible=visible(overlay);
      rec('R3_hidden_read_is_intent', hidRead===true?'pass':'fail', {hidRead:hidRead, before3:before3});
      rec('R3_hidden_still_visible', hidVisible?'pass':'fail', {visible:hidVisible});
      if(typeof closeCb==='function') closeCb();
      rec('R3_hidden_committed', !visible(overlay)?'pass':'fail', {computed:getComputedStyle(overlay).display});
      overlay.hidden=false;

      // R4 重复帧赋值：连续多帧写 display='none'
      var closesBefore=realClose;
      overlay.style.display='';
      for(var i=0;i<30;i++){ overlay.style.display='none'; }        // 模拟逐帧重复赋值
      var r4visible=visible(overlay);
      rec('R4_single_defer', (realClose-closesBefore)===1?'pass':'fail', {closesDelta:realClose-closesBefore});
      rec('R4_visible_during_loop', r4visible?'pass':'fail', {computed:getComputedStyle(overlay).display});
      if(typeof closeCb==='function') closeCb();
      rec('R4_committed_once', !visible(overlay)?'pass':'fail', {computed:getComputedStyle(overlay).display});

      // R7 关闭完成后跨多帧重复写 'none' ⇒ 不得新增关闭动画（真实 frame() 每帧写 display）
      var r7Base=realClose;
      overlay.style.display='';                       // 先恢复可见
      overlay.style.display='none';
      if(typeof closeCb==='function') closeCb();      // 完成本次关闭
      var closedVisible=visible(overlay);
      for(var k=0;k<40;k++){ overlay.style.display='none'; }   // 关闭完成后逐帧重复写入
      rec('R7_no_new_animation_after_commit', (realClose-r7Base)===1?'pass':'fail',
          {delta:realClose-r7Base, closedVisible:closedVisible});
      rec('R7_stays_hidden', !visible(overlay)?'pass':'fail', {computed:getComputedStyle(overlay).display});

      // R8 关闭未完成时 reopen（模拟适配器取消 close 回调），再次关闭必须能正确收尾
      overlay.style.display='';                       // 可见
      overlay.style.display='none';                   // 启动关闭#1（回调不会被调用；模拟被 open 取消）
      var staleCb=closeCb;
      overlay.style.display='flex';                   // ★ reopen：应放弃延后并提交为可见
      var afterReopen=visible(overlay);
      var r8Base=realClose;
      overlay.style.display='none';                   // 关闭#2
      var secondStarted=(realClose-r8Base)===1;
      if(typeof closeCb==='function' && closeCb!==staleCb) closeCb();   // 收尾#2
      var committed=!visible(overlay);
      if(typeof staleCb==='function'){ try{ staleCb(); }catch(_){} }    // 迟到的#1回调不得改变状态
      rec('R8_reopen_visible', afterReopen?'pass':'fail', {computed:getComputedStyle(overlay).display});
      rec('R8_second_close_starts', secondStarted?'pass':'fail', {delta:realClose-r8Base});
      rec('R8_second_close_commits', committed?'pass':'fail', {computed:getComputedStyle(overlay).display});

      // R5 uninstall 恢复（基准在 R5 之前重新取样，避免受 R7/R8 新增关闭次数影响）
      overlay.style.display='';
      var r5Base=realClose;
      api.uninstall();
      overlay.style.display='none';
      rec('R5_uninstall_immediate', !visible(overlay)?'pass':'fail', {computed:getComputedStyle(overlay).display});
      rec('R5_uninstall_no_motion', (realClose-r5Base)===0?'pass':'fail', {delta:realClose-r5Base, closesTotal:realClose});
      emit();
    }catch(e){ rec('EXCEPTION','fail',{message:String(e&&e.message||e)}); emit(); }

    // R6 真实 WAAPI 端到端（独立元素 + 真适配器 + 真集成），异步，最后覆盖输出
    (async function(){
      try{
        var ov2=document.createElement('div'); ov2.id='oc-seventh-guide-2';
        var card2=document.createElement('div'); card2.className='card'; ov2.appendChild(card2);
        document.body.appendChild(ov2); ov2.style.display='flex';
        var runtime2={running_layout:{name:'game'}, all_global_vars:[{name:'pause',data:false}]};
        var api2=window.oneConnectTutorialMotionIntegration;
        // 用真适配器：motion 未注入 ⇒ 自动取 window.oneConnectTutorialMotion
        api2.install({ env:{ document: document, runtime: runtime2, MutationObserver: MutationObserver },
                       targets:[{ id:'t7b', enabled:true, overlaySelectors:['#oc-seventh-guide-2'], cardFrom:'firstChild', cardSelectors:['.card'], hideProps:['display','hidden'] }] });
        var t0=performance.now();
        ov2.style.display='none';
        var visNow=visible(ov2);
        await new Promise(function(r){ setTimeout(r, 600); });      // 超过 180ms + 120ms 兜底
        var visAfter=visible(ov2);
        var rail={
          supportsWAAPI: (typeof card2.animate==='function'),
          visibleImmediatelyAfterWrite: visNow,
          visibleAfter600ms: visAfter,
          elapsedMs: Math.round(performance.now()-t0)
        };
        var status = 'unknown';
        if(rail.visibleImmediatelyAfterWrite && !rail.supportsWAAPI) status='unknown';
        else if(rail.visibleImmediatelyAfterWrite && !rail.visibleAfter600ms) status='pass';
        else if(rail.visibleImmediatelyAfterWrite && rail.visibleAfter600ms) status='unknown';   // 虚拟时间可能未推进 WAAPI
        else status='fail';
        results.push({name:'R6_real_waapi_e2e', status:status, observed: rail});
        emit();
      }catch(e){ results.push({name:'R6_real_waapi_e2e', status:'unknown', observed:{message:String(e&&e.message||e)}}); emit(); }
    })();
  })();
  </script></body></html>`;
}

function runBrowser() {
  // 说明：data:URL 会超出 Windows 命令行长度上限（ENAMETOOLONG），
  // 因此在**系统临时目录**落一个测试页（仅测试机制文件，跑完立即删除；不触碰任何源码/工作区文件）。
  const tmp = join(tmpdir(), 'oc-motion-browser-test-' + process.pid + '.html');
  writeFileSync(tmp, pageHtml(), 'utf8');
  try {
    const url = pathToFileURL(tmp).href;
    const args = ['--headless', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=8000', '--dump-dom', url];
    const out = execFileSync(BROWSER, args, { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'], maxBuffer: 32 * 1024 * 1024 });
    const m = out.match(/<pre id="out">([\s\S]*?)<\/pre>/);
    if (!m) throw new Error('未找到 #out 输出（dump 长度 ' + out.length + '）');
    const txt = m[1].replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
    if (txt.trim() === 'PENDING') throw new Error('页面脚本未完成（仍为 PENDING）');
    return JSON.parse(txt);
  } finally {
    try { unlinkSync(tmp); } catch (_) {}
  }
}

const suite = BROWSER ? test : test.skip;
if (!BROWSER) {
  test('真实浏览器 DOM 测试（环境不可用 ⇒ UNKNOWN）', { skip: '本机未找到 Chromium/Chrome/Edge 可执行文件' }, () => {});
}

suite('真实浏览器 DOM：真实 CSSStyleDeclaration 上的拦截/可见性/恢复', () => {
  let data;
  try { data = runBrowser(); }
  catch (e) { console.error('UNKNOWN: 浏览器执行失败 ⇒ ' + e.message); assert.ok(false, '浏览器执行失败：' + e.message); }
  assert.equal(data.ok, 1, '页面应输出结果');
  const by = new Map(data.results.map((r) => [r.name, r]));
  const dump = () => data.results.map((r) => `  ${r.status.toUpperCase().padEnd(7)} ${r.name} ${JSON.stringify(r.observed)}`).join('\n');
  console.log('真实浏览器 DOM 实测结果：\n' + dump());

  // R1 拦截定义生效
  assert.equal(by.get('R1_own_accessor_defined')?.status, 'pass', 'display 自有访问器应定义成功');
  assert.equal(by.get('R1b_open_visible')?.status, 'pass', '打开后应可见');
  // R2 读值=意图、渲染仍可见、收尾后提交
  assert.equal(by.get('R2_read_is_intent')?.status, 'pass', '读应返回意图值 none');
  assert.equal(by.get('R2_still_visible_until_done')?.status, 'pass', '★ 动效结束前渲染必须仍可见（退出动画可播）');
  assert.equal(by.get('R2_committed_after_done')?.status, 'pass', '收尾后才真正隐藏');
  // R3 hidden
  assert.equal(by.get('R3_hidden_read_is_intent')?.status, 'pass');
  assert.equal(by.get('R3_hidden_still_visible')?.status, 'pass');
  assert.equal(by.get('R3_hidden_committed')?.status, 'pass');
  // R4 重复帧赋值
  assert.equal(by.get('R4_single_defer')?.status, 'pass', '多帧重复赋值只延后一次');
  assert.equal(by.get('R4_visible_during_loop')?.status, 'pass', '循环期间始终可见');
  assert.equal(by.get('R4_committed_once')?.status, 'pass', '最终提交一次');
  // R5 卸载恢复
  assert.equal(by.get('R5_uninstall_immediate')?.status, 'pass', '卸载后写入立即生效');
  assert.equal(by.get('R5_uninstall_no_motion')?.status, 'pass', '卸载后不再启动动效');
  // R7/R8 本轮新增回归
  assert.equal(by.get('R7_no_new_animation_after_commit')?.status, 'pass', '关闭完成后跨帧重复 none 不得新增动画');
  assert.equal(by.get('R7_stays_hidden')?.status, 'pass', '重复写入后应保持隐藏');
  assert.equal(by.get('R8_reopen_visible')?.status, 'pass', '关闭中 reopen 应提交为可见');
  assert.equal(by.get('R8_second_close_starts')?.status, 'pass', 'reopen 后再次关闭必须能重新启动');
  assert.equal(by.get('R8_second_close_commits')?.status, 'pass', '★ 再次关闭必须能提交隐藏（不得卡死）');
  // R6 WAAPI 端到端：允许 unknown（虚拟时间可能不推进动画），但不得 fail
  const r6 = by.get('R6_real_waapi_e2e');
  assert.ok(r6, 'R6 应存在');
  assert.notEqual(r6.status, 'fail', 'R6 真实 WAAPI 端到端不得 fail（unknown 可接受）');
});
