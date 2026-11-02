#!/usr/bin/env bash
# 固定官方版本与内容哈希，在 Linux 上重现真实 Cocos WebGL 构建。
set -euo pipefail
project_path="$(cd "$(dirname "$0")/.." && pwd)"
engine_path="${COCOS_ENGINE_PATH:-${XDG_CACHE_HOME:-$HOME/.cache}/cocos/cocos-engine-3.8.8}"
archive_path="${COCOS_ENGINE_ARCHIVE:-$(dirname "$engine_path")/engine-3.8.8.tar.gz}"
archive_hash="8af14ad3f861b9edd1d90c928a676ccaec4d9ec6d0bce42f56c59c9b3a82afa5"
mkdir -p "$engine_path" "$(dirname "$archive_path")"
if [ ! -f "$engine_path/package.json" ]; then
  if [ ! -f "$archive_path" ]; then
    echo '正在下载官方 Cocos Engine 3.8.8 源码'
    curl --fail --location --silent --show-error 'https://codeload.github.com/cocos/cocos-engine/tar.gz/refs/tags/3.8.8' --output "$archive_path"
  fi
  printf '%s  %s\n' "$archive_hash" "$archive_path" | sha256sum --check --status
  tar -xzf "$archive_path" --strip-components=1 -C "$engine_path"
fi
# 使用已通过本项目实际构建的完整依赖锁，避开上游锁中的旧镜像地址。
cp "$project_path/scripts/engine-package-lock.json" "$engine_path/package-lock.json"
(cd "$engine_path" && npm ci --ignore-scripts --no-audit --no-fund && npm run build:debug-infos)
COCOS_ENGINE_PATH="$engine_path" COCOS_ENGINE_ARCHIVE="$archive_path" node "$project_path/scripts/build-engine.cjs"
