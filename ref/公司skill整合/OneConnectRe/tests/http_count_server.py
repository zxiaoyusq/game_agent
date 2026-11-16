from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import json,sys,time,threading
lock=threading.Lock()
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def log_request(self,code='-',size='-'):
  path=self.translate_path(self.path)
  try:n=Path(path).stat().st_size if int(code)==200 and Path(path).is_file() else 0
  except (ValueError,OSError):n=0
  with lock:
   with open('analysis/offline_cache_network_log_v2.jsonl','a',encoding='utf8') as f:f.write(json.dumps({'time':time.time(),'path':self.path,'code':str(code),'body_bytes':n})+'\n')
ThreadingHTTPServer(('127.0.0.1',18803),Handler).serve_forever()
