// 美术阶段专用：只合成静态预览并校验图像，不实现或模拟游戏规则。
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const crypto = require('node:crypto');
const root = process.cwd();
function read(relative) { return fs.readFileSync(path.join(root, relative)); }
function decodePNG(bytes) {
  if (!bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))) throw Error('PNG签名错误');
  let width, height, type, depth, parts=[];
  for(let p=8;p<bytes.length;) { const n=bytes.readUInt32BE(p), t=bytes.toString('ascii',p+4,p+8), d=bytes.subarray(p+8,p+8+n); if(t==='IHDR'){width=d.readUInt32BE(0);height=d.readUInt32BE(4);depth=d[8];type=d[9];if(d[12])throw Error('不支持交错PNG');} if(t==='IDAT')parts.push(d);p+=n+12; }
  if(depth!==8 || ![2,6].includes(type))throw Error('只支持8位RGB/RGBA');
  const channels=type===6?4:3, stride=width*channels, raw=zlib.inflateSync(Buffer.concat(parts)), recon=Buffer.alloc(height*stride), rgba=Buffer.alloc(width*height*4);
  function paeth(a,b,c){const p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;}
  for(let y=0;y<height;y++){const filter=raw[y*(stride+1)];if(filter>4)throw Error('PNG过滤器错误');for(let x=0;x<stride;x++){const a=x>=channels?recon[y*stride+x-channels]:0,b=y?recon[(y-1)*stride+x]:0,c=y&&x>=channels?recon[(y-1)*stride+x-channels]:0;const v=raw[y*(stride+1)+1+x];recon[y*stride+x]=(v+[0,a,b,Math.floor((a+b)/2),paeth(a,b,c)][filter])&255;}}
  for(let i=0;i<width*height;i++){rgba[i*4]=recon[i*channels];rgba[i*4+1]=recon[i*channels+1];rgba[i*4+2]=recon[i*channels+2];rgba[i*4+3]=channels===4?recon[i*channels+3]:255;}
  return {width,height,data:rgba};
}
const crcTable=Array.from({length:256},(_,n)=>{for(let i=0;i<8;i++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
function crc(bytes){let c=0xffffffff;for(const b of bytes)c=crcTable[(c^b)&255]^(c>>>8);return (c^0xffffffff)>>>0;}
function chunk(type,data){const b=Buffer.alloc(data.length+12);b.writeUInt32BE(data.length);b.write(type,4);data.copy(b,8);b.writeUInt32BE(crc(b.subarray(4,-4)),b.length-4);return b;}
function encodePNG(image){const h=Buffer.alloc(13);h.writeUInt32BE(image.width);h.writeUInt32BE(image.height,4);h[8]=8;h[9]=6;const raw=Buffer.alloc((image.width*4+1)*image.height);for(let y=0;y<image.height;y++)image.data.copy(raw,y*(image.width*4+1)+1,y*image.width*4,(y+1)*image.width*4);return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',h),chunk('IDAT',zlib.deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]);}
function canvas(width,height){return {width,height,data:Buffer.alloc(width*height*4)};}
function pixel(dst,x,y,color,alpha=1){if(x<0||y<0||x>=dst.width||y>=dst.height)return;const i=(y*dst.width+x)*4;for(let c=0;c<3;c++)dst.data[i+c]=Math.round(dst.data[i+c]*(1-alpha)+color[c]*alpha);dst.data[i+3]=255;}
function rect(dst,x,y,w,h,color,alpha=1){for(let j=Math.max(0,y);j<Math.min(dst.height,y+h);j++)for(let i=Math.max(0,x);i<Math.min(dst.width,x+w);i++)pixel(dst,i,j,color,alpha);}
function blit(dst,src,x,y,w=src.width,h=src.height,alpha=1){for(let j=0;j<h;j++)for(let i=0;i<w;i++){const sx=Math.min(src.width-1,Math.floor(i*src.width/w)),sy=Math.min(src.height-1,Math.floor(j*src.height/h)),p=(sy*src.width+sx)*4;pixel(dst,x+i,y+j,src.data.subarray(p,p+3),alpha*src.data[p+3]/255);}}
const names={I:'kingfisher',O:'leopard',T:'owl',J:'bear',S:'chameleon',L:'fox',Z:'rabbit'};
const colors={I:[73,173,241],O:[234,182,67],T:[173,121,226],J:[192,135,86],S:[106,195,91],L:[246,153,65],Z:[238,166,196]};
const samples={};
for(const [type,name] of Object.entries(names))for(const size of [24,30]){const file=`public/assets/qa/${name}-${size}.png`,im=decodePNG(read(file));if(im.width!==size||im.height!==size)throw Error('样张尺寸错误：'+file);samples[type+size]=im;}
const bg=decodePNG(read('public/assets/masters/starfield.png'));
const atlas=decodePNG(read('public/assets/masters/animal-six.png'));
if(atlas.width!==1536||atlas.height!==1024)throw Error('图集尺寸与裁切契约不符');
for(const [x,y] of [[0,0],[512,0],[1024,0],[0,512],[512,512],[1024,512]])if(x<0||y<0||x+512>atlas.width||y+512>atlas.height)throw Error('裁切越界');
const spec=JSON.parse(read('workflow/visual-spec.json'));
if(spec.language!=='zh-CN'||Object.keys(spec.tiles).length!==7)throw Error('语言或七类映射错误');
for(const t of Object.values(spec.tiles))if(!fs.existsSync(path.join(root,'public',t.path)))throw Error('缺少交接素材：'+t.path);
const html=read('assets/art-preview.html').toString();
if(!html.includes('lang="zh-CN"'))throw Error('预览语言错误');
for(const m of html.matchAll(/<img[^>]+src="([^"]+)"/g))if(!fs.existsSync(path.resolve(root,'assets',m[1])))throw Error('预览图片路径错误');
function cover(dst,src){const scale=Math.max(dst.width/src.width,dst.height/src.height),sw=dst.width/scale,sh=dst.height/scale,ox=(src.width-sw)/2,oy=(src.height-sh)/2;for(let y=0;y<dst.height;y++)for(let x=0;x<dst.width;x++){const sx=Math.floor(ox+x/scale),sy=Math.floor(oy+y/scale),p=(sy*src.width+sx)*4;pixel(dst,x,y,src.data.subarray(p,p+3));}}
function tile(dst,type,x,y,size,ghost=false,active=false){blit(dst,samples[type+size],x,y,size,size,ghost?0.18:1);if(ghost||active){const c=colors[type];for(let i=0;i<size;i++)if(!ghost||i%5<3){pixel(dst,x+i,y,c);pixel(dst,x+i,y+size-1,c);pixel(dst,x,y+i,c);pixel(dst,x+size-1,y+i,c);}}}
// 构图夹具为静态合法占格示意，非真实游玩、得分或下一块随机证据。
const rows=['..........','..........','..........','..........','..........','..........','..........','..........','..........','..........','..........','..........','..........','..........','..........','JJ........','JJ..OO....','LLL.OO..SS','LTTT...SS.','IIT..ZZJJJ'];
const active=[[4,4],[3,5],[4,5],[5,5]],ghost=[[4,14],[3,15],[4,15],[5,15]];
function preview(width,height,size,boardX,boardY,nextX,nextY){const out=canvas(width,height);cover(out,bg);rect(out,boardX-5,boardY-5,size*10+10,size*20+10,[64,91,136]);rect(out,boardX,boardY,size*10,size*20,[10,20,43]);for(let y=0;y<20;y++)for(let x=0;x<10;x++){rect(out,boardX+x*size,boardY+y*size,size,1,[23,38,65]);rect(out,boardX+x*size,boardY+y*size,1,size,[23,38,65]);const t=rows[y][x];if(t!=='.')tile(out,t,boardX+x*size,boardY+y*size,size);}
  for(const [x,y] of ghost)tile(out,'T',boardX+x*size,boardY+y*size,size,true);for(const [x,y] of active)tile(out,'T',boardX+x*size,boardY+y*size,size,false,true);
  rect(out,nextX-8,nextY-8,76,76,[28,44,74]);for(const [x,y] of [[0,0],[1,0],[0,1],[1,1]])tile(out,'O',nextX+x*30,nextY+y*30,30);
  // 无烘焙文字：HUD、按钮文案由配套HTML使用中文DOM叠加。
  return out;
}
fs.mkdirSync(path.join(root,'public/assets/previews'),{recursive:true});
const mobile=preview(390,700,24,75,112,278,30), desktop=preview(720,740,30,205,84,545,135);
for(const [name,im] of [['mobile-board.png',mobile],['desktop-board.png',desktop]]){const bytes=encodePNG(im),file='public/assets/previews/'+name;fs.writeFileSync(path.join(root,file),bytes);const round=decodePNG(bytes);if(!round.data.equals(im.data))throw Error('预览PNG回读失败');}
const sheet=canvas(420,130);rect(sheet,0,0,420,130,[11,21,50]);let k=0;for(const t of Object.keys(names)){blit(sheet,samples[t+24],14+k*58,18);blit(sheet,samples[t+30],14+k*58,70);k++;}fs.writeFileSync(path.join(root,'public/assets/previews/size-sheet.png'),encodePNG(sheet));
const runtime=['public/assets/tiles/I-kingfisher.webp','public/assets/tiles/O-leopard.webp','public/assets/tiles/T-owl-card.webp','public/assets/tiles/J-bear.webp','public/assets/tiles/S-chameleon.webp','public/assets/tiles/L-fox.webp','public/assets/tiles/Z-rabbit.webp','public/assets/backgrounds/starfield.webp'];
const inventory=runtime.map(p=>({path:p,bytes:read(p).length,sha256:crypto.createHash('sha256').update(read(p)).digest('hex')}));
if(inventory.some(a=>!a.bytes))throw Error('存在空素材');
const total=inventory.reduce((n,a)=>n+a.bytes,0);
if(total>=10*1024*1024)throw Error('运行素材超过预算');
fs.mkdirSync(path.join(root,'evidence'),{recursive:true});
fs.writeFileSync(path.join(root,'evidence/art-file-check.json'),JSON.stringify({stage:'art',checks:{sampleSizes:14,previewRoundtrip:true,cropBounds:true},runtimeBytes:total,assets:inventory,limitations:['静态合成，不验证玩法或浏览器','PNG预览使用实际WebP派生样张，背景使用生成母版','素材alpha以process_art_image结果为准，全不透明']},null,2));
console.log('美术文件检查通过：14张尺寸样张，2张棋盘预览回读一致，运行素材共'+total+'字节。未执行游戏或浏览器验收。');
