import fs from 'node:fs/promises';
import path from 'node:path';

// 无运行时依赖的静态构建，完整复制源码，便于交付后直接修改。
const root = path.resolve(import.meta.dirname, '..');
const dist = path.join(root, 'dist');
await fs.rm(dist, { recursive: true, force: true });
await fs.mkdir(dist, { recursive: true });
for (const name of ['index.html', 'src']) await fs.cp(path.join(root, name), path.join(dist, name), { recursive: true });
await fs.cp(path.join(root, 'public'), dist, { recursive: true });
async function totalBytes(directory) {
  let sum = 0;
  for (const item of await fs.readdir(directory, { withFileTypes: true })) {
    const itemPath = path.join(directory, item.name);
    sum += item.isDirectory() ? await totalBytes(itemPath) : (await fs.stat(itemPath)).size;
  }
  return sum;
}
const bytes = await totalBytes(dist);
if (bytes > 10_000_000) throw new Error(`发布包超过10MB：${bytes}字节`);
console.log(`构建完成：dist/index.html，未压缩共 ${bytes} 字节。`);
