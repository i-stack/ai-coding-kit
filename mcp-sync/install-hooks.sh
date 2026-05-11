#!/usr/bin/env bash
# 将本仓库的 Git 钩子目录设为 githooks（可提交、可版本管理）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$ROOT/githooks/pre-push"
git -C "$ROOT" config core.hooksPath githooks

echo "已设置 core.hooksPath=githooks；此后 git push 前会执行 sync_all.sh。"
echo "单次跳过：git push --no-verify"
