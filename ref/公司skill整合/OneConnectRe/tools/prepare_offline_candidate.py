from pathlib import Path
import hashlib,json,shutil
root=Path.cwd();source=root/'game';stage=root/'analysis/offline_stage_20261030';
if stage.exists():raise SystemExit('stage exists')
shutil.copytree(source,stage)
files=sorted(p for p in stage.rglob('*') if p.is_file()); listing=[p.relative_to(stage).as_posix() for p in files]
h=hashlib.sha256()
for p in files:h.update(p.relative_to(stage).as_posix().encode());h.update(hashlib.sha256(p.read_bytes()).digest())
version=h.hexdigest()[:16]
worker='''const CACHE_NAME = 'oneconnect-offline-%s';
const FILES = %s;
const allowed = new Set(FILES.map(x => new URL(x, self.registration.scope).href));
self.addEventListener('install', event => event.waitUntil((async()=>{const cache=await caches.open(CACHE_NAME);await cache.addAll(FILES);await self.skipWaiting()})()));
self.addEventListener('activate', event => event.waitUntil((async()=>{for(const k of await caches.keys())if(k.startsWith('oneconnect-offline-')&&k!==CACHE_NAME)await caches.delete(k);await self.clients.claim()})()));
self.addEventListener('fetch', event => {if(event.request.method!=='GET'||!allowed.has(event.request.url))return;event.respondWith((async()=>{const cache=await caches.open(CACHE_NAME);return (await cache.match(event.request))||fetch(event.request)})())});
'''%(version,json.dumps(['./'+x for x in listing],ensure_ascii=False));(stage/'offline-worker.js').write_text(worker,encoding='utf8')
loader='''<script>
(function(){
 if (!('serviceWorker' in navigator) || !(location.protocol === 'https:' || location.hostname === '127.0.0.1' || location.hostname === 'localhost')) return;
 var timer=setInterval(function(){
   var r=window.cr_getC2Runtime && window.cr_getC2Runtime();
   if (!r || !r.running_layout) return;
   clearInterval(timer);
   navigator.serviceWorker.getRegistration(new URL('./',location.href).href).then(function(existing){
     if(existing && !existing.active?.scriptURL.endsWith('/offline-worker.js')) return;
     return navigator.serviceWorker.register('./offline-worker.js',{scope:'./'});
   }).catch(function(error){console.warn('Offline cache unavailable:',error)});
 },1000);
})();
</script>
'''
p=stage/'game.html';s=p.read_text(encoding='utf8');assert s.count('</body>')==1;p.write_text(s.replace('</body>',loader+'</body>'),encoding='utf8');print('offline stage',len(listing),'version',version)
