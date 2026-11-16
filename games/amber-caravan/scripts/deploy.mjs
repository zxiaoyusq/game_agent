import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';

// 只发布已经浏览器验收的静态构建，不复制源包、存档或服务器配置。
const root = path.resolve(import.meta.dirname, '..');
const targetArgument = process.argv[2];
if (!targetArgument) throw new Error('请指定静态发布目录：node scripts/deploy.mjs <目录>');
const target = path.resolve(targetArgument);
const dist = path.join(root, 'dist');
const checks = JSON.parse(await fs.readFile(path.join(root, 'evidence/browser-results.json'), 'utf8'));
if (checks.status !== 'PASS') throw new Error('浏览器验收未通过，停止发布');
for (const [name, hash] of Object.entries(checks.sourceSha256)) {
  const actual = createHash('sha256').update(await fs.readFile(path.join(dist, name))).digest('hex');
  if (actual !== hash) throw new Error(`构建与已验收版本不一致：${name}`);
}
const manifest = JSON.parse(await fs.readFile(path.join(root, 'workflow/art-manifest.json'), 'utf8'));
for (const asset of manifest.assets) {
  const name = asset.path.replace(/^public\//, '');
  const actual = createHash('sha256').update(await fs.readFile(path.join(dist, name))).digest('hex');
  if (actual !== asset.sha256) throw new Error(`美术与已验收版本不一致：${name}`);
}

// 在同一个磁盘准备完整目录后改名生效，旧版本备份放在非公开目录便于回滚。
await fs.mkdir(path.dirname(target), { recursive: true });
const staging = await fs.mkdtemp(path.join(path.dirname(target), '.amber-caravan-'));
let backup;
try {
  await fs.cp(dist, staging, { recursive: true });
  try {
    await fs.access(target);
    backup = path.join(root, 'releases/deployment-backups', String(Date.now()));
    await fs.mkdir(path.dirname(backup), { recursive: true });
    await fs.rename(target, backup);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  try { await fs.rename(staging, target); }
  catch (error) {
    if (backup) await fs.rename(backup, target);
    throw error;
  }
  console.log(`已发布：${target}`);
  if (backup) console.log(`上一版备份：${backup}`);
} finally {
  await fs.rm(staging, { recursive: true, force: true });
}
