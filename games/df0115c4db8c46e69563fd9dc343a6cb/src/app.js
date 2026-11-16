/* 控制器负责生命周期和菜单，规则、绘制、输入各自独立。 */
(function(){
  'use strict';
  const spec=/* VISUAL_SPEC */null;
  const game=new TetrisRules.Game();
  let local;try{local=window.localStorage;}catch(e){local={getItem(){throw e;},setItem(){throw e;}};}
  const store=new TetrisStorage.BestStore(local),renderer=new TetrisRenderer(document.getElementById('board'),document.getElementById('next'),spec);
  const $=id=>document.getElementById(id);let loaded=false,error='',confirmRestart=false,last=0,previousPhase='ready',savedScore=-1,startBest=store.best;
  const input=new TetrisInput(game,action);
  // 只读快照用于诊断和验收，不提供注入棋盘/分数/结束状态的接口。
  Object.defineProperty(window,'tetrisSnapshot',{get:()=>({...game.snapshot(),bestScore:store.best,loaded,storageWarning:store.warning})});
  function action(a){
    if(!loaded||error||confirmRestart)return;
    if(a==='pause'){input.clear();if(game.phase==='paused')game.resume();else game.pause();}
    else if(a==='left')game.move(-1);else if(a==='right')game.move(1);else if(a==='rotate')game.rotate();else if(a==='hard'){input.clear();game.hardDrop();}
    update();
  }
  function start(){input.clear();confirmRestart=false;startBest=store.best;savedScore=-1;game.start();last=performance.now();update();}
  $('pause').onclick=()=>action('pause');
  $('restart').onclick=()=>{if(game.phase==='ready'||game.phase==='gameOver')return;game.pause();input.clear();confirmRestart=true;update();};
  $('cancel').onclick=()=>{confirmRestart=false;game.resume();last=performance.now();update();};
  $('primary').onclick=()=>{if(error){load();return;}if(!loaded)return;if(confirmRestart||game.phase==='ready'||game.phase==='gameOver')start();else if(game.phase==='paused'){input.clear();game.resume();last=performance.now();update();}};
  document.addEventListener('visibilitychange',()=>{if(document.hidden){game.pause();input.clear();update();}});
  window.addEventListener('blur',()=>{game.pause();input.clear();update();});
  function update(){
    if(game.score>store.best || (game.phase==='gameOver'&&savedScore!==game.score)){store.save(game.score);savedScore=game.score;}
    $('score').textContent=game.score;$('best').textContent=store.best;$('level').textContent=game.level;$('lines').textContent=game.totalLines;$('storage-warning').textContent=store.warning;
    const active=game.playable||game.phase==='clearing'||game.phase==='paused';$('pause').disabled=!active||confirmRestart;$('restart').disabled=!active;
    $('pause').textContent=game.phase==='paused'?'继续游戏':'暂停';
    $('animal').textContent=game.queue[0]?spec.tiles[game.queue[0]].animal:'动物伙伴待命';
    document.querySelectorAll('[data-action]').forEach(b=>b.disabled=!game.playable||confirmRestart);
    const visible=!loaded||!!error||confirmRestart||['ready','paused','gameOver'].includes(game.phase);$('overlay').hidden=!visible;$('cancel').hidden=!confirmRestart;
    if(error){$('overlay-title').textContent='资源加载失败';$('overlay-text').textContent='资源加载失败，请重试。'+error;$('primary').textContent='重新加载';$('primary').disabled=false;}
    else if(!loaded){$('overlay-title').textContent='萌兽正在赶来';$('overlay-text').textContent='正在准备动物方块…';$('primary').textContent='正在准备动物方块…';$('primary').disabled=true;}
    else{$('primary').disabled=false;if(confirmRestart){$('overlay-title').textContent='重新开始？';$('overlay-text').textContent='重新开始会清空本局进度。';$('primary').textContent='重新开始';}else if(game.phase==='paused'){$('overlay-title').textContent='游戏已暂停';$('overlay-text').textContent='星空会等你，准备好后继续。';$('primary').textContent='继续游戏';}else if(game.phase==='gameOver'){$('overlay-title').textContent='游戏结束';$('overlay-text').textContent='本局分数：'+game.score+(game.score>startBest?' · 刷新最高分！':' · 再挑战一次吧！');$('primary').textContent='再玩一局';}else{$('overlay-title').textContent='准备好了吗？';$('overlay-text').textContent='移动、旋转动物方块，填满一整行即可消除。堆到顶部时游戏结束。';$('primary').textContent='开始游戏';}}
    if(previousPhase!==game.phase){$('notice').textContent=game.phase==='clearing'?'消除 '+game.clearRows.length+' 行！':game.phase==='gameOver'?'游戏结束':game.phase==='paused'?'游戏已暂停':'';previousPhase=game.phase;}
  }
  async function load(){loaded=false;error='';update();try{await renderer.load();loaded=true;}catch(e){error=e.message;}update();}
  function frame(now){const dt=last?Math.min(100,Math.max(0,now-last)):0;last=now;const soft=input.tick(dt);if(loaded&&!error)game.tick(dt,soft);update();if(loaded&&!error)renderer.draw(game);requestAnimationFrame(frame);}
  load();requestAnimationFrame(frame);
})();
