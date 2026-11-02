// 复制可独立部署的静态 Web 包；引擎只能来自已成功编译的官方产物。
import { cp, mkdir, rm, access } from 'node:fs/promises';
await access(new URL('../public/engine/cc.js', import.meta.url));
const target = new URL('../dist/', import.meta.url);
await rm(target, { recursive: true, force: true });
await mkdir(target, { recursive: true });
await cp(new URL('../public/', import.meta.url), target, { recursive: true });
await cp(new URL('../src/', import.meta.url), new URL('src/', target), { recursive: true });
console.log('彩球工坊 Web 成品已打包到 dist');
