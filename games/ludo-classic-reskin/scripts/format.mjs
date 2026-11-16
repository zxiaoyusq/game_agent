import * as prettier from 'prettier';
import { readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
assert.equal(prettier.version, '3.6.2', '必须使用官方固定Prettier3.6.2');
// 显式范围，避免五个复用纯核心和已确认美术字节变化。
const paths = [
  'src/assets.js',
  'src/map.js',
  'src/timeline.js',
  'src/render.js',
  'src/main.js',
  'index.html',
  'style.css',
  'scripts/build.mjs',
  'scripts/zip.mjs',
  'scripts/verify-assets.mjs',
  'scripts/check.mjs',
  'scripts/browser-lifecycle.mjs',
  'scripts/browser-regression.mjs',
  'scripts/format.mjs',
  'tests/core.test.mjs',
];
for (const path of paths) {
  const source = await readFile(path, 'utf8');
  const formatted = await prettier.format(source, {
    filepath: path,
    singleQuote: true,
    printWidth: 90,
  });
  if (formatted !== source) await writeFile(path, formatted);
}
console.log(`官方Prettier3.6.2格式化完成：${paths.length}个限定文件`);
