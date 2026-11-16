export async function loadAssets(progress) {
  const manifest=await (await fetch('./assets/manifest.json')).json();
  const images={}; let done=0;
  const entries=manifest.assets.filter(a=>/\.(png|webp)$/.test(a.path));
  await Promise.all(entries.map(async a=>{
    const name=a.path.split('/').at(-1); const image=new Image(); image.src='./assets/'+name;
    try {await image.decode();} catch {throw Error('图片加载失败：'+name);}
    images[name]=image; progress(++done,entries.length);
  }));
  const board=await (await fetch('./assets/board-contract.json')).json();
  return {images,board};
}
export class AudioBank {
  constructor() {this.effects=new Set(); this.music=new Audio('./assets/bgm.mp3'); this.music.loop=true; this.music.volume=.22; this.settings={sound:true,music:false};}
  unlock() {if(this.settings.music&&!document.hidden) this.music.play().catch(()=>{});}
  play(name) {
    if(!this.settings.sound||document.hidden) return;
    const audio=new Audio('./assets/'+name); audio.volume=.55; this.effects.add(audio);
    audio.addEventListener('ended',()=>this.effects.delete(audio),{once:true});
    audio.play().catch(()=>this.effects.delete(audio));
  }
  pause() {this.music.pause(); for(const a of this.effects) a.pause(); this.effects.clear();}
  update(settings) {this.settings=settings; this.pause(); this.unlock();}
}
