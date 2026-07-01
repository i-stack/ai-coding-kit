#!/bin/bash
set -euo pipefail

# ============================================================
# iOS 单元测试执行脚本（自适应，可跨项目复用）
#
# 配置发现优先级：
#   1. 环境变量 WORKSPACE / SCHEME / SIMULATOR_NAME（手动指定）
#   2. 项目内 .xcodebuildmcp/config.yaml（由 xmcp-init.sh 自动生成）
#   3. 自动发现（查找 .xcworkspace → xcodebuild -list → 默认模拟器）
#
# 用法:
#   ./run_ios_tests.sh                        # 跑全部测试
#   ./run_ios_tests.sh MyTestClass             # 只跑指定测试类
#   CLASS=MyTestClass ./run_ios_tests.sh       # 环境变量指定
#   WORKSPACE=MyApp.xcworkspace ./run_ios_tests.sh
#   SCHEME=MyScheme SIMULATOR_NAME="iPhone 16 Pro" ./run_ios_tests.sh
#
# 环境变量（均可选，覆盖自动发现）:
#   PROJECT_ROOT         项目根目录（默认脚本所在目录向上查找）
#   WORKSPACE            .xcworkspace 路径（相对于 PROJECT_ROOT 或绝对路径）
#   SCHEME               Xcode scheme 名称
#   SIMULATOR_NAME       模拟器名称（默认 "iPhone 16"）
#   TEST_CLASS           测试类名
#   XCBEAUTIFY           是否使用 xcbeautify（默认自动检测）
# ============================================================

# --- 0. 确定项目根目录 ---
if [ -z "${PROJECT_ROOT:-}" ]; then
    PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
    # 向上查找包含 .xcodebuildmcp/config.yaml 或 .xcworkspace 的目录
    while [ "$PROJECT_ROOT" != "/" ]; do
        if [ -f "$PROJECT_ROOT/.xcodebuildmcp/config.yaml" ] || \
           ls "$PROJECT_ROOT"/*.xcworkspace >/dev/null 2>&1; then
            break
        fi
        PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
    done
    if [ "$PROJECT_ROOT" = "/" ]; then
        echo "❌ 未找到 iOS 项目根目录（无 .xcworkspace 或 .xcodebuildmcp/config.yaml）"
        echo "   请手动设置: PROJECT_ROOT=/path/to/project ./run_ios_tests.sh"
        exit 1
    fi
fi

echo "📁 项目根目录: ${PROJECT_ROOT}"

# --- 1. 从 .xcodebuildmcp/config.yaml 读取配置 ---
_read_yaml_value() {
    local key="$1"
    local file="$2"
    grep "^[[:space:]]*${key}:" "$file" 2>/dev/null | head -1 | \
        sed 's/.*:[[:space:]]*"\(.*\)"/\1/' | sed "s/.*:[[:space:]]*'\(.*\)'/\1/" | \
        sed 's/.*:[[:space:]]*//' | tr -d '"'"'" || true
}

CONFIG_YAML="${PROJECT_ROOT}/.xcodebuildmcp/config.yaml"
if [ -f "$CONFIG_YAML" ]; then
    _yaml_ws="$(_read_yaml_value "workspace" "$CONFIG_YAML")"
    _yaml_scheme="$(_read_yaml_value "scheme" "$CONFIG_YAML")"
    _yaml_sim="$(_read_yaml_value "simulatorName" "$CONFIG_YAML")"
    _yaml_udid="$(_read_yaml_value "simulatorUdid" "$CONFIG_YAML")"
    _yaml_config="$(_read_yaml_value "configuration" "$CONFIG_YAML")"
    echo "📋 已读取 .xcodebuildmcp/config.yaml"
else
    _yaml_ws=""
    _yaml_scheme=""
    _yaml_sim=""
    _yaml_udid=""
    _yaml_config=""
fi

# --- 2. 确定 workspace ---
WORKSPACE="${WORKSPACE:-}"
if [ -z "$WORKSPACE" ] && [ -n "${_yaml_ws:-}" ]; then
    # config.yaml 中的 workspace 是相对于项目根目录的文件名
    if [ -f "${PROJECT_ROOT}/${_yaml_ws}" ]; then
        WORKSPACE="${PROJECT_ROOT}/${_yaml_ws}"
    fi
fi
if [ -z "$WORKSPACE" ]; then
    WORKSPACE=$(find "$PROJECT_ROOT" -maxdepth 3 -name "*.xcworkspace" ! -path "*/Pods/*" 2>/dev/null | head -1)
fi
if [ -z "$WORKSPACE" ]; then
    echo "❌ 未找到 .xcworkspace 文件"
    echo "   请手动设置: WORKSPACE=path/to/App.xcworkspace ./run_ios_tests.sh"
    exit 1
fi
echo "📦 Workspace:   ${WORKSPACE}"

# --- 3. 确定 scheme ---
SCHEME="${SCHEME:-}"
if [ -z "$SCHEME" ] && [ -n "${_yaml_scheme:-}" ]; then
    SCHEME="${_yaml_scheme}"
fi
if [ -z "$SCHEME" ]; then
    # 从 xcodebuild -list 获取第一个 scheme
    SCHEME=$(xcodebuild -list -workspace "$WORKSPACE" 2>/dev/null | \
        awk '/Schemes:/{found=1; next} found && NF && !/^[[:space:]]*$/{print $1; exit}')
fi
if [ -z "$SCHEME" ]; then
    # 回退：从 workspace 名称推导
    SCHEME=$(basename "$WORKSPACE" .xcworkspace)
fi
echo "🏗️  Scheme:      ${SCHEME}"

# --- 4. 确定 simulator ---
SIMULATOR_ID="${SIMULATOR_ID:-}"
if [ -z "$SIMULATOR_ID" ] && [ -n "${_yaml_udid:-}" ]; then
    # 优先使用 config.yaml 中的 simulatorUdid（最精确）
    SIMULATOR_NAME="${_yaml_sim}"
    SIMULATOR_ID="${_yaml_udid}"
fi
if [ -z "$SIMULATOR_ID" ]; then
    SIMULATOR_NAME="${SIMULATOR_NAME:-}"
    if [ -z "$SIMULATOR_NAME" ] && [ -n "${_yaml_sim:-}" ]; then
        SIMULATOR_NAME="${_yaml_sim}"
    fi
    if [ -z "$SIMULATOR_NAME" ]; then
        SIMULATOR_NAME="iPhone 16"
    fi
    # 按名称查找 UDID
    SIMULATOR_ID=$(xcrun simctl list devices available iPhone 2>/dev/null | \
        grep "$SIMULATOR_NAME" | grep -v "unavailable" | head -1 | \
        grep -oE '[A-F0-9]{8}-([A-F0-9]{4}-){3}[A-F0-9]{12}' || true)
fi

if [ -z "$SIMULATOR_ID" ]; then
    echo "❌ 未找到可用模拟器: ${SIMULATOR_NAME:-unknown}"
    echo ""
    echo "   可用 iPhone 模拟器:"
    xcrun simctl list devices available iPhone 2>/dev/null | grep -v "unavailable" | head -15 || true
    echo ""
    echo "   请手动指定: SIMULATOR_ID=<UDID> ./run_ios_tests.sh"
    echo "   或: SIMULATOR_NAME=\"iPhone 16 Pro\" ./run_ios_tests.sh"
    exit 1
fi

DEST="platform=iOS Simulator,id=${SIMULATOR_ID}"
echo "📱 Simulator:   ${SIMULATOR_NAME} (${SIMULATOR_ID})"

# --- 5. 确定测试类 ---
TEST_CLASS="${1:-${CLASS:-}}"
if [ -n "${TEST_CLASS:-}" ]; then
    TEST_FLAG="-only-testing:${SCHEME}Tests/${TEST_CLASS}"
    echo "🧪 Test Class:  ${TEST_CLASS}"
else
    TEST_FLAG=""
    echo "🧪 Test Class:  ALL"
fi

# --- 6. 检测 xcbeautify ---
XCBEAUTIFY="${XCBEAUTIFY:-}"
if [ -z "$XCBEAUTIFY" ]; then
    if command -v xcbeautify &>/dev/null; then
        XCBEAUTIFY="true"
    else
        XCBEAUTIFY="false"
    fi
fi

# --- 7. 执行测试 ---
echo ""
echo "========================================"
echo "🚀 开始执行测试..."
echo "========================================"
echo ""

if [ "$XCBEAUTIFY" = "true" ]; then
    set +e
    xcodebuild \
        -workspace "${WORKSPACE}" \
        -scheme "${SCHEME}" \
        -destination "${DEST}" \
        ${TEST_FLAG:+"${TEST_FLAG}"} \
        test 2>&1 | xcbeautify --quiet --report junit
    EXIT_CODE=${PIPESTATUS[0]}
    set -e
else
    xcodebuild \
        -workspace "${WORKSPACE}" \
        -scheme "${SCHEME}" \
        -destination "${DEST}" \
        ${TEST_FLAG:+"${TEST_FLAG}"} \
        test
    EXIT_CODE=$?
fi

echo ""
echo "========================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 测试通过"
else
    echo "❌ 测试失败 (exit code: $EXIT_CODE)"
fi
echo "========================================"

exit $EXIT_CODE
