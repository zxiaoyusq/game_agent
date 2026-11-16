import { spawnSync } from 'node:child_process';
// 仅安装官方固定版本，关闭生命周期；不是自制格式化器。
for (const args of [['uninstall', '@playwright/test', '--ignore-scripts'], ['install', '--save-dev', '--save-exact', 'prettier@3.6.2', '--ignore-scripts']]) {
  const result = spawnSync('npm', args, { stdio: 'inherit' });
  if (result.status !== 0) process.exit(result.status || 1);
}
