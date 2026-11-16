import {COLORS,NAMES,legalMoves} from './rules.js';
import {segmentAt,ROLL_MS} from './animation.js';
const TINT=['#3988ff','#ef333e','#21d14e','#ffd225'];
export class Renderer {
  constructor(canvas,assets) {this.canvas=canvas; this.ctx=canvas.getContext('2d'); this.assets=assets; this.hits=[]; this.resize();}
  resize() {const rect=this.canvas.getBoundingClientRect(), dpr=Math.min(devicePixelRatio||1,2); this.canvas.width=Math.round(rect.width*dpr); this.canvas.height=Math.round(rect.height*dpr); this.ctx.setTransform(this.canvas.width/720,0,0,this.canvas.height/1280,0,0);}
  point(local) {return [360+1.15*local[0],640-1.15*local[1]];}
  infoPoint(p) {const point=this.point(this.assets.board.player_info_centers[p]);if(p===0||p===3)point[1]-=55;return point;}
  position(loc) {
    const {p,i,pos,parked}=loc, b=this.assets.board;
    if(parked) {const center=this.point(b.terminal_visual_centers[p]); return [center[0]+(i%2?12:-12),center[1]+(i<2?-8:9)];}
    return this.point(pos<0?b.base_token_centers[p][i]:b.grid_centers[pos]);
  }
  image(name,x,y,w,h,angle=0) {
    const c=this.ctx,img=this.assets.images[name]; if(!img) return;
    c.save(); c.translate(x,y); if(angle)c.rotate(angle); c.drawImage(img,-w/2,-h/2,w,h); c.restore();
  }
  label(text,x,y,size=28,color='#fff') {const c=this.ctx; c.fillStyle=color; c.font=`bold ${size}px system-ui,sans-serif`; c.textAlign='center'; c.textBaseline='middle'; c.fillText(text,x,y);}
  halo(x,y,color,r=29,alpha=1) {const c=this.ctx; c.save();c.globalAlpha=alpha;c.strokeStyle=color;c.lineWidth=5;c.beginPath();c.arc(x,y,r,0,Math.PI*2);c.stroke();c.restore();}
  token(p,i,x,y,scale=1,highlight=false) {
    const color=COLORS[p]; if(highlight)this.halo(x,y+14,TINT[p],26);
    this.image(`token-${color}${p===1?'-packed':''}.png`,x,y, (p===1?52:p===0?32:33)*1.15*scale,(p===1?32:53)*1.15*scale,p===1?Math.PI/2:0);
    this.label(String(i+1),x,y-3,18*scale,'#fff');
  }
  draw(session,time=0) {
    const c=this.ctx,b=this.assets.board,g=session?.game; c.clearRect(0,0,720,1280);this.hits=[];
    this.image('background.png',360,640,720,1602);
    for(let p=0;p<4;p++) {const [x,y]=this.point(b.camp_centers[p]);this.image(`camp-${COLORS[p]}.png`,x,y,233*1.15,233*1.15);}
    const center=this.point(b.board_sprite_center);this.image('board.png',...center,586*1.15,585*1.15);
    for(const pos of b.safe_grids.filter(x=>x%13!==0)) this.image('safe-star.png',...this.point(b.grid_centers[pos]),27*1.15,26*1.15);
    if(!g) return;
    for(let p=0;p<4;p++) {
      const [x,y]=this.infoPoint(p);
      c.save();if(g.seats[p]==='off')c.globalAlpha=.3;
      this.image(`info-${COLORS[p]}.png`,x-42,y,138,138);
      this.image(`avatar-${g.seats[p]==='ai'?'ai':'human'}.png`,x-42,y-7,g.seats[p]==='ai'?70:60,76);
      this.label(`${NAMES[p]}方${g.seats[p]==='off'?' · 空席':''}`,x-42,y+53,24);
      if(g.current===p&&g.winner===null)this.halo(x-42,y,TINT[p],71);
      this.dice(session,p,x+88,y);
      c.restore();
      if(g.mode==='quick'&&!g.unlocked[p]&&g.seats[p]!=='off') this.image('gate-packed.png',...this.point(b.grid_centers[52+6*p]),33*1.15,15*1.15,Math.PI/2+p*Math.PI/2);
    }
    const valid=session.phase==='choosing'?legalMoves(g):[];
    const moving=session.phase==='moving'?segmentAt(session.segments,session.elapsed):null;
    const poses=new Map();
    if(session.phase==='moving') {
      let offset=0;
      for(const s of session.segments) {
        if(session.elapsed>=offset+s.ms) poses.set(s.who.join(':'),{position:this.position(s.to),scale:1});
        else if(session.elapsed>=offset) {
          const t=Math.min(1,(session.elapsed-offset)/s.ms), a=this.position(s.from),z=this.position(s.to);
          const jump=s.kind==='walk'?Math.sin(Math.PI*t)*22:s.kind==='return'?Math.sin(Math.PI*t)*9:0;
          poses.set(s.who.join(':'),{position:[a[0]+(z[0]-a[0])*t,a[1]+(z[1]-a[1])*t-jump],scale:s.kind==='home'?1+.35*Math.sin(Math.PI*t):1+.12*Math.sin(Math.PI*t)});
          break;
        } else break;
        offset+=s.ms;
      }
    }
    const occupied=new Map();
    g.tokens.forEach((list,p)=>list.forEach((token,i)=>{if(token.pos>=0&&!token.finished&&!poses.has(`${p}:${i}`)){const key=token.pos; if(!occupied.has(key))occupied.set(key,[]);occupied.get(key).push([p,i]);}}));
    const foreground=[];
    g.tokens.forEach((list,p)=>list.forEach((token,i)=>{
      const key=`${p}:${i}`,pose=poses.get(key);let [x,y]=pose?.position||this.position({p,i,pos:token.pos,parked:token.finished});let scale=pose?.scale||1;
      const group=!pose&&!token.finished?occupied.get(token.pos):null;
      if(group?.length>1) {const j=group.findIndex(a=>a[0]===p&&a[1]===i);x+=((j%3)-1)*12;y+=Math.floor(j/3)*12;scale=.76;}
      const highlight=p===g.current&&valid.includes(i);
      if(pose)foreground.push(()=>this.token(p,i,x,y,scale,highlight));else this.token(p,i,x,y,scale,highlight);
      if(highlight)this.hits.push({x,y,p,i});
    }));
    foreground.forEach(fn=>fn());
    if(moving?.segment.kind==='home') {const s=moving.segment;this.halo(...this.position(s.to),TINT[s.who[0]],32+moving.t*23,1-moving.t*.5);}
    if(session.phase==='celebrating'||session.phase==='result') {
      const p=g.winner,[x,y]=this.point(b.terminal_visual_centers[p]);this.halo(x,y,TINT[p],60+8*Math.sin(time/130));
      if(session.phase==='celebrating') {
        for(let i=0;i<72;i++) {const t=session.elapsed/1500,angle=i*2.399; c.fillStyle=TINT[i%4]; c.save();c.translate(360+Math.cos(angle)*t*(150+i%9*30),600+Math.sin(angle)*t*250+t*t*260);c.rotate(time/200+i);c.fillRect(-4,-7,8,14);c.restore();}
        this.label(`${NAMES[p]}方获胜！`,360,330,58,'#ffdf62');
      }
    }
  }
  dice(s,p,x,y) {
    const c=this.ctx, active=s.game.current===p;
    c.save();c.translate(x,y);c.scale(.82,.82);
    if(s.phase==='rolling'&&active) {
      this.image(`dice-roll-${String(Math.min(24,Math.floor(s.elapsed/(1000/30)))).padStart(2,'0')}.png`,0,0,220,220);
    } else {
      const face=active&&s.game.dice?s.game.dice:1;
      // 六面裁片放回原220画布trim位置，不把裁片撑成220。
      c.drawImage(this.assets.images[`dice-face-${face}.png`],62-110,54-110,104,106);
    }
    c.restore();
  }
}
