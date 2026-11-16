#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INDEX_HTML="${SCRIPT_DIR}/index.html"

TITLE_RAW="$(perl -0777 -ne 'if (/<title[^>]*>\s*([^<]*)\s*<\/title>/i) { print $1; exit }' "$INDEX_HTML")"
if [ -z "$TITLE_RAW" ]; then
  echo "Failed to read <title> from: $INDEX_HTML"
  exit 1
fi

REPO_NAME_AUTO="$(printf '%s' "$TITLE_RAW" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' | sed -E 's/ /_/g')"
TAG_NAME_AUTO="v$(date +%Y%m%d%H%M)"

if [ $# -eq 0 ]; then
  REPO_NAME="$REPO_NAME_AUTO"
  TAG_NAME="$TAG_NAME_AUTO"
elif [ $# -eq 2 ]; then
  REPO_NAME="$1"
  TAG_NAME="$2"
else
  echo "Usage: $0 [<参数1> <参数2>]"
  exit 1
fi

# 初始化 Git 仓库
echo "Initializing Git repository..."
git init

# 添加所有文件到暂存区
echo "Adding files to staging area..."
git add .

# 提交到本地仓库
echo "Committing changes..."
git commit -m "init"

# 添加远程仓库地址
REMOTE_URL="git@game-gitlab.ahagamecenter.com:game-h5/excellenth5game/${REPO_NAME}.git"
echo "Adding remote repository: $REMOTE_URL"
git remote add origin "$REMOTE_URL"

# 推送到远程 master 分支
echo "Pushing to remote master branch..."
git push origin master

# 创建附注标签
echo "Creating annotated tag: $TAG_NAME"
git tag -a "$TAG_NAME" -m "申请代码发布-初始化"

# 推送标签到远程仓库
echo "Pushing tags to remote repository..."
git push origin --tags

echo "Git operations completed successfully!"
