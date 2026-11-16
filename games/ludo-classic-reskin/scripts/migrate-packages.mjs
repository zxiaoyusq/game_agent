import { readdir, mkdir, rename, rmdir, readFile, writeFile, access } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { hash } from './verify-assets.mjs';
// 一次性有限迁移；未知内容不删除，目标已存在时拒绝覆盖。
const allowed = ['ludo-classic-reskin-dist.zip', 'ludo-classic-reskin-source.zip'];
const entries = await readdir('delivery');
assert(entries.every(name => allowed.includes(name)), 'delivery存在非本项目归档，停止迁移');
await mkdir('releases/initial-code', { recursive: true });
const records = [];
for (const name of entries) {
  const target = `releases/initial-code/${name}`;
  let exists = false;
  try { await access(target); exists = true; } catch {}
  assert(!exists, `拒绝覆盖：${target}`);
  const bytes = await readFile(`delivery/${name}`);
  await rename(`delivery/${name}`, target);
  records.push({ path: target, bytes: bytes.length, sha256: hash(bytes) });
}
await rmdir('delivery');
await writeFile('evidence/package-migration.json', JSON.stringify(records, null, 2));
console.log('旧版两个ZIP已有限迁移，delivery目录已不存在');
