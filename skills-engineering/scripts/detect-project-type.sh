#!/usr/bin/env bash
#
# detect-project-type.sh — 探测一个项目目录的技术栈类型。
#
# 用法:
#   ./detect-project-type.sh [PROJECT_ROOT]
#     PROJECT_ROOT 缺省为当前工作目录 (.)。
#
# 输出:
#   单行、空格分隔的平台类型标签。可能值（去重、顺序稳定）:
#     ios  android  web  backend  flutter  react-native  unknown
#   无任何命中时输出 "unknown"（注意: 仍是一行，便于脚本消费）。
#
# 退出码:
#   0  成功（总是成功，最多输出 unknown）。
#
# 设计原则:
#   - 纯信号文件探测，不读文件内容、不跑构建、不联网，毫秒级。
#   - 一个项目可以是多类型的（如 react-native 同时含 ios/android/web）。
#   - 仅输出"该仓库里存在哪种平台的工程信号"，是否真正加载某 skill
#     仍由各 SKILL.md 门控决定；本脚本只决定生成哪些 .mdc。

set -euo pipefail

PROJECT_ROOT="${1:-.}"
[[ -d "${PROJECT_ROOT}" ]] || { echo "unknown"; exit 0; }

# 进入目标目录，后续用相对路径探测
cd "${PROJECT_ROOT}" || { echo "unknown"; exit 0; }

types=()

# ── iOS ────────────────────────────────────────────────────────────────
if compgen -G "*.xcodeproj" >/dev/null 2>&1 \
   || compgen -G "*.xcworkspace" >/dev/null 2>&1 \
   || [[ -f "Package.swift" ]] \
   || [[ -f "Podfile" ]] \
   || [[ -f "Cartfile" ]]; then
  types+=(ios)
fi

# ── Android ─────────────────────────────────────────────────────────────
if [[ -f "settings.gradle" ]] \
   || [[ -f "settings.gradle.kts" ]] \
   || [[ -f "build.gradle" ]] \
   || [[ -f "build.gradle.kts" ]] \
   || [[ -f "AndroidManifest.xml" ]] \
   || [[ -d "app/src/main" ]]; then
  types+=(android)
fi

# ── Flutter (同时带 ios/android 信号，单独标出便于精确 skill) ────────────
if [[ -f "pubspec.yaml" ]]; then
  types+=(flutter)
fi

# ── React Native (同时带 ios/android 信号) ─────────────────────────────
if [[ -f "package.json" ]] && grep -q '"react-native"' package.json 2>/dev/null; then
  types+=(react-native)
fi

# ── Web ────────────────────────────────────────────────────────────────
# 任一前端信号文件独立命中即判 web（各条件用 || 并列，不相互依赖 package.json）。
if [[ -f "package.json" ]] \
   || [[ -f "vite.config.ts" ]] || [[ -f "vite.config.js" ]] \
   || [[ -f "next.config.js" ]] || [[ -f "next.config.mjs" ]] \
   || [[ -f "angular.json" ]] \
   || [[ -f "index.html" ]]; then
  types+=(web)
fi

# ── Backend (语言级信号) ───────────────────────────────────────────────
# 注意: bash 中 && / || 同优先级左结合，绝不可写成
#   `A || B || C && grep ...` （会被解析为 (A||B||C) && grep）。
# 每个信号独立成行判断，避免优先级陷阱。
backend_signal=0
[[ -f "go.mod" ]] && backend_signal=1
[[ -f "requirements.txt" ]] && backend_signal=1
[[ -f "pyproject.toml" ]] && backend_signal=1
[[ -f "Pipfile" ]] && backend_signal=1
[[ -f "Cargo.toml" ]] && backend_signal=1
[[ -f "pom.xml" ]] && backend_signal=1
[[ -f "build.sbt" ]] && backend_signal=1
[[ -f "composer.json" ]] && backend_signal=1
[[ -f "Gemfile" ]] && backend_signal=1
# 额外：ruby 后端框架命中（不影响纯 Gemfile 已判 backend）
if [[ -f "Gemfile" ]] && grep -q 'rails\|sinatra\|hanami' Gemfile 2>/dev/null; then
  backend_signal=1
fi
[[ "${backend_signal}" -eq 1 ]] && types+=(backend)

if [[ ${#types[@]} -eq 0 ]]; then
  echo "unknown"
  exit 0
fi

# 去重并保持稳定顺序
printf '%s\n' "${types[@]}" | awk '!seen[$0]++' | paste -sd' ' -
