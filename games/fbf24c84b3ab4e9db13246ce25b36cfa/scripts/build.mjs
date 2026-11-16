import { cp, mkdir, readFile, readdir, rm, stat, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

export async function fileList(root) {
  const result = [];
  async function walk(path) {
    for (const entry of (await readdir(path, { withFileTypes: true })).sort((a,b) => a.name.localeCompare(b.name, 'en'))) {
      const full = `${path}/${entry.name}`;
      if (entry.isDirectory()) await walk(full); else result.push(full);
    }
  }
  await walk(root); return result;
}
export async function fingerprints(paths) {
  const files = [];
  for (const path of paths.sort()) {
    const bytes = await readFile(path);
    files.push({ path, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') });
  }
  return { sha256: createHash('sha256').update(JSON.stringify(files)).digest('hex'), files };
}
export async function build(destination = 'dist') {
  const manifest = JSON.parse(await readFile('workflow/art-manifest.json', 'utf8'));
  for (const asset of manifest.assets) {
    const hash = createHash('sha256').update(await readFile(asset.path)).digest('hex');
    assert.equal(hash, asset.sha256, `上游资源被改动：${asset.path}`);
  }
  await rm(destination, { recursive: true, force: true }); await mkdir(destination, { recursive: true });
  await cp('public', destination, { recursive: true });
  const files = await fileList(destination);
  let bytes = 0; for (const path of files) bytes += (await stat(path)).size;
  assert(bytes < 10 * 1024 * 1024, '展开构建超过10MB');
  return { bytes, fingerprint: await fingerprints(files) };
}
if (process.argv[1]?.endsWith('/build.mjs')) {
  const result = await build();
  const source = await fingerprints([...await fileList('public'), ...await fileList('scripts'), ...await fileList('tests'), 'package.json', 'package-lock.json']);
  await mkdir('evidence', { recursive: true });
  await writeFile('evidence/build.json', JSON.stringify({ result: '通过', ...result, source }, null, 2) + '\n');
  console.log(`构建通过：dist/index.html，展开${result.bytes}字节；资源哈希与上游一致。`);
}
