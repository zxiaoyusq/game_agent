(function(){
  'use strict';
  var plate=new Image(), texture=null, installed=false;
  plate.src='images/menu-score-plate.png';
  function eligible(inst){return inst.runtime.running_layout && inst.runtime.running_layout.name==='menu' && inst.type.name==='t25' && inst.layer && inst.layer.name==='Menu' && inst.visible && inst.text!=='';}
  function install(){
    var r=window.cr_getC2Runtime && window.cr_getC2Runtime(),t=r && r.types && r.types.t25;
    if(!t||!t.instances||!t.instances.length||!plate.complete||!plate.naturalWidth) return;
    if(r.canvas && !r.canvas.__scorePlateContextListener){r.canvas.addEventListener('webglcontextlost',function(){texture=null;});r.canvas.addEventListener('webglcontextrestored',function(){texture=null;r.redraw=true;});r.canvas.__scorePlateContextListener=true;}
    var proto=Object.getPrototypeOf(t.instances[0]); if(proto.__scorePlateInstalled){clearInterval(timer);return;}
    var oldDraw=proto.draw,oldGL=proto.drawGL;
    proto.draw=function(ctx){if(eligible(this)){this.rebuildText();var w=Math.max(130,this.textWidth+40);ctx.save();ctx.globalAlpha=this.opacity;ctx.drawImage(plate,this.x-w/2,this.y-27,w,54);ctx.restore();}return oldDraw.apply(this,arguments);};
    proto.drawGL=function(gl){if(eligible(this)){if(!texture) texture=gl.loadTexture(plate,false,true);gl.setTexture(texture);gl.setOpacity(this.opacity);this.rebuildText();var x=this.x,y=this.y,w=Math.max(130,this.textWidth+40);gl.quad(x-w/2,y-27,x+w/2,y-27,x+w/2,y+27,x-w/2,y+27);}return oldGL.apply(this,arguments);};
    proto.__scorePlateInstalled=true; installed=true;r.redraw=true;clearInterval(timer);
  }
  var timer=setInterval(install,100);
})();
