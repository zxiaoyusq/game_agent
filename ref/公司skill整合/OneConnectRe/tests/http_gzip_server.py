from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import gzip,io
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def send_head(self):
  path=Path(self.translate_path(self.path))
  if path.is_file() and path.suffix.lower() in ('.js','.css','.html','.json') and 'gzip' in self.headers.get('Accept-Encoding',''):
   payload=gzip.compress(path.read_bytes(),compresslevel=6,mtime=0);self.send_response(200);self.send_header('Content-Type',self.guess_type(str(path)));self.send_header('Content-Encoding','gzip');self.send_header('Vary','Accept-Encoding');self.send_header('Content-Length',str(len(payload)));self.end_headers();return io.BytesIO(payload)
  return super().send_head()
ThreadingHTTPServer(('127.0.0.1',18804),Handler).serve_forever()
