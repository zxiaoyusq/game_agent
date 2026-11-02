// 使用官方源码和官方 ccbuild 构建器，生成真实的 Cocos WebGL 运行时。
const path = require('node:path');
const fs = require('node:fs');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const os = require('node:os');
const configuredEngine = process.env.COCOS_ENGINE_PATH || path.join(process.env.XDG_CACHE_HOME || path.join(os.homedir(), '.cache'), 'cocos/cocos-engine-3.8.8');
const project = path.resolve(__dirname, '..');
(async () => {
  if (!fs.existsSync(path.join(configuredEngine, 'package.json'))) throw new Error('请先按 README 下载官方 Cocos Engine 3.8.8 源码并安装依赖');
  // ccbuild 的模块重定向依赖真实路径，自定义符号链接必须先展开。
  const engine = fs.realpathSync(configuredEngine);
  const version = JSON.parse(fs.readFileSync(path.join(engine, 'package.json'))).version;
  if (version !== '3.8.8') throw new Error(`引擎版本必须为 3.8.8，当前为 ${version}`);
  // 上游 DebugInfos 属于生成文件；独立源码编译前必须运行官方生成器。
  execFileSync(process.execPath, [path.join(engine, 'scripts/build-debug-infos')], { cwd: engine, stdio: 'inherit' });
  const expectedCommit = '411f98df047c25902f93440d4b22925c2fb65461';
  const expectedTarballSha256 = '8af14ad3f861b9edd1d90c928a676ccaec4d9ec6d0bce42f56c59c9b3a82afa5';
  const archive = process.env.COCOS_ENGINE_ARCHIVE || path.join(engine, '../engine-3.8.8.tar.gz');
  const tarballSha256 = fs.existsSync(archive) ? crypto.createHash('sha256').update(fs.readFileSync(archive)).digest('hex') : null;
  if (tarballSha256 && tarballSha256 !== expectedTarballSha256) throw new Error('引擎归档 SHA256 与固定官方版本不匹配');
  const sourceComparison = tarballSha256 ? JSON.parse(execFileSync('python3', [path.join(project, 'scripts/verify-engine-source.py'), archive, engine], { encoding:'utf8' })) : null;
  let gitCommit = null, gitDirty = null;
  try {
    const gitRoot = execFileSync('git', ['-C', engine, 'rev-parse', '--show-toplevel'], { encoding:'utf8', stdio:['ignore','pipe','ignore'] }).trim();
    if (fs.realpathSync(gitRoot) === engine) {
      gitCommit = execFileSync('git', ['-C', engine, 'rev-parse', 'HEAD'], { encoding:'utf8' }).trim();
      gitDirty = !!execFileSync('git', ['-C', engine, 'status', '--porcelain', '--untracked-files=no'], { encoding:'utf8' }).trim();
    }
  } catch { /* 非 Git 的源码归档目录由逐文件比较证明身份。 */ }
  const { buildEngine } = require(path.join(engine, 'node_modules/@cocos/ccbuild'));
  const result = await buildEngine({
    engine, out: path.join(project, 'public/engine'), moduleFormat: 'esm',
    mode: 'BUILD', platform: 'HTML5', compress: false, sourceMap: false,
    features: ['base', 'legacy-pipeline', 'gfx-webgl', 'gfx-webgl2', '2d', 'graphics', 'ui', 'tween', 'audio'],
    flags: { DEBUG: false, NATIVE: false },
  });
  execFileSync(process.execPath, [path.join(project, 'scripts/prepare-effects.mjs')], { env: {...process.env, COCOS_ENGINE_PATH: engine}, stdio:'inherit' });
  fs.copyFileSync(path.join(engine, 'LICENSE.md'), path.join(project, 'public/engine/LICENSE.md'));
  const runtimeSha256 = crypto.createHash('sha256').update(fs.readFileSync(path.join(project, 'public/engine/cc.js'))).digest('hex');
  fs.writeFileSync(path.join(project, 'evidence/engine-build.json'), JSON.stringify({
    version: '3.8.8', source: 'https://github.com/cocos/cocos-engine/releases/tag/3.8.8',
    commit: gitCommit || (sourceComparison?.matched ? expectedCommit : null),
    expectedCommit, gitCommit, gitDirty, expectedTarballSha256, sourceComparison,
    sourceIdentityVerified: !!(sourceComparison?.matched || (gitCommit === expectedCommit && !gitDirty)),
    runtimeSha256,
    builderVersion: require(path.join(engine, 'node_modules/@cocos/ccbuild/package.json')).version,
    tarballSha256,
    sourceVersionVerified: version,
    builtAt: new Date().toISOString(), result,
  }, null, 2));
  console.log('Cocos 3.8.8 官方引擎 WebGL 构建完成');
})().catch(error => { console.error('引擎构建失败：', error); process.exitCode = 1; });
