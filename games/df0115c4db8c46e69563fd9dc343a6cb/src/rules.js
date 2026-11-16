/* 规则层只维护数据，不访问DOM；浏览器普通脚本与Node单测共用。 */
(function(root) {
  'use strict';
  const TYPES = ['I','O','T','J','L','S','Z'];
  const SHAPES = {
    I: ['....','IIII','....','....'], O: ['.OO.','.OO.','....','....'],
    T: ['.T.','TTT','...'], J: ['J..','JJJ','...'], L: ['..L','LLL','...'],
    S: ['.SS','SS.','...'], Z: ['ZZ.','.ZZ','...']
  };
  const KICKS = [ [[0,0],[-1,0],[-1,-1],[0,2],[-1,2]], [[0,0],[1,0],[1,1],[0,-2],[1,-2]], [[0,0],[1,0],[1,-1],[0,2],[1,2]], [[0,0],[-1,0],[-1,1],[0,-2],[-1,-2]] ];
  const IKICKS = [ [[0,0],[-2,0],[1,0],[-2,1],[1,-2]], [[0,0],[-1,0],[2,0],[-1,-2],[2,1]], [[0,0],[2,0],[-1,0],[2,-1],[-1,2]], [[0,0],[1,0],[-2,0],[1,2],[-2,-1]] ];
  function seeded(seed) { let n = seed >>> 0; return () => { n += 0x6d2b79f5; let t = Math.imul(n ^ n >>> 15, 1 | n); t ^= t + Math.imul(t ^ t >>> 7, 61 | t); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function cells(p) {
    let matrix = SHAPES[p.type].map(s => [...s]);
    if (p.type !== 'O') for (let r = 0; r < p.rotation; r++) matrix = matrix[0].map((_, x) => matrix.map(row => row[x]).reverse());
    const result = [];
    matrix.forEach((row,y) => row.forEach((v,x) => { if (v !== '.') result.push([x+p.x,y+p.y]); }));
    return result;
  }
  class Game {
    constructor(random = Math.random) { this.random = random; this.sessionId = 0; this.phase = 'ready'; this.board = Array.from({length:22}, () => Array(10).fill(null)); this.score = 0; this.totalLines = 0; this.level = 1; this.queue = []; this.active = null; this.pieceId = 0; this.clearRows = []; this.clearRemaining = 0; }
    get gravityInterval() { return Math.max(100, Math.round(1000 * Math.pow(0.8,this.level-1))); }
    get playable() { return this.phase === 'falling' || this.phase === 'grounded'; }
    fillQueue() {
      while (this.queue.length < 2) {
        const bag = TYPES.slice();
        for (let i=6;i>0;i--) { const j = Math.floor(this.random()*(i+1)); [bag[i],bag[j]] = [bag[j],bag[i]]; }
        this.queue.push(...bag);
      }
    }
    start() {
      this.sessionId++; this.board = Array.from({length:22},()=>Array(10).fill(null));
      this.score=0; this.totalLines=0; this.level=1; this.queue=[]; this.clearRows=[]; this.clearRemaining=0;
      this.spawn();
    }
    valid(p) { return cells(p).every(([x,y]) => x>=0 && x<10 && y>=-2 && y<20 && !this.board[y+2][x]); }
    spawn() {
      this.fillQueue(); this.active = {type:this.queue.shift(),rotation:0,x:3,y:-2}; this.fillQueue(); this.pieceId++;
      this.gravityElapsed=0; this.lockElapsed=0; this.lockResetCount=0;
      if (!this.valid(this.active)) { this.end(); return; }
      this.phase='falling'; this.ground();
    }
    end() { this.phase='gameOver'; this.active=null; }
    ground() { this.phase = this.valid({...this.active,y:this.active.y+1}) ? 'falling' : 'grounded'; }
    adjust(next) {
      if (!this.valid(next)) return false;
      const wasGrounded = this.phase === 'grounded'; this.active=next; this.ground();
      // 只在有效接地操作时重置，离地不会清除已经消耗的次数。
      if ((wasGrounded || this.phase === 'grounded') && this.lockResetCount<15) { this.lockElapsed=0; this.lockResetCount++; }
      return true;
    }
    move(dx) { return this.playable && this.adjust({...this.active,x:this.active.x+dx}); }
    rotate() {
      if (!this.playable || this.active.type==='O') return false;
      const p=this.active, list=p.type==='I'?IKICKS[p.rotation]:KICKS[p.rotation];
      for (const [dx,dy] of list) if(this.adjust({...p,rotation:(p.rotation+1)%4,x:p.x+dx,y:p.y+dy})) return true;
      return false;
    }
    down(soft=false) {
      if (!this.playable) return false;
      const next={...this.active,y:this.active.y+1};
      if (!this.valid(next)) { this.ground(); return false; }
      this.active=next; if(soft)this.score++; this.ground(); return true;
    }
    ghost() { if(!this.active)return null; const p={...this.active}; while(this.valid({...p,y:p.y+1}))p.y++; return p; }
    hardDrop() {
      if(!this.playable)return false;
      const p=this.ghost(); this.score+=2*(p.y-this.active.y); this.active=p; this.lock(); return true;
    }
    lock() {
      cells(this.active).forEach(([x,y])=>{this.board[y+2][x]=this.active.type;}); this.active=null;
      this.clearRows=[];
      for(let y=0;y<20;y++)if(this.board[y+2].every(Boolean))this.clearRows.push(y);
      if(this.clearRows.length) {
        this.score += [0,100,300,500,800][this.clearRows.length]*this.level;
        this.totalLines+=this.clearRows.length; this.level=1+Math.floor(this.totalLines/10);
        this.phase='clearing'; this.clearRemaining=180;
      } else this.finishLock();
    }
    finishLock() {
      if(this.clearRows.length) {
        const remove=new Set(this.clearRows.map(y=>y+2)); this.board=this.board.filter((_,i)=>!remove.has(i));
        while(this.board.length<22)this.board.unshift(Array(10).fill(null));
      }
      this.clearRows=[]; this.clearRemaining=0;
      if(this.board[0].some(Boolean)||this.board[1].some(Boolean)){this.end();return;}
      this.spawn();
    }
    pause() { if(this.playable||this.phase==='clearing'){this.pausedFrom=this.phase;this.phase='paused';return true;}return false; }
    resume() { if(this.phase==='paused'){this.phase=this.pausedFrom;return true;}return false; }
    tick(ms,soft=false) {
      ms=Math.min(100,Math.max(0,ms));
      if(this.phase==='clearing') { this.clearRemaining-=ms; if(this.clearRemaining<=0)this.finishLock(); return; }
      if(!this.playable)return;
      if(this.phase==='grounded') { this.lockElapsed+=ms; if(this.lockElapsed>=500)this.lock(); return; }
      this.gravityElapsed+=ms; const interval=soft?Math.min(50,this.gravityInterval):this.gravityInterval;
      while(this.playable && this.phase!=='grounded' && this.gravityElapsed>=interval){this.gravityElapsed-=interval;this.down(soft);}
    }
    snapshot() { return JSON.parse(JSON.stringify({phase:this.phase,board:this.board,active:this.active,queue:this.queue,score:this.score,totalLines:this.totalLines,level:this.level,gravityInterval:this.gravityInterval,gravityElapsed:this.gravityElapsed,lockElapsed:this.lockElapsed,lockResetCount:this.lockResetCount,clearRows:this.clearRows,clearRemaining:this.clearRemaining,sessionId:this.sessionId,pieceId:this.pieceId})); }
  }
  const api={Game,TYPES,SHAPES,cells,seeded};
  if(typeof module!=='undefined'&&module.exports)module.exports=api; else root.TetrisRules=api;
})(typeof globalThis!=='undefined'?globalThis:this);
