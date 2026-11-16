const fs=require('node:fs'),crypto=require('node:crypto');const {walk,pack}=require('./archive.cjs');
const play=walk('dist').sort().map(p=>({name:p.slice(5),data:fs.readFileSync(p)}));
pack(play,'releases/animal-tetris-play.zip');
const files=[...walk('src'),...walk('scripts'),...walk('tests'),...walk('workflow'),...walk('public/assets'),...walk('assets'),'package.json','package-lock.json','README.md'].sort();
pack(files.map(p=>({name:p,data:fs.readFileSync(p)})),'releases/animal-tetris-source.zip');
fs.writeFileSync('evidence/releases.json',JSON.stringify(['releases/animal-tetris-play.zip','releases/animal-tetris-source.zip'].map(p=>({path:p,bytes:fs.statSync(p).size,sha256:crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')})),null,2));console.log('离线试玩ZIP与可重建源码ZIP已写入releases。');
