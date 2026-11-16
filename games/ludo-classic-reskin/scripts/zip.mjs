import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve, sep } from 'node:path';
import assert from 'node:assert/strict';
// 标准ZIP的store方法，无外部打包器依赖。只解包本工程自行生成的交付包。
function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
  }
  return (crc ^ 0xffffffff) >>> 0;
}
export async function zipFiles(destination, files) {
  const locals = [],
    central = [];
  let offset = 0;
  for (const file of files) {
    const data = await readFile(file.path),
      name = Buffer.from(file.name);
    const crc = crc32(data);
    const header = Buffer.alloc(30);
    header.writeUInt32LE(0x04034b50);
    header.writeUInt16LE(20, 4);
    header.writeUInt16LE(0x800, 6);
    header.writeUInt32LE(crc, 14);
    header.writeUInt32LE(data.length, 18);
    header.writeUInt32LE(data.length, 22);
    header.writeUInt16LE(name.length, 26);
    locals.push(header, name, data);
    const entry = Buffer.alloc(46);
    entry.writeUInt32LE(0x02014b50);
    entry.writeUInt16LE(20, 4);
    entry.writeUInt16LE(20, 6);
    entry.writeUInt16LE(0x800, 8);
    entry.writeUInt32LE(crc, 16);
    entry.writeUInt32LE(data.length, 20);
    entry.writeUInt32LE(data.length, 24);
    entry.writeUInt16LE(name.length, 28);
    entry.writeUInt32LE(offset, 42);
    central.push(entry, name);
    offset += header.length + name.length + data.length;
  }
  const centralSize = central.reduce((sum, b) => sum + b.length, 0);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50);
  end.writeUInt16LE(files.length, 8);
  end.writeUInt16LE(files.length, 10);
  end.writeUInt32LE(centralSize, 12);
  end.writeUInt32LE(offset, 16);
  await mkdir(dirname(destination), { recursive: true });
  await writeFile(destination, Buffer.concat([...locals, ...central, end]));
}
export async function unzipOwn(path, destination) {
  const data = await readFile(path);
  let offset = 0;
  const files = [];
  while (data.readUInt32LE(offset) === 0x04034b50) {
    assert.equal(data.readUInt16LE(offset + 8), 0);
    const size = data.readUInt32LE(offset + 18),
      n = data.readUInt16LE(offset + 26),
      extra = data.readUInt16LE(offset + 28);
    const name = data.subarray(offset + 30, offset + 30 + n).toString();
    const start = offset + 30 + n + extra,
      bytes = data.subarray(start, start + size);
    assert.equal(crc32(bytes), data.readUInt32LE(offset + 14));
    const target = resolve(destination, name);
    assert(target.startsWith(resolve(destination) + sep));
    await mkdir(dirname(target), { recursive: true });
    await writeFile(target, bytes);
    files.push(name);
    offset = start + size;
  }
  return files;
}
