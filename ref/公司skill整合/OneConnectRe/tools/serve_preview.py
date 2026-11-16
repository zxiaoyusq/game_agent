from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os, webbrowser
os.chdir(Path(__file__).resolve().parent)
server=ThreadingHTTPServer(('127.0.0.1',0),SimpleHTTPRequestHandler)
url=f'http://127.0.0.1:{server.server_port}/%E5%BC%80%E5%8F%91%E9%A2%84%E8%A7%88.html'
print('Open:',url,flush=True)
webbrowser.open(url)
try: server.serve_forever()
except KeyboardInterrupt: pass
finally: server.server_close()
