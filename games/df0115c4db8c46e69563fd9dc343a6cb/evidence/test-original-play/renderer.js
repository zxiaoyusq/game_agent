/* 表现层按规则快照绘制，消行动画没有独立的结算回调。 */
(function(root){
  class Renderer {
    constructor(board,next,spec){this.canvas=board;this.next=next;this.spec=spec;this.images={};this.reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;}
    async load(){await Promise.all(Object.entries(this.spec.tiles).map(([type,data])=>new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>{this.images[type]=image;resolve();};image.onerror=()=>reject(new Error('动物牌面加载失败：'+type));image.src=data.path;})));await new Promise((resolve,reject)=>{const image=new Image();image.onload=resolve;image.onerror=()=>reject(new Error('星空背景加载失败'));image.src=this.spec.background.path;});}
    context(canvas){const rect=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);const w=Math.round(rect.width*dpr),h=Math.round(rect.height*dpr);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.imageSmoothingEnabled=true;return [ctx,rect.width,rect.height];}
    tile(ctx,type,x,y,size,ghost=false,active=false,alpha=1){
      ctx.save();ctx.globalAlpha=alpha*(ghost?.18:1);ctx.beginPath();ctx.roundRect(x+.5,y+.5,size-1,size-1,size*.16);ctx.clip();
      ctx.drawImage(this.images[type],16,16,224,224,x,y,size,size);ctx.restore();
      if(ghost||active){ctx.save();ctx.strokeStyle=this.spec.tiles[type].color;ctx.globalAlpha=ghost?.6:1;ctx.lineWidth=1;if(ghost)ctx.setLineDash([3,3]);ctx.beginPath();ctx.roundRect(x+.8,y+.8,size-1.6,size-1.6,size*.16);ctx.stroke();ctx.restore();}
    }
    draw(game){
      if(!Object.keys(this.images).length)return;
      const [ctx,w,h]=this.context(this.canvas),s=w/10;ctx.clearRect(0,0,w,h);ctx.fillStyle=this.spec.board.background;ctx.fillRect(0,0,w,h);
      ctx.strokeStyle=this.spec.board.grid;ctx.lineWidth=.5;ctx.beginPath();for(let x=0;x<=10;x++){ctx.moveTo(x*s,0);ctx.lineTo(x*s,h);}for(let y=0;y<=20;y++){ctx.moveTo(0,y*s);ctx.lineTo(w,y*s);}ctx.stroke();
      const clearing=game.phase==='clearing'||(game.phase==='paused'&&game.pausedFrom==='clearing');
      for(let y=0;y<20;y++)for(let x=0;x<10;x++){const type=game.board[y+2][x];if(type){const alpha=clearing&&game.clearRows.includes(y)&&!this.reduced&&game.clearRemaining<120?Math.max(0,game.clearRemaining/120):1;this.tile(ctx,type,x*s,y*s,s,false,false,alpha);}}
      if(game.active){const ghost=game.ghost();for(const [x,y]of TetrisRules.cells(ghost))if(y>=0)this.tile(ctx,ghost.type,x*s,y*s,s,true);for(const [x,y]of TetrisRules.cells(game.active))if(y>=0)this.tile(ctx,game.active.type,x*s,y*s,s,false,true);}
      if(clearing&&!this.reduced){const t=180-game.clearRemaining;for(const y of game.clearRows){if(t<60){ctx.fillStyle='rgba(255,245,223,'+(.25*Math.sin(t/60*Math.PI))+')';ctx.fillRect(0,y*s,w,s);}for(let i=0;i<6;i++){ctx.globalAlpha=Math.max(0,1-t/180);ctx.fillStyle='#ffe3a0';ctx.beginPath();ctx.arc((i+.5)*w/6,y*s+s/2-t*.05,1.5,0,Math.PI*2);ctx.fill();}ctx.globalAlpha=1;}}
      const [nc,nw,nh]=this.context(this.next);nc.clearRect(0,0,nw,nh);const type=game.queue[0];if(type){const p={type,rotation:0,x:0,y:0},points=TetrisRules.cells(p),xs=points.map(v=>v[0]),ys=points.map(v=>v[1]),minX=Math.min(...xs),minY=Math.min(...ys),cols=Math.max(...xs)-minX+1,rows=Math.max(...ys)-minY+1,ns=nw/4;for(const [x,y]of points)this.tile(nc,type,(x-minX)*ns+(nw-cols*ns)/2,(y-minY)*ns+(nh-rows*ns)/2,ns);}
    }
  }
  root.TetrisRenderer=Renderer;
})(globalThis);
