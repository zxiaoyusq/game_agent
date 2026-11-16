import { readFile, writeFile, mkdir, cp, rm, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import assert from 'node:assert/strict';
import { verifyAssets, hash } from './verify-assets.mjs';
import { zipFiles } from './zip.mjs';
export async function walk(root) {
  const files = [];
  for (const item of await readdir(root, { withFileTypes: true })) {
    const path = join(root, item.name);
    if (item.isDirectory()) files.push(...(await walk(path)));
    else files.push(path);
  }
  return files.sort();
}
const manifest = await verifyAssets();
await rm('dist', { recursive: true, force: true });
await mkdir('dist/assets', { recursive: true });
await cp('src', 'dist/src', { recursive: true });
for (const name of ['index.html', 'style.css']) await cp(name, `dist/${name}`);
for (const asset of manifest.assets) await cp(asset.path, `dist/${asset.runtime_path}`);
await cp('public/assets/visual-manifest.json', 'dist/assets/visual-manifest.json');
const files = await walk('dist');
let total = 0;
const hashes = {};
for (const path of files) {
  const bytes = await readFile(path);
  total += bytes.length;
  hashes[path.slice(5)] = hash(bytes);
}
assert(total < 10000000, '构建超过10MB');
await mkdir('evidence', { recursive: true });
await writeFile(
  'evidence/build.json',
  JSON.stringify({ totalBytes: total, hashes, assets: manifest.assets.length }, null, 2),
);
if (!process.env.REBUILD_ONLY) {
  await zipFiles(
    'releases/ludo-classic-reskin-dist.zip',
    files.map((path) => ({ path, name: path.slice(5) })),
  );
  // 明确打包白名单；不带美术生产脚本、一次性迁移器或凭据。
  const names = [
    'README.md',
    'package.json',
    'package-lock.json',
    'index.html',
    'style.css',
    'workflow/art-manifest.json',
    'design/reuse-baseline.json',
    'design/acceptance.md',
    'design/art-integration.md',
    'design/visual-baseline.md',
    'reference-assets/camp-calibration.json',
    'public/assets/visual-manifest.json',
    ...manifest.assets.map((a) => a.path),
    ...(await walk('src')),
    ...(await walk('tests')),
    ...(await walk('scripts')).filter(
      (p) =>
        ![
          'audit-art.mjs',
          'migrate-packages.mjs',
          'prepare-format.mjs',
          'patch-lifecycle.mjs',
        ].some((name) => p.endsWith(name)),
    ),
  ];
  await zipFiles(
    'releases/ludo-classic-reskin-source.zip',
    names.map((path) => ({ path, name: path })),
  );
}
console.log(
  `构建完成：${total}字节，58件白名单资源，相对路径，独立ludo-classic-reskin入口`,
);
