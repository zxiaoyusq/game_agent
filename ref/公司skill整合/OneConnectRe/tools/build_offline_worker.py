from pathlib import Path
import argparse,hashlib,json,os,tempfile

def build(game_dir):
 game_dir=Path(game_dir);worker=game_dir/'offline-worker.js'; files=sorted(p for p in game_dir.rglob('*') if p.is_file() and p!=worker)
 if not (game_dir/'game.html').is_file():raise ValueError('game.html missing')
 manifest={'./'+p.relative_to(game_dir).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 body="""// Generated. Local files only; existing host registrations take precedence.
const PREFIX='oneconnect-offline-'+encodeURIComponent(self.registration.scope)+'-';
const NAME=PREFIX+%s;
const MANIFEST=%s;
const META=new URL('__oneconnect_manifest__',self.registration.scope).href;
const allowed=new Set(Object.keys(MANIFEST).map(x=>new URL(x,self.registration.scope).href));
async function digest(response){const bytes=await response.clone().arrayBuffer();const hash=await crypto.subtle.digest('SHA-256',bytes);return Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('')}
self.addEventListener('install',event=>event.waitUntil((async()=>{
 const cache=await caches.open(NAME);try{
  let oldCache=null,oldManifest={};for(const k of (await caches.keys()).reverse()){if(k.startsWith(PREFIX)&&k!==NAME){try{const c=await caches.open(k),m=await c.match(META);if(m){const parsed=await m.json();if(!parsed||typeof parsed!=='object'||Array.isArray(parsed))continue;oldCache=c;oldManifest=parsed;break}}catch(_){/* Ignore a corrupt prior manifest and rebuild from network. */}}}
  const entries=Object.entries(MANIFEST);let next=0;
  async function run(){while(next<entries.length){let [path,expected]=entries[next++],url=new URL(path,self.registration.scope).href,response;
   if(oldCache&&oldManifest[path]===expected){response=await oldCache.match(url);if(response){try{if(await digest(response)!==expected)response=null}catch(_){response=null}}}
   if(!response){response=await fetch(new Request(url,{cache:'default'}));let valid=response.ok&&await digest(response)===expected;if(!valid){response=await fetch(new Request(url,{cache:'reload'}));valid=response.ok&&await digest(response)===expected}if(!valid)throw Error('offline cache integrity failure: '+path)}
   await cache.put(url,response)
  }}
  await Promise.all(Array.from({length:6},()=>run()));await cache.put(META,new Response(JSON.stringify(MANIFEST),{headers:{'Content-Type':'application/json'}}))
 }catch(e){await caches.delete(NAME);throw e}
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{for(const k of await caches.keys())if(k.startsWith(PREFIX)&&k!==NAME)await caches.delete(k);await self.clients.claim()})()));
self.addEventListener('fetch',event=>{if(event.request.method!=='GET')return;const url=new URL(event.request.url);if(url.pathname.endsWith('/html5games/gameapi/v1.js'))url.search='';if(!allowed.has(url.href))return;event.respondWith((async()=>{const cache=await caches.open(NAME);return(await cache.match(url.href))||fetch(event.request)})())});
"""
 # The worker itself is not a manifest entry. Include its template so a
 # changed installer never writes to (or deletes) the active version's cache.
 version=hashlib.sha256(('cache-session-v6\0'+body+'\0'+json.dumps(manifest,sort_keys=True,separators=(',',':'))).encode()).hexdigest()[:16]
 body=body%(json.dumps(version),json.dumps(manifest,ensure_ascii=False,separators=(',',':')))
 with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=game_dir,delete=False) as f:f.write(body);tmp=f.name
 os.replace(tmp,worker);return version,len(files)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);a=p.parse_args();version,n=build(a.game_dir);print('offline cache',version,'files',n)
