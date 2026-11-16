import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

export const hash = (data) => createHash('sha256').update(data).digest('hex');
// 冻结资源白名单：逐件校验字节、尺寸、RGBA和上游清单，不扫描后自动收录。
export async function verifyAssets(root = '.') {
  const manifest = JSON.parse(
    await readFile(`${root}/public/assets/visual-manifest.json`, 'utf8'),
  );
  const art = JSON.parse(await readFile(`${root}/workflow/art-manifest.json`, 'utf8'));
  assert.equal(manifest.assets.length, 58);
  assert.deepEqual(
    manifest.assets.map((a) => a.runtime_path),
    manifest.package_policy.only_assets_allowlist,
  );
  for (const asset of manifest.assets) {
    const bytes = await readFile(`${root}/${asset.path}`);
    assert.equal(hash(bytes), asset.sha256, `素材哈希变化：${asset.path}`);
    assert.equal(bytes.length, asset.bytes);
    assert.equal(art.assets.find((a) => a.path === asset.path)?.sha256, asset.sha256);
    if (asset.output_format === 'PNG') {
      assert.equal(bytes.readUInt32BE(16), asset.size[0]);
      assert.equal(bytes.readUInt32BE(20), asset.size[1]);
      assert.equal(bytes[25], 6);
    }
  }
  assert.equal(
    hash(await readFile(`${root}/public/assets/visual-manifest.json`)),
    '896bcf843a797a6dbcfa1f2edd46bf261d7e074d4369ae92235553e5b6b26c95',
  );
  assert.equal(
    hash(await readFile(`${root}/workflow/art-manifest.json`)),
    '7955424cd32138f68ebbb4356b51ed808af1f52a194260f2ce8647f8a3f4c4fe',
  );
  return manifest;
}
