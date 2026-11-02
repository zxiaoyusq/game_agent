import { bootEngine } from './engine-bootstrap.mjs';
import { cloneBoard, applyMove, isComplete } from './rules.mjs';
import { freshSave, normalizeSave } from './storage.mjs';

// 本地研究版直接加载已提取的参考材质；所有场景、按钮、文字与动画均由 Cocos 渲染。
const cc = await bootEngine();
const [levels, assetMap] = await Promise.all([
  fetch('./assets/levels.json').then(response => response.json()),
  fetch('./assets/asset-map.json').then(response => response.json()),
]);
const { Node, Scene, Camera, Canvas, Graphics, Label, UITransform, Sprite, SpriteFrame, Texture2D, ImageAsset, Color, Vec3, Layers, tween } = cc;
const WIDTH = 540, HEIGHT = 960;
const COLORS = ['#f45d70','#62c6ff','#ffc75b','#8be29a','#b993ff','#ff9e5c','#65e0d5','#ea95c8','#b3c754','#7b97eb','#f5e9bb','#c5987b'];
const THEMES = [
  { name:'暮色海湾', bg:'#101c31', card:'#1b2d46', edge:'#35546e', text:'#edf5f9', muted:'#92a8bf', accent:'#82dfce', balls:'guru' },
  { name:'清晨雾岛', bg:'#e4ecec', card:'#f7fbf8', edge:'#c3d6d5', text:'#254951', muted:'#688c92', accent:'#2c9c8d', balls:'infinite' },
  { name:'极光花园', bg:'#231e3a', card:'#342b4b', edge:'#5c4c75', text:'#fbf0ff', muted:'#b5a1c6', accent:'#f0c575', balls:'guru' },
];
const STORAGE = 'ball-sort-atelier:v1';
let stored;let storageRecovered=false;
let storageUnsaved=false, feedback='';
let sessionRevision=0, viewRevision=0, settlementTimer=null;
try { const text=localStorage.getItem(STORAGE); stored=text?JSON.parse(text):freshSave(); } catch { stored=freshSave();storageRecovered=true; }
const normalized=normalizeSave(stored,levels);
let save=normalized.save;storageRecovered ||= normalized.recovered;
let mode = levels[save.mode] ? save.mode : 'classic';
let index = save.indices[mode], board, history=[], historyBoundary=null, selected=-1, moves=0, busy=false, won=false, extra=false;
let gameLayer, boardLayer, overlay, hud, messageNode, tubePositions=[], ballNodes=[], hintPair=null, hintRequest=0, lastHint=null, lastHintSource=null;
const textures = {};
const sounds = {};
const solver = new Worker(new URL('./solver-worker.mjs', import.meta.url), { type:'module' });
const current = () => levels[mode][index];
const theme = () => THEMES[save.theme];
const color = (hex, alpha=255) => { const value=new Color();Color.fromHEX(value,hex);value.a=alpha;return value; };
function persist() {
  save.mode=mode; save.indices[mode]=index;
  save.session={mode,index,board,history,historyBoundary,moves,extra,won};
  try { localStorage.setItem(STORAGE,JSON.stringify(save)); storageUnsaved=false; } catch { storageUnsaved=true; }
  renderFeedback();
}
function node(name,parent,x=0,y=0,w=1,h=1) {
  const value = new Node(name); value.layer=Layers.Enum.UI_2D; value.setPosition(x,y);
  value.addComponent(UITransform).setContentSize(w,h); parent.addChild(value);return value;
}
function shape(parent,x,y,w,h,fill,radius=18,stroke=null) {
  const value=node('界面形状',parent,x,y,w,h); const graphics=value.addComponent(Graphics);
  graphics.fillColor=color(fill);graphics.roundRect(-w/2,-h/2,w,h,radius);graphics.fill();
  if(stroke){graphics.strokeColor=color(stroke);graphics.lineWidth=1.4;graphics.roundRect(-w/2,-h/2,w,h,radius);graphics.stroke();}
  return value;
}
function text(parent,value,x,y,size=20,tint=theme().text,width=480) {
  const valueNode=node('文字',parent,x,y,width,size*1.6);const label=valueNode.addComponent(Label);
  label.string=value; label.fontSize=size; label.lineHeight=size*1.4;label.fontFamily='Arial, "Noto Sans CJK SC", sans-serif';
  label.color=color(tint);label.horizontalAlign=Label.HorizontalAlign.CENTER;label.verticalAlign=Label.VerticalAlign.CENTER;
  return valueNode;
}
function cssScale(){const rect=cc.game.canvas.getBoundingClientRect();return Math.min(rect.width/WIDTH,rect.height/HEIGHT);}
function resizeTargets(){
  const minimum=44/cssScale();
  function visit(parent){for(const child of parent.children){if(child.buttonSize){const [w,h]=child.buttonSize;child.getComponent(UITransform).setContentSize(Math.max(w,minimum),Math.max(h,minimum));}visit(child);}}
  visit(canvas);
}
function button(parent,title,x,y,w,h,action,{fill=theme().card,tint=theme().text,size=18,stroke=theme().edge}={}) {
  const value=shape(parent,x,y,w,h,fill,Math.min(16,h/2),stroke);text(value,title,0,0,size,tint,w-8);
  value.name=`按钮:${title}`;value.buttonSize=[w,h];
  const minimum=44/cssScale();value.getComponent(UITransform).setContentSize(Math.max(w,minimum),Math.max(h,minimum));
  value.on(Node.EventType.TOUCH_END,()=>{if(!busy){play('tap');action();}});
  return value;
}
function clear(parent){for(const child of [...parent.children]){child.removeFromParent();child.destroy();}}
function play(name) { if(save.sound && sounds[name]) { try { sounds[name].playOneShot(sounds[name].clip, name==='complete'?.45:.35); } catch {} } }
async function loadSprite(url) {
  const image=await new Promise((resolve,reject)=>{const value=new Image();value.onload=()=>resolve(value);value.onerror=reject;value.src=url;});
  const texture=new Texture2D();texture.image=new ImageAsset(image);const frame=new SpriteFrame();frame.texture=texture;return frame;
}
async function loadAssets() {
  await Promise.all(Object.values(assetMap).flat().map(async url=>{textures[url]=await loadSprite(`./${url}`);}));
  await Promise.all(['tap','move','complete'].map(key=>new Promise(resolve=>cc.assetManager.loadRemote(`./assets/${key}.wav`,{ext:'.wav'},(error,clip)=>{
    if(!error){const audio=node('音效',scene).addComponent(cc.AudioSource);audio.clip=clip;sounds[key]=audio;}resolve();
  }))));
}
const scene=new Scene('彩球工坊');
const cameraNode=node('界面相机',scene,0,0);cameraNode.setPosition(0,0,1000);
const camera=cameraNode.addComponent(Camera);camera.projection=Camera.ProjectionType.ORTHO;camera.orthoHeight=HEIGHT/2;camera.near=.1;camera.far=2000;camera.visibility=Layers.Enum.UI_2D;camera.clearFlags=Camera.ClearFlag.SOLID_COLOR;
const canvas=node('画布',scene,0,0,WIDTH,HEIGHT);const canvasComponent=canvas.addComponent(Canvas);canvasComponent.cameraComponent=camera;
cc.view.setDesignResolutionSize(WIDTH,HEIGHT,cc.ResolutionPolicy.SHOW_ALL);cc.view.resizeWithBrowserSize(true);
cc.director.runSceneImmediate(scene);
await loadAssets();

function drawBackground() {
  camera.clearColor=color(theme().bg);gameLayer=node('游戏界面',canvas,0,0,WIDTH,HEIGHT);
  shape(gameLayer,0,0,WIDTH,HEIGHT,theme().bg,0);
  const decoration=node('背景柔光',gameLayer);const graphics=decoration.addComponent(Graphics);
  graphics.fillColor=color(theme().accent,9);graphics.circle(230,300,200);graphics.fill();graphics.circle(-220,-230,170);graphics.fill();
  // 原生 Cocos Graphics 绘制低细节装饰，保持球体和管口的对比度。
  for(let i=0;i<20;i++){graphics.fillColor=color(theme().accent,18);graphics.circle(-246+(i*73)%490,-400+(i*137)%800,1.1);graphics.fill();}
  text(gameLayer,'BALL SORT  /  ATELIER',0,434,13,theme().accent);
  button(gameLayer,'☰',-226,390,48,46,showModes,{size:22});
  text(gameLayer,'彩球工坊',0,392,30);
  button(gameLayer,'⚙',226,390,48,46,showSettings,{size:24});
  hud=node('状态栏',gameLayer,0,0,WIDTH,HEIGHT);
  boardLayer=node('试管区域',gameLayer,0,0,WIDTH,HEIGHT);
  const toolbarY=-322;
  button(gameLayer,'↶\n撤销',-186,toolbarY,82,78,undo,{size:19});
  button(gameLayer,'↻\n重开',-62,toolbarY,82,78,confirmRestart,{size:19});
  button(gameLayer,'✦\n提示',62,toolbarY,82,78,requestHint,{size:19});
  button(gameLayer,'＋\n加管',186,toolbarY,82,78,addTube,{size:19});
  button(gameLayer,'经典旅程',-165,-405,150,49,()=>changeMode('classic'),{fill:mode==='classic'?theme().accent:theme().card,tint:mode==='classic'?theme().bg:theme().muted,size:16});
  button(gameLayer,'长管挑战',0,-405,150,49,()=>changeMode('challenge'),{fill:mode==='challenge'?theme().accent:theme().card,tint:mode==='challenge'?theme().bg:theme().muted,size:16});
  button(gameLayer,'迷雾实验',165,-405,150,49,()=>changeMode('mystery'),{fill:mode==='mystery'?theme().accent:theme().card,tint:mode==='mystery'?theme().bg:theme().muted,size:16});
  text(gameLayer,'整理颜色，也整理此刻的心情',0,-458,12,theme().muted);
  messageNode=text(gameLayer,'',0,-262,16,theme().accent);
}
function updateHud() {
  clear(hud);
  const completed=Object.keys(save.completed).length;
  button(hud,`${current().label}  ·  第 ${index+1} 关  ⌄`,0,320,300,46,showLevels,{fill:theme().bg,stroke:theme().bg,size:18,tint:theme().accent});
  text(hud,`步数  ${moves}     ·     已整理  ${board.filter(tube=>tube.length===current().capacity&&new Set(tube).size===1).length} / ${new Set(board.flat()).size}`,0,276,15,theme().muted);
  text(hud,`✧ ${completed} 颗星`,207,434,12,theme().muted,100);
  shape(hud,0,245,450,1,theme().edge,0);
}
function layoutTubes() {
  const count=board.length, rows=count<=6?1:2;
  const perRow=rows===1?count:Math.ceil(count/2);
  const size=rows===1?43:(current().capacity>=6?204/current().capacity:43);
  const height=current().capacity*size+27;
  const width=Math.min(size+7,(460/perRow)-18);
  tubePositions=[];
  for(let i=0;i<count;i++){
    const row=Math.floor(i/perRow), rowCount=Math.min(perRow,count-row*perRow);
    const spacing=Math.min(98,460/rowCount);
    const x=(i%perRow-(rowCount-1)/2)*spacing;
    const y=rows===1?7:(row===0?120:-118);
    tubePositions.push({x,y,width,height,size,bottom:y-height/2+size/2+10});
  }
}
function ball(parent,colorIndex,x,y,size,{hidden=false,symbols=save.symbols}={}) {
  const ballNode=node('彩球',parent,x,y,size,size);
  const frame=textures[assetMap[theme().balls]?.[(colorIndex-1)%assetMap[theme().balls].length]];
  if(frame&&!hidden){const sprite=ballNode.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.spriteFrame=frame;ballNode.getComponent(UITransform).setContentSize(size,size);}
  else { const graphics=ballNode.addComponent(Graphics);graphics.fillColor=color(hidden?'#687a91':COLORS[(colorIndex-1)%COLORS.length]);graphics.circle(0,0,size/2-1);graphics.fill();graphics.fillColor=color('#ffffff',110);graphics.ellipse(-size*.18,size*.22,size*.12,size*.06);graphics.fill(); }
  if(hidden)text(ballNode,'?',0,0,size*.47,'#e3edf7',size);
  else if(symbols) { const badge=shape(ballNode,0,-1,size*.47,size*.48,'#132a43',8);text(badge,String(colorIndex),0,0,size*.33,'#ffffff',size); }
  return ballNode;
}
function renderBoard(displayBoard=board) {
  clear(boardLayer);layoutTubes();ballNodes=[];
  displayBoard.forEach((tube,index)=>{
    const p=tubePositions[index];const tubeNode=node(`试管${index+1}`,boardLayer,p.x,p.y,Math.min(460/Math.ceil(board.length/(board.length<=6?1:2)),p.width+36),p.height+40);
    const graphics=tubeNode.addComponent(Graphics);
    const isDone=tube.length===current().capacity&&new Set(tube).size===1;
    graphics.fillColor=color('#000000',28);graphics.ellipse(0,-p.height/2-5,p.width*.55,7);graphics.fill();
    graphics.fillColor=color(theme().card,110);graphics.roundRect(-p.width/2,-p.height/2,p.width,p.height,14);graphics.fill();
    graphics.strokeColor=color(isDone?theme().accent:(selected===index?'#ffd68b':theme().edge));graphics.lineWidth=selected===index?3:2;
    graphics.moveTo(-p.width/2,p.height/2);graphics.lineTo(-p.width/2,-p.height/2+15);graphics.quadraticCurveTo(-p.width/2,-p.height/2,0,-p.height/2);graphics.quadraticCurveTo(p.width/2,-p.height/2,p.width/2,-p.height/2+15);graphics.lineTo(p.width/2,p.height/2);graphics.stroke();
    graphics.strokeColor=color('#ffffff',90);graphics.lineWidth=2;graphics.moveTo(-p.width/2+5,-p.height/2+20);graphics.lineTo(-p.width/2+5,p.height/2-8);graphics.stroke();
    graphics.strokeColor=color(selected===index?'#ffd68b':'#adc5d9',140);graphics.lineWidth=3;graphics.moveTo(-p.width/2-3,p.height/2);graphics.lineTo(p.width/2+3,p.height/2);graphics.stroke();
    // HM 的原始玻璃管贴图叠加于几何轮廓，帮助统一三套参考素材的质感。
    const glass=textures[assetMap.hm[0]];
    if(glass){const glassNode=node('玻璃高光',tubeNode,0,0,p.width+3,p.height+5);const sprite=glassNode.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.spriteFrame=glass;glassNode.getComponent(UITransform).setContentSize(p.width+3,p.height+5);sprite.color=color('#ffffff',70);}
    ballNodes[index]=[];
    tube.forEach((c,j)=>{
      const hidden=current().hidden&&j<tube.length-1;
      const y=p.bottom+j*p.size-p.y+(selected===index&&j===tube.length-1?18:0);
      ballNodes[index].push(ball(tubeNode,c,0,y,p.size-3,{hidden}));
    });
    if(!tube.length)text(tubeNode,'·',0,0,24,theme().edge,p.width);
    if(isDone)text(tubeNode,'✓',0,p.height/2+20,17,theme().accent,p.width);
    if(hintPair?.includes(index))text(tubeNode,index===hintPair[0]?'↑':'↓',0,p.height/2+39,26,'#ffd68b',p.width);
    text(tubeNode,String(index+1),0,-p.height/2-13,12,theme().muted,p.width);
    tubeNode.on(Node.EventType.TOUCH_END,()=>chooseTube(index));
  });
  updateHud();
}
function renderFeedback() { if(messageNode)messageNode.getComponent(Label).string=storageUnsaved?'本次进度暂未保存，当前局面仍可继续':feedback; }
function notify(value) { feedback=value;renderFeedback(); }
function cancelSettlement(){clearTimeout(settlementTimer);settlementTimer=null;viewRevision++;}
function redrawLevel(){
  cancelSettlement();
  if(gameLayer)gameLayer.destroy();closeOverlay();
  drawBackground();renderBoard();renderFeedback();
}
function startLevel(restore=null) {
  sessionRevision++;cancelSettlement();
  selected=-1;hintPair=null;hintRequest++;won=false;busy=false;extra=false;moves=0;history=[];historyBoundary=null;board=cloneBoard(current().board);
  if(restore){board=cloneBoard(restore.board);history=restore.history||[];historyBoundary=restore.historyBoundary?{board:cloneBoard(restore.historyBoundary.board),moves:restore.historyBoundary.moves,extra:restore.historyBoundary.extra}:null;moves=restore.moves||0;extra=!!restore.extra;won=!!restore.won;}
  if(gameLayer)gameLayer.destroy(); if(overlay){overlay.destroy();overlay=null;}
  drawBackground();renderBoard();
  notify(current().hidden?'管口下方藏着未知颜色，移开便能揭晓':'先点选试管，再点同色管口或空管');persist();
  if(won)completeLevel();
}
function chooseTube(target) {
  if(busy||won||overlay)return;
  play('tap');
  if(selected<0){if(board[target].length){selected=target;renderBoard();notify('点同色管口或空管，把颜色聚在一起');}return;}
  if(selected===target){selected=-1;renderBoard();return;}
  const from=selected;const result=applyMove(board,from,target,current().capacity);
  if(!result){selected=board[target].length?target:-1;renderBoard();notify('只能放到空管，或同色且未满的管口');const p=ballNodes[target]?.at(-1);if(p)tween(p).by(.05,{position:new Vec3(4,0,0)}).by(.1,{position:new Vec3(-8,0,0)}).by(.05,{position:new Vec3(4,0,0)}).start();return;}
  animateMove(from,target,result);
}
// 丢弃最早事务时同步保存新边界；撤销至空历史仍保留该边界。
function rememberSnapshot(){
  history.push({board:cloneBoard(board),moves,extra});
  if(history.length>500){history.shift();const first=history[0];historyBoundary={board:cloneBoard(first.board),moves:first.moves,extra:first.extra};}
}
function animateMove(from,to,result) {
  busy=true;selected=-1;hintPair=null;hintRequest++;rememberSnapshot();
  const source=tubePositions[from], destination=tubePositions[to];const sourceCount=board[from].length,destinationCount=board[to].length;
  const colorIndex=result.color;
  // 移除源管球后，以独立 Cocos 节点依次抛起、横移、落入目标管，锁定输入防止重入。
  const interim=cloneBoard(board);interim[from].splice(-result.count);
  // 完整逻辑局面先提交并保存，动画只展示快照；中途刷新也不会回退或丢失球。
  board=result.board;moves++;
  const firstWin=isComplete(board,current().capacity)?recordCompletion():false;
  persist();renderBoard(interim);
  const duration=save.fast?.075:.14;
  let landed=0;
  for(let i=0;i<result.count;i++){
    const flying=ball(gameLayer,colorIndex,source.x,source.bottom+(sourceCount-1-i)*source.size,source.size-3,{hidden:false});
    const apex=Math.min(245,Math.max(source.y+source.height/2,destination.y+destination.height/2)+42);
    const endY=destination.bottom+(destinationCount+i)*destination.size;
    tween(flying).delay(i*.075).to(duration,{position:new Vec3(source.x,apex,0)},{easing:'quadOut'}).to(duration*1.25,{position:new Vec3(destination.x,apex+10,0)},{easing:'sineInOut'}).to(duration,{position:new Vec3(destination.x,endY,0)},{easing:'quadIn'}).call(()=>{
      flying.destroy();play('move');landed++;
      if(landed===result.count){busy=false;renderBoard();persist();
        if(isComplete(board,current().capacity))completeLevel(firstWin);else notify('很好，继续给每种颜色找到自己的位置');}
    }).start();
  }
}
function undo() {
  if(!history.length){notify('还没有可撤销的操作');return;}
  hintRequest++;const previous=history.pop();board=cloneBoard(previous.board);moves=previous.moves;extra=previous.extra;selected=-1;won=false;hintPair=null;renderBoard();persist();notify('已撤销一步，试试另一种整理方式');
}
function confirmRestart(){showDialog('重新整理这一关？','当前关卡的步数与操作会重新开始。',[['继续当前关卡',closeOverlay],['重新开始',()=>{closeOverlay();startLevel();}]]);}
function addTube() {
  if(won)return;
  if(extra){notify('本关已经添加了一支辅助管');return;}
  hintRequest++;hintPair=null;rememberSnapshot();board.push([]);extra=true;selected=-1;renderBoard();persist();notify('多一支空管，多一点思考空间');
}
function requestHint() {
  if(won)return;
  const known=findKnownHint();
  if(known){showHint(known,'预置解法');return;}
  notify('正在思考可完成的路线…');const id=++hintRequest;solver.postMessage({id,board:cloneBoard(board),capacity:current().capacity});
}
function findKnownHint() {
  let state=cloneBoard(current().board);
  const key=JSON.stringify(board.slice(0,current().board.length));
  for(const step of current().solution){if(JSON.stringify(state)===key)return step;state=applyMove(state,...step,current().capacity).board;}return null;
}
function showHint(pair,source='离线求解'){lastHint=[...pair];lastHintSource=source;hintPair=pair;selected=-1;renderBoard();notify(`试试把 ${pair[0]+1} 号管的球移到 ${pair[1]+1} 号管`);}
solver.onmessage=({data})=>{if(data.id!==hintRequest||overlay||won)return;if(data.solution?.length)showHint(data.solution[0]);else notify(history.length?'这里有些绕，撤销几步或添加辅助管再试试':'可以添加一支辅助管，给颜色腾出空间');};
function recordCompletion(){const first=!save.completed[current().id];save.completed[current().id]={moves,best:Math.min(moves,save.completed[current().id]?.best??Infinity)};return first;}
function completeLevel(first=recordCompletion()) {
  won=true;play('complete');persist();
  // 星屑只使用 Cocos Graphics 与 Tween，不引入额外粒子依赖。
  for(let i=0;i<28;i++){const spark=shape(gameLayer,-200+Math.random()*400,150+Math.random()*80,5+Math.random()*5,5+Math.random()*5,COLORS[i%12],2);tween(spark).delay(Math.random()*.15).to(.9,{position:new Vec3(spark.position.x+(Math.random()-.5)*130,spark.position.y-280,0),scale:new Vec3(.05,.05,1)},{easing:'quadIn'}).call(()=>spark.destroy()).start();}
  cancelSettlement();const session=sessionRevision,view=viewRevision;
  settlementTimer=setTimeout(()=>{settlementTimer=null;if(!won||session!==sessionRevision||view!==viewRevision||overlay)return;showDialog('每一种颜色，都有归处',`第 ${index+1} 关完成 · ${moves} 步\n${first?'获得一颗整理之星 ✧':'再一次找到了秩序 ✧'}`,[[index+1<levels[mode].length?'下一关':'从第一关再出发',()=>{closeOverlay();index=(index+1)%levels[mode].length;startLevel();}],['看看我的旅程',showLevels]]);},650);
}
function closeOverlay(){cancelSettlement();if(overlay){overlay.destroy();overlay=null;}}
function modal(title,subtitle='',height=520){
  closeOverlay();overlay=node('弹窗',canvas,0,0,WIDTH,HEIGHT);
  const veil=shape(overlay,0,0,WIDTH,HEIGHT,'#080f1d',0);veil.addComponent(cc.UIOpacity).opacity=220;
  veil.on(Node.EventType.TOUCH_END,()=>{});
  const panel=shape(overlay,0,0,484,height,theme().card,26,theme().edge);
  text(panel,title,0,height/2-55,26);
  if(subtitle)text(panel,subtitle,0,height/2-105,15,theme().muted,430);
  button(panel,'×',200,height/2-36,38,38,closeOverlay,{fill:theme().card,stroke:theme().card,size:26,tint:theme().muted});return panel;
}
function showDialog(title,subtitle,actions){const panel=modal(title,subtitle,380);actions.forEach(([label,action],i)=>button(panel,label,0,-20-i*69,390,51,action,{fill:i===0?theme().accent:theme().card,tint:i===0?theme().bg:theme().text}));}
function requestLevel(nextMode,nextIndex){
  const commit=()=>{mode=nextMode;index=nextIndex;closeOverlay();startLevel();};
  if(!won&&(moves>0||extra||history.length)){showDialog('离开当前关卡？','切换后将重新开始所选关卡，当前尝试不会保留。',[['继续当前关卡',closeOverlay],['确认切换',commit]]);return;}
  commit();
}
function changeMode(nextMode){if(mode===nextMode){closeOverlay();return;}requestLevel(nextMode,save.indices[nextMode]||0);}
function showModes(){const panel=modal('给今天一点新鲜感','三个房间，三种整理心情',510);[['classic','经典旅程','100 关 · 从三色到缤纷世界'],['challenge','长管挑战','12 关 · 6 / 8 层玻璃管的策略空间'],['mystery','迷雾实验','20 关 · 移开表层，揭开未知颜色']].forEach(([key,title,desc],i)=>{button(panel,title,0,65-i*105,410,56,()=>changeMode(key),{fill:key===mode?theme().accent:theme().bg,tint:key===mode?theme().bg:theme().text});text(panel,desc,0,25-i*105,13,theme().muted);});}
function showLevels(page=Math.floor(index/20)) {
  const pages=Math.ceil(levels[mode].length/20);page=Math.max(0,Math.min(page,pages-1));
  const panel=modal('我的整理旅程',`${current().label} · 已完成 ${levels[mode].filter(level=>save.completed[level.id]).length} / ${levels[mode].length}`,590);
  for(let i=0;i<20;i++){const n=page*20+i;if(n>=levels[mode].length)break;const done=!!save.completed[levels[mode][n].id];button(panel,`${done?'✧ ':''}${n+1}`,-170+(i%5)*85,120-Math.floor(i/5)*78,70,58,()=>requestLevel(mode,n),{fill:n===index?theme().accent:theme().bg,tint:n===index?theme().bg:done?theme().accent:theme().text,size:17});}
  button(panel,'←',-100,-220,65,42,()=>showLevels(page-1));text(panel,`${page+1} / ${pages}`,0,-220,15,theme().muted,80);button(panel,'→',100,-220,65,42,()=>showLevels(page+1));
}
function showSettings(){
  const panel=modal('让工坊更适合你','主题会随整理之星逐步点亮',650);const completed=Object.keys(save.completed).length;
  THEMES.forEach((item,i)=>{const unlocked=i===0||completed>=i*3;button(panel,`${save.theme===i?'●':'○'} ${item.name} ${unlocked?'':`· ${i*3} 星解锁`}`,0,130-i*72,400,50,()=>{if(!unlocked){text(panel,`完成 ${i*3} 关即可解锁${item.name}`,0,-310,13,theme().accent);return;}save.theme=i;persist();redrawLevel();showSettings();},{fill:save.theme===i?theme().accent:theme().bg,tint:save.theme===i?theme().bg:theme().text,size:17});});
  [['sound','声音反馈'],['symbols','颜色数字辅助'],['fast','快速动画']].forEach(([key,label],i)=>button(panel,`${label}  ${save[key]?'开':'关'}`,0,-90-i*72,400,44,()=>{save[key]=!save[key];persist();renderBoard();showSettings();},{fill:theme().bg,size:16}));
  text(panel,storageUnsaved?'本次进度暂未保存，当前局面仍可继续':'进度自动保存在当前浏览器',0,-296,12,storageUnsaved?theme().accent:theme().muted);
}
// 仅暴露可观察状态与与界面相同的操作，供自动化验收；不提供跳过通关的入口。
window.ballSortGame={
  engine:'Cocos Engine 3.8.8',
  getEngineInfo:()=>({version:cc.VERSION,scene:cc.director.getScene()?.name,canvas:cc.game.canvas===document.getElementById('GameCanvas'),graphicsApi:cc.gfx.API[cc.director.root.device.gfxAPI],drawCalls:cc.director.root.device.numDrawCalls}),
  getState:()=>({mode,index,board:cloneBoard(board),moves,selected,busy,won,extra,theme:save.theme,symbols:save.symbols,storageRecovered,message:messageNode?.getComponent(Label)?.string,hintPair,lastHint,lastHintSource,overlay:!!overlay,capacity:current().capacity,solution:current().solution,tubePositions,completed:Object.keys(save.completed).length}),
  chooseTube,undo,requestHint,addTube,changeMode,closeOverlay,
};
startLevel(save.session);if(storageRecovered)notify('已修复异常存档，保留有效进度并恢复可玩的关卡');
window.addEventListener('resize',()=>requestAnimationFrame(()=>requestAnimationFrame(resizeTargets)));
cc.view.on('canvas-resize',resizeTargets);
resizeTargets();
document.getElementById('loading').remove();
console.log('彩球工坊已启动：Cocos 3.8.8，132 个已验证关卡');
