import {createGame,roll,legalMoves,planMove,commitMove,skip,chooseAI,clone,NAMES} from './rules.js';
import {entropy} from './random.js';
import {movementSegments,duration,segmentAt,ROLL_MS} from './animation.js';
import {load,persist} from './storage.js';
import {loadAssets,AudioBank} from './assets.js';
import {Renderer} from './renderer.js';
const canvas=document.querySelector('#game'), screen=document.querySelector('#screen'),hud=document.querySelector('#hud'),warning=document.querySelector('#warning'),status=document.querySelector('#status');
const audio=new AudioBank();
let renderer,session=null,saved=null,overlay='loading',lastTime=0,saveTimer=0,loadGeneration=0,mode='classic',seats=['human','off','ai','off'],configError='',saveError='',loadError='',lastSegment=-1,lifecyclePaused=false;
const events=[];
const seedParam=new URLSearchParams(location.search).get('seed');
const fixedSeed=seedParam!==null&&/^\d+$/.test(seedParam)?Number(seedParam)>>>0:null;
let settings={sound:true,music:false};
try {settings={...settings,...JSON.parse(localStorage.getItem('ludo-settings')||'{}')};saved=load(localStorage);}catch(error){saveError='存档读取失败：'+error.message+'。可开始新局。';}
function event(kind,details={}) {events.push({...details,segmentKind:details.kind,kind,at:performance.now(),phase:session?.phase,id:session?.id,turn:session?.game.turn,elapsed:session?.elapsed});if(events.length>16000)events.shift();}
// 只读诊断快照；种子入口仅复现随机流，不允许注入局面、点数或胜利。
window.ludo={snapshot:()=>clone({session,overlay,seats,mode,events,assetsReady:!!renderer,saveError,hidden:document.hidden}),coordinates:()=>renderer?clone(renderer.hits):[]};
function writeSave() {
  if(!session)return;
  try {persist(localStorage,session);saveError='';saved=clone(session);} catch(error){saveError='存档写入失败，请勿关闭页面：'+error.message;}
  warning.textContent=saveError;
}
function button(label,id,handler,disabled=false) {
  const el=document.createElement('button');el.textContent=label;el.dataset.action=id;el.disabled=disabled;el.addEventListener('click',()=>{audio.unlock();audio.play('click.ogg');handler();});return el;
}
function addButton(label,id,handler,disabled=false) {const b=button(label,id,handler,disabled);b.className='wide';screen.append(b);return b;}
function text(tag,value) {const el=document.createElement(tag);el.textContent=value;screen.append(el);return el;}
function setOverlay(value) {overlay=value;lastTime=0;audio.pause();if(!value)audio.unlock();writeSave();event('覆盖层',{value});renderUI();}
function saveSettings() {audio.update(settings);try {localStorage.setItem('ludo-settings',JSON.stringify(settings));} catch {saveError='设置保存失败，当前声音设置仍生效。';warning.textContent=saveError;}}
function startGame() {
  try {
    const game=createGame(mode,seats,fixedSeed??entropy());
    session={schema:1,id:crypto.randomUUID(),game,phase:'ready',elapsed:0,wait:0,plan:null,segments:[]};
    overlay='';lastTime=0;lastSegment=-1;events.length=0;event('新局',{mode,seats:[...seats],seed:fixedSeed});writeSave();audio.pause();audio.unlock();renderUI();
  }catch(error){configError=error.message;renderUI();}
}
function continueGame() {session=clone(saved);mode=session.game.mode;seats=[...session.game.seats];overlay=session.phase==='result'?'result':'';lastTime=0;lastSegment=-1;event('恢复',{restored:session.phase,dice:session.game.dice});renderUI();audio.unlock();}
function phase(value) {session.phase=value;session.elapsed=0;session.wait=0;lastSegment=-1;event('阶段',{value});writeSave();renderUI();}
function doRoll() {
  if(overlay||!session||session.phase!=='ready')return;
  roll(session.game);phase('rolling');event('摇骰开始',{dice:session.game.dice});audio.play('roll.mp3');
}
function doMove(index) {
  if(overlay||session?.phase!=='choosing'||!legalMoves(session.game).includes(index))return;
  session.plan=planMove(session.game,index);session.segments=movementSegments(session.game,session.plan);phase('moving');event('走子开始',{plan:clone(session.plan),duration:duration(session.segments)});
}
function humanRoll() {if(session?.game.seats[session.game.current]==='human')doRoll();}
function humanMove(i) {if(session?.game.seats[session.game.current]==='human')doMove(i);}
function currentText() {
  if(!session)return '经典与快速 · 同屏 / 人机';
  const g=session.game,p=NAMES[g.current],controller=g.seats[g.current]==='ai'?'电脑':'玩家';
  const message={ready:`${p}方${controller}：${controller==='电脑'?'思考中…':'请掷骰'}`,rolling:`${p}方摇骰中…`,choosing:`${p}方掷出 ${g.dice}，请选择编号棋子`,moving:segmentAt(session.segments,session.elapsed)?.segment.kind==='return'?'吃子回营中…':'棋子移动中…',skip:'无可移动棋子',celebrating:`${NAMES[g.winner]}方获胜！`,result:`${NAMES[g.winner]}方获胜！`}[session.phase];
  return `${g.mode==='quick'?'快速':'经典'} · ${message}${g.mode==='quick'&&g.winner===null?` · ${g.unlocked[g.current]?'归家道已开':'吃子后开门'}`:''}`;
}
function renderHud() {
  hud.replaceChildren();if(!session)return;
  const top=document.createElement('div');top.className='bar top';
  top.append(button('菜单','menu',()=>setOverlay('menuConfirm')),button('重开','restart',()=>setOverlay('restartConfirm')),button('设置','settings',()=>setOverlay('settings')));hud.append(top);
  const bottom=document.createElement('div');bottom.className='bar bottom';
  if(session.phase==='choosing') {
    for(let i=0;i<4;i++)bottom.append(button(`棋子 ${i+1}`,`token-${i}`,()=>humanMove(i),!!overlay||session.game.seats[session.game.current]!=='human'||!legalMoves(session.game).includes(i)));
  } else bottom.append(button(session.phase==='ready'?'掷骰':session.phase==='rolling'?'摇骰中…':session.phase==='result'?'再来一局':'请等待…','roll',()=>session.phase==='result'?startGame():humanRoll(),!!overlay||!['ready','result'].includes(session.phase)||(session.phase==='ready'&&session.game.seats[session.game.current]!=='human')));
  hud.append(bottom);
}
function renderUI() {
  renderHud();screen.replaceChildren();screen.className=overlay?'open':'';status.textContent=currentText();warning.textContent=saveError;
  if(!overlay)return;
  if(overlay==='loading') {text('h1','LUDO');text('p',loadError||'正在加载原版素材…');if(loadError)addButton('重试加载','retry',initialize);return;}
  if(overlay==='menu') {
    text('h1','LUDO');text('p','经典骰子棋 · 原版美术');
    addButton('开始游戏','new',()=>{configError='';setOverlay('setup');});
    if(saved)addButton('继续存档','continue',continueGame);
    addButton('玩法说明','rules',()=>setOverlay('rules'));addButton('设置','settings',()=>setOverlay('settings'));text('small','本地同屏 / 电脑对手 · 无联网与广告');return;
  }
  if(overlay==='setup') {
    text('h2','选择对局');
    const row=document.createElement('div');row.className='row';row.append(button(mode==='classic'?'✓ 经典':'经典','mode-classic',()=>{mode='classic';renderUI();}),button(mode==='quick'?'✓ 快速':'快速','mode-quick',()=>{mode='quick';renderUI();}));screen.append(row);
    const countRow=document.createElement('div');countRow.className='row';
    for(const n of [2,3,4])countRow.append(button(`${n} 人`,`count-${n}`,()=>{seats=n===2?['human','off','ai','off']:n===3?['human','ai','ai','off']:['human','ai','ai','ai'];renderUI();}));screen.append(countRow);
    for(let p=0;p<4;p++) {
      const el=document.createElement('label');el.className='seat';const img=document.createElement('img');img.src=`./assets/avatar-${seats[p]==='ai'?'ai':'human'}.png`;img.alt='原版'+(seats[p]==='ai'?'电脑':'真人')+'形象';const label=document.createElement('span');label.textContent=`${NAMES[p]}方`;
      const select=document.createElement('select');select.dataset.seat=p;select.setAttribute('aria-label',`${NAMES[p]}方控制器`);
      for(const [value,name] of [['human','真人'],['ai','电脑'],['off','空席']]){const option=document.createElement('option');option.value=value;option.textContent=name;option.selected=seats[p]===value;select.append(option);}
      select.addEventListener('change',()=>{seats[p]=select.value;configError='';renderUI();});el.append(img,label,select);screen.append(el);
    }
    text('p',mode==='quick'?'两子在起点；先吃子开门，首子精确归家获胜。':'掷6出营；四子精确归家获胜。');
    if(configError)text('p',configError);
    addButton('开始对局','start',startGame,seats.filter(s=>s!=='off').length<2||!seats.includes('human'));addButton('返回','back',()=>setOverlay('menu'));return;
  }
  if(overlay==='settings') {
    text('h2','设置 · 对局已暂停');
    for(const [key,label] of [['sound','音效'],['music','背景音乐']]) {const el=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=settings[key];input.dataset.setting=key;input.addEventListener('change',()=>{settings[key]=input.checked;saveSettings();audio.pause();});el.append(input,document.createTextNode(' '+label));screen.append(el);}
    text('p','动画默认开启 · 摇骰833ms · 每格110ms');addButton('完成','close',()=>setOverlay(session?'':'menu'));return;
  }
  if(overlay==='rules') {
    text('h2','玩法说明');const el=text('p','掷6出营到本色起点；仅移动一枚棋子。起点和星格安全。非安全格只有一枚敌子时可以吃子，多子叠格不吃、不封路。6点、吃子或归家只奖励一次再掷；没有连续六点惩罚。终点必须精确到达，超点不可走。经典四子归家胜，快速先吃子永久开门、首子归家胜。首次胜利即结束。');el.className='rules';addButton('返回','back',()=>setOverlay('menu'));return;
  }
  if(overlay==='restartConfirm'||overlay==='menuConfirm') {
    text('h2',overlay==='restartConfirm'?'重新开始？':'返回菜单？');text('p',overlay==='restartConfirm'?'当前对局将被替换，旧动画会取消。':'当前对局已存档，可从菜单继续。');
    addButton('确定','confirm',()=>{if(overlay==='restartConfirm')startGame();else{writeSave();session=null;setOverlay('menu');}});addButton('取消','cancel',()=>setOverlay(''));return;
  }
  if(overlay==='result') {
    const p=session.game.winner;text('h2',`${NAMES[p]}方获胜！`);const img=document.createElement('img');img.className='winner-avatar';img.src=`./assets/avatar-${session.game.seats[p]==='ai'?'ai':'human'}.png`;img.alt='赢家原版形象';screen.append(img);text('p','首名结束 · 恭喜归家');addButton('再来一局','again',startGame);addButton('回菜单','result-menu',()=>{writeSave();session=null;setOverlay('menu');});
  }
}
function update(dt) {
  if(!session||overlay||document.hidden||lifecyclePaused)return;
  const s=session,g=s.game; s.elapsed+=dt;s.wait+=dt;
  if(s.phase==='ready'&&g.seats[g.current]==='ai'&&s.wait>=450)doRoll();
  else if(s.phase==='rolling'&&s.elapsed>=ROLL_MS) {event('摇骰结束',{dice:g.dice});phase(legalMoves(g).length?'choosing':'skip');}
  else if(s.phase==='skip'&&s.elapsed>=350) {skip(g);phase('ready');audio.play('turn.mp3');}
  else if(s.phase==='choosing'&&g.seats[g.current]==='ai'&&s.wait>=450)doMove(chooseAI(g));
  else if(s.phase==='moving') {
    const point=segmentAt(s.segments,s.elapsed),index=point?.index??s.segments.length;
    // 长帧仍逐项记录越过的落地，表现时钟按最大50ms推进。
    if(index!==lastSegment) {
      for(let i=lastSegment+1;i<=index;i++) {
        if(i>0)event('落地',{segment:i-1,kind:s.segments[i-1].kind,to:s.segments[i-1].to});
        if(i<s.segments.length) {const seg=s.segments[i];event('动画段',{index:i,kind:seg.kind,from:seg.from,to:seg.to,ms:seg.ms});if(seg.kind==='walk')audio.play('walk.mp3');if(seg.kind==='capture')audio.play('capture.mp3');if(seg.kind==='home')audio.play('home.mp3');}
      }
      lastSegment=index;
    }
    if(s.elapsed>=duration(s.segments)) {
      const plan=clone(s.plan);commitMove(g,s.plan);event('动作提交',{plan,last:clone(g.last),action:g.action});s.plan=null;s.segments=[];
      if(g.winner!==null){phase('celebrating');audio.play('win.mp3');}else{phase('ready');audio.play('turn.mp3');}
    }
  } else if(s.phase==='celebrating'&&s.elapsed>=1500) {phase('result');setOverlay('result');}
  saveTimer+=dt;if(saveTimer>=200){saveTimer=0;writeSave();}
}
function frame(now) {
  const dt=lastTime?Math.min(50,now-lastTime):0;lastTime=now;
  update(dt);if(renderer)renderer.draw(session,now);status.textContent=currentText();requestAnimationFrame(frame);
}
let pointer=null;
canvas.addEventListener('pointerdown',e=>{if(!e.isPrimary)return;pointer=e.pointerId;canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointercancel',()=>{pointer=null;});
canvas.addEventListener('pointerup',e=>{
  if(e.pointerId!==pointer)return;pointer=null;
  if(overlay||!renderer||!session)return;
  const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)*720/r.width,y=(e.clientY-r.top)*1280/r.height;
  audio.unlock();
  if(session.phase==='ready') {
    const [a,b]=renderer.infoPoint(session.game.current);
    if(Math.abs(x-(a+88))<65&&Math.abs(y-b)<65)humanRoll();
  } else if(session.phase==='choosing') {
    const hits=renderer.hits.filter(h=>Math.hypot(h.x-x,h.y-y)<34);
    if(hits.length===1)humanMove(hits[0].i);
    else if(hits.length>1){status.textContent='棋子重叠，请用下方编号选择';}
  }
});
window.addEventListener('resize',()=>renderer?.resize());
function suspend(reason) {lifecyclePaused=true;lastTime=0;writeSave();audio.pause();event('后台暂停',{reason});}
function resume(reason) {lifecyclePaused=false;lastTime=0;event('前台恢复',{reason});if(!overlay&&!document.hidden)audio.unlock();}
document.addEventListener('visibilitychange',()=>document.hidden?suspend('visibilitychange'):resume('visibilitychange'));
// Chromium冻结事件与可见性事件共用恢复路径，避免长后台时钟跳完动画。
document.addEventListener('freeze',()=>suspend('freeze'));
document.addEventListener('resume',()=>resume('resume'));
window.addEventListener('pagehide',()=>{writeSave();audio.pause();});
async function initialize() {
  const generation=++loadGeneration;overlay='loading';loadError='';renderUI();
  try {
    const assets=await loadAssets((done,total)=>{if(generation===loadGeneration&&overlay==='loading')status.textContent=`素材 ${done}/${total}`;});
    if(generation!==loadGeneration)return;
    renderer=new Renderer(canvas,assets);overlay='menu';renderUI();audio.settings=settings;event('素材完成');
  }catch(error){if(generation!==loadGeneration)return;loadError=error.message;renderUI();}
}
initialize();requestAnimationFrame(frame);
