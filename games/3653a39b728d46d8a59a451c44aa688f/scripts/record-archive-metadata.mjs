// 核对本地逐文件证据覆盖率；不执行参考游戏，不访问主工程。
// 会话路径不能由Node读取，故不伪造全量哈希回填，明确保留未测项。
import fs from 'node:fs';
import assert from 'node:assert/strict';
const inventory = JSON.parse(fs.readFileSync('workflow/resource-inventory.json','utf8'));
const audit = JSON.parse(fs.readFileSync('evidence/static-audit.json','utf8'));
assert.equal(inventory.assets.length, 321);
const measured = inventory.assets.filter(row => /^[0-9a-f]{64}$/.test(row.sha256));
assert.equal(measured.length, audit.samples.length);
for (const row of measured) {
  const sample = audit.samples.find(item => item.member === row.member);
  assert(sample);
  assert.equal(sample.sha256, row.sha256);
  assert.equal(sample.bytes, row.bytes);
}
fs.writeFileSync('evidence/archive-metadata-coverage.json', JSON.stringify({
  scope:'本地清单覆盖率，不是全量ZIP哈希副本',
  archive_sha256: inventory.archive_sha256,
  resource_entries: inventory.assets.length,
  locally_verified_hashes: measured.length,
  unfilled_hashes: inventory.assets.length-measured.length,
  known_archive_entries:329,
  known_uncompressed_bytes:5074490,
  limitation:'ZIP分页曾实际读取；其全量逐条哈希未迁入独立清单。会话路径在Node不可读，未将未测项伪造为已验证。'
},null,2));
console.log('本地逐文件证据覆盖：321条资源；实测哈希'+measured.length+'条；未回填'+(321-measured.length)+'条。');
