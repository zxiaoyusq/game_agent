import fs from 'node:fs';
// 仅研究索引，不执行参考源码，不解包。
const cfg=JSON.parse(fs.readFileSync('reference-inputs/superstar-resources.json','utf8'));
const table='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
function decode(s){if(s.length!==22)return s;let h=s.slice(0,2);for(let i=2;i<22;i+=2){const a=table.indexOf(s[i]),b=table.indexOf(s[i+1]);h+=(a>>2).toString(16)+(((a&3)<<2)|(b>>4)).toString(16)+(b&15).toString(16);}return h.slice(0,8)+'-'+h.slice(8,12)+'-'+h.slice(12,16)+'-'+h.slice(16,20)+'-'+h.slice(20);}
const versions=new Map();for(let i=0;i<cfg.versions.native.length;i+=2)versions.set(cfg.versions.native[i],cfg.versions.native[i+1]);
function native(s,ext='png'){let idx=cfg.uuids.indexOf(s),id=decode(s);return `www.hnyigegame.com/Ludo_Superstar/game/${idx<0?'': ''}loading/assets/resources/native/${id.slice(0,2)}/${id}.${versions.get(idx)}.${ext}`;}
const pack=JSON.parse(fs.readFileSync('reference-inputs/superstar-dice-animation-pack.json','utf8'));const frames=pack[5].filter(e=>e[0]?.[0]?.name).map(e=>({...e[0][0],member:native(pack[1][e[5][0]])}));
const audios=[4,7,12,26,27,40,43,44].map(i=>({name:cfg.paths[i][0],member:native(cfg.uuids[i],i===7?'ogg':'mp3').replace('/loading/',i===12?'/loading/':'/')}));
fs.mkdirSync('evidence',{recursive:true});fs.writeFileSync('evidence/art-source-index.json',JSON.stringify({frames,audios},null,2));const local=[0,3,13,21,23,29,32,33,34,42].map(i=>({name:cfg.paths[i][0],member:native(cfg.uuids[i])}));const code=fs.readFileSync('reference-inputs/superstar-main.js','utf8');const snippets=[...code.matchAll(/.{0,140}(?:img_head|headIcon|head_icon|avatar).{0,180}/g)].slice(0,25).map(m=>m[0]);console.log(JSON.stringify({photos:[...code.matchAll(/.{0,100}(?:Photo|photo).{0,180}/g)].map(m=>m[0]).slice(0,35)},null,2));
