/* Pointer事件只绑定一条输入链；释放、取消、失焦统一清理长按。 */
(function(root){
  class Input {
    constructor(game,action){this.game=game;this.action=action;this.held=new Map();this.time=0;this.order=0;this.dropAt=-Infinity;this.pointerButtons=new Map();
      const map={ArrowLeft:'left',ArrowRight:'right',ArrowUp:'rotate',ArrowDown:'soft',Space:'hard',KeyP:'pause'};
      window.addEventListener('keydown',e=>{const a=map[e.code];if(!a)return;if(e.target.closest('button')&&(e.code==='Space'||e.code==='Enter'))return;e.preventDefault();if(!e.repeat)this.press('key:'+e.code,a);});
      window.addEventListener('keyup',e=>this.release('key:'+e.code));
      document.querySelectorAll('[data-action]').forEach(button=>{
        button.addEventListener('pointerdown',e=>{if(this.pointerButtons.has(button))return;e.preventDefault();button.setPointerCapture(e.pointerId);this.pointerButtons.set(button,e.pointerId);button.classList.add('held');this.press('pointer:'+e.pointerId,button.dataset.action);});
        const release=e=>{if(this.pointerButtons.get(button)!==e.pointerId)return;this.pointerButtons.delete(button);button.classList.remove('held');this.release('pointer:'+e.pointerId);};
        button.addEventListener('pointerup',release);button.addEventListener('pointercancel',release);button.addEventListener('lostpointercapture',release);
        button.addEventListener('click',e=>{if(e.detail===0){if(button.dataset.action==='soft')this.game.down(true);else this.action(button.dataset.action);}});
      });
      window.addEventListener('blur',()=>this.clear());document.addEventListener('visibilitychange',()=>this.clear());
    }
    press(id,a){if(this.held.has(id))return;this.held.set(id,{a,order:++this.order,next:this.time+150});
      if(a==='left'||a==='right')this.action(a);
      else if(a==='soft'){if(this.game.playable){this.game.gravityElapsed=0;this.game.down(true);}}
      else if(a==='hard'){// 阻止同一帧多指硬降穿透到下一枚。
        if(this.time-this.dropAt>=100){this.dropAt=this.time;this.action(a);}}
      else this.action(a);
    }
    release(id){this.held.delete(id);}
    clear(){this.held.clear();for(const button of this.pointerButtons.keys())button.classList.remove('held');this.pointerButtons.clear();}
    tick(ms){this.time+=ms;const directions=[...this.held.values()].filter(v=>v.a==='left'||v.a==='right').sort((a,b)=>b.order-a.order);if(directions[0]&&this.time>=directions[0].next){directions[0].next=this.time+60;this.action(directions[0].a);}return [...this.held.values()].some(v=>v.a==='soft');}
  }
  root.TetrisInput=Input;
})(globalThis);
