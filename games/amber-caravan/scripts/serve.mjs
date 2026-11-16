import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/** 本地预览与浏览器验收共享静态服务，不依赖常驻工程后端。 */
export function createServer(root) {
  const base = path.resolve(root);
  const types = { '.html': 'text/html; charset=utf-8', '.mjs': 'text/javascript', '.css': 'text/css', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.json': 'application/json' };
  return http.createServer(async (request, response) => {
    try {
      const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
      const target = path.resolve(base, `.${pathname.endsWith('/') ? pathname + 'index.html' : pathname}`);
      if (!target.startsWith(base + path.sep)) throw new Error('路径无效');
      const contents = await fs.readFile(target);
      response.writeHead(200, { 'Content-Type': types[path.extname(target)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      response.end(contents);
    } catch { response.writeHead(404); response.end('未找到文件'); }
  });
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT || 8124);
  const server = createServer(path.resolve(import.meta.dirname, '../dist'));
  server.listen(port, '0.0.0.0', () => console.log(`琥珀商路预览：http://127.0.0.1:${port}`));
}
