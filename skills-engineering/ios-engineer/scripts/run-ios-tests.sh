#!/bin/bash
set -euo pipefail

# ============================================================
# iOS 单元测试执行脚本（自适应，可跨项目复用）
#
# 配置发现优先级：
#   1. 环境变量 WORKSPACE / SCHEME / SIMULATOR_NAME / SIMULATOR_ID（手动指定）
#   2. 项目内 .xcodebuildmcp/config.yaml（由 xmcp-init.sh 自动生成）
#   3. 自动发现（查找 .xcworkspace / .xcodeproj → xcodebuild -list
#      → 从 -showdestinations 选择与 scheme 匹配的 available Simulator）
#
# 用法:
#   ./run-ios-tests.sh                        # 跑全部测试
#   ./run-ios-tests.sh MyTestClass             # 只跑指定测试类
#   CLASS=MyTestClass ./run-ios-tests.sh       # 环境变量指定
#   WORKSPACE=MyApp.xcworkspace ./run-ios-tests.sh
#   SCHEME=MyScheme SIMULATOR_NAME="iPhone 16 Pro" ./run-ios-tests.sh
#
# 环境变量（均可选，覆盖自动发现）:
#   PROJECT_ROOT         项目根目录（默认脚本所在目录向上查找）
#   WORKSPACE            .xcworkspace 或 .xcodeproj 路径
#   SCHEME               Xcode scheme 名称
#   SIMULATOR_NAME       模拟器名称（可选；未指定时不写死型号）
#   SIMULATOR_ID         模拟器 UDID（最精确）
#   TEST_CLASS           测试类名
#   XCBEAUTIFY           是否使用 xcbeautify（默认自动检测）
# ============================================================

# --- 0. 确定项目根目录 ---
if [ -z "${PROJECT_ROOT:-}" ]; then
    PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
    # 向上查找包含 .xcodebuildmcp/config.yaml 或 .xcworkspace 的目录
    while [ "$PROJECT_ROOT" != "/" ]; do
        if [ -f "$PROJECT_ROOT/.xcodebuildmcp/config.yaml" ] || \
           ls "$PROJECT_ROOT"/*.xcworkspace >/dev/null 2>&1 || \
           ls "$PROJECT_ROOT"/*.xcodeproj >/dev/null 2>&1; then
            break
        fi
        PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
    done
    if [ "$PROJECT_ROOT" = "/" ]; then
        echo "❌ 未找到 iOS 项目根目录（无 .xcworkspace / .xcodeproj 或 .xcodebuildmcp/config.yaml）"
        echo "   请手动设置: PROJECT_ROOT=/path/to/project ./run-ios-tests.sh"
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
    WORKSPACE=$(find "$PROJECT_ROOT" -maxdepth 3 -name "*.xcworkspace" ! -path "*/Pods/*" ! -path "*.xcodeproj/*" 2>/dev/null | head -1)
fi
if [ -z "$WORKSPACE" ]; then
    WORKSPACE=$(find "$PROJECT_ROOT" -maxdepth 3 -name "*.xcodeproj" ! -path "*/Pods/*" 2>/dev/null | head -1)
fi
if [ -z "$WORKSPACE" ]; then
    echo "❌ 未找到 .xcworkspace 或 .xcodeproj"
    echo "   请手动设置: WORKSPACE=path/to/App.xcworkspace ./run-ios-tests.sh"
    exit 1
fi
XCB_FLAG="-workspace"
case "$WORKSPACE" in
    *.xcodeproj) XCB_FLAG="-project" ;;
esac
echo "📦 Container:   ${WORKSPACE} (${XCB_FLAG})"

# --- 3. 确定 scheme ---
SCHEME="${SCHEME:-}"
if [ -z "$SCHEME" ] && [ -n "${_yaml_scheme:-}" ]; then
    SCHEME="${_yaml_scheme}"
fi
if [ -z "$SCHEME" ]; then
    SCHEME=$(xcodebuild -list ${XCB_FLAG} "$WORKSPACE" 2>/dev/null | \
        awk '/Schemes:/{found=1; next} found && NF && !/^[[:space:]]*$/{print $1; exit}')
fi
if [ -z "$SCHEME" ]; then
    SCHEME=$(basename "$WORKSPACE" .xcworkspace)
    SCHEME=$(basename "$SCHEME" .xcodeproj)
fi
echo "🏗️  Scheme:      ${SCHEME}"

# --- 4. 确定 simulator ---
_show_destinations() {
    xcodebuild -showdestinations ${XCB_FLAG} "$WORKSPACE" -scheme "$SCHEME" 2>/dev/null || true
}

_parse_dest_fields() {
    local want_name="$1"
    local want_id="$2"
    awk -v want_name="$want_name" -v want_id="$want_id" '
        function trim(s) { gsub(/^ +| +$/, "", s); return s }
        {
            name = ""; id = ""; plat = ""
            if (match($0, /name:[^,}]+/)) name = trim(substr($0, RSTART+5, RLENGTH-5))
            if (match($0, /id:[A-Fa-f0-9-]+/)) id = substr($0, RSTART+3, RLENGTH-3)
            if (match($0, /platform:[^,}]+/)) plat = trim(substr($0, RSTART+9, RLENGTH-9))
            if (id == "") next
            if (want_id != "" && id != want_id) next
            if (want_name != "" && name != want_name) next
            print id "\t" name "\t" plat
        }'
}

_pick_row() {
    local rows="$1"
    local prefer_iphone="$2"
    if [ "$prefer_iphone" = "1" ]; then
        local iphone_row
        iphone_row=$(printf '%s\n' "$rows" | awk -F'\t' '$2 ~ /^iPhone/ { print; exit }')
        if [ -n "$iphone_row" ]; then
            printf '%s\n' "$iphone_row"
            return
        fi
    fi
    printf '%s\n' "$rows" | awk 'NF { print; exit }'
}

SIMULATOR_ID="${SIMULATOR_ID:-}"
SIMULATOR_NAME="${SIMULATOR_NAME:-}"
SIMULATOR_PLATFORM="${SIMULATOR_PLATFORM:-}"
if [ -z "$SIMULATOR_ID" ] && [ -n "${_yaml_udid:-}" ]; then
    SIMULATOR_NAME="${SIMULATOR_NAME:-${_yaml_sim:-}}"
    SIMULATOR_ID="${_yaml_udid}"
fi
if [ -z "$SIMULATOR_NAME" ] && [ -n "${_yaml_sim:-}" ]; then
    SIMULATOR_NAME="${_yaml_sim}"
fi

DEST_RAW=$(_show_destinations)
DEST_SIM_LINES=$(printf '%s\n' "$DEST_RAW" | grep '{' | grep 'Simulator' | grep 'id:' \
    | grep -v 'unavailable' | grep -v 'placeholder' \
    | grep -v 'Designed for' | grep -v 'macOS' || true)
DEST_ID_LINES=$(printf '%s\n' "$DEST_RAW" | grep '{' | grep 'id:' \
    | grep -v 'unavailable' | grep -v 'placeholder' \
    | grep -v 'Designed for' || true)

if [ -z "$SIMULATOR_ID" ]; then
    PICKED=$(_pick_row "$(_parse_dest_fields "$SIMULATOR_NAME" "" <<< "$DEST_SIM_LINES")" \
        "$([ -z "$SIMULATOR_NAME" ] && echo 1 || echo 0)")
    SIMULATOR_ID=$(printf '%s\n' "$PICKED" | awk -F'\t' 'NR==1 { print $1 }')
    SIMULATOR_NAME=$(printf '%s\n' "$PICKED" | awk -F'\t' 'NR==1 { print $2 }')
    SIMULATOR_PLATFORM=$(printf '%s\n' "$PICKED" | awk -F'\t' 'NR==1 { print $3 }')
fi

if [ -n "$SIMULATOR_ID" ] && { [ -z "$SIMULATOR_PLATFORM" ] || [ -z "$SIMULATOR_NAME" ]; }; then
    LOOKUP=$(_pick_row "$(_parse_dest_fields "" "$SIMULATOR_ID" <<< "$DEST_ID_LINES")" 0)
    if [ -n "$LOOKUP" ]; then
        if [ -z "$SIMULATOR_NAME" ]; then
            SIMULATOR_NAME=$(printf '%s\n' "$LOOKUP" | awk -F'\t' 'NR==1 { print $2 }')
        fi
        if [ -z "$SIMULATOR_PLATFORM" ]; then
            SIMULATOR_PLATFORM=$(printf '%s\n' "$LOOKUP" | awk -F'\t' 'NR==1 { print $3 }')
        fi
    fi
fi

if [ -z "$SIMULATOR_ID" ]; then
    echo "❌ 未找到与 scheme 匹配的 available Simulator destination${SIMULATOR_NAME:+: $SIMULATOR_NAME}"
    echo ""
    echo "   可用 destination:"
    printf '%s\n' "$DEST_RAW" | grep '{' | head -20 || true
    echo ""
    echo "   请指定 SIMULATOR_ID=<UDID> 或 SIMULATOR_NAME=<已安装模拟器名称>"
    echo "   不要改用 macOS destination 来跑 iOS/watchOS/tvOS 测试"
    exit 1
fi

if [ -n "$SIMULATOR_PLATFORM" ]; then
    DEST="platform=${SIMULATOR_PLATFORM},id=${SIMULATOR_ID}"
else
    DEST="id=${SIMULATOR_ID}"
fi
echo "📱 Destination: ${SIMULATOR_NAME:-unknown} (${SIMULATOR_ID}${SIMULATOR_PLATFORM:+, $SIMULATOR_PLATFORM})"

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
        ${XCB_FLAG} "${WORKSPACE}" \
        -scheme "${SCHEME}" \
        -destination "${DEST}" \
        ${TEST_FLAG:+"${TEST_FLAG}"} \
        test 2>&1 | xcbeautify --quiet --report junit
    EXIT_CODE=${PIPESTATUS[0]}
    set -e
else
    xcodebuild \
        ${XCB_FLAG} "${WORKSPACE}" \
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
