#!/usr/bin/env bash
# Auto-create .xcodebuildmcp/config.yaml if this is an iOS/macOS Xcode project

[ -f .xcodebuildmcp/config.yaml ] && exit 0

ws=$(find . -maxdepth 2 -name "*.xcworkspace" ! -path "*/Pods/*" 2>/dev/null | head -1)
[ -z "$ws" ] && exit 0

ws_name=$(basename "$ws")
scheme="${ws_name%.xcworkspace}-Debug"

# Auto-discover first available iPhone simulator (prefer iPhone 16, fall back to newest available)
sim_info=$(xcrun simctl list devices available iPhone 2>/dev/null | grep -v "unavailable" | grep "iPhone 16" | head -1)
if [ -z "$sim_info" ]; then
    sim_info=$(xcrun simctl list devices available iPhone 2>/dev/null | grep -v "unavailable" | head -1)
fi

sim_name="iPhone 16"
sim_udid=""
if [ -n "$sim_info" ]; then
    sim_name=$(echo "$sim_info" | sed 's/ (.*//' | xargs)
    sim_udid=$(echo "$sim_info" | grep -oE '[A-F0-9]{8}-([A-F0-9]{4}-){3}[A-F0-9]{12}' | head -1)
fi

mkdir -p .xcodebuildmcp
if [ -n "$sim_udid" ]; then
cat > .xcodebuildmcp/config.yaml << EOF
schemaVersion: 1

sessionDefaults:
  workspace: "${ws_name}"
  scheme: "${scheme}"
  configuration: "Debug"
  simulatorName: "${sim_name}"
  simulatorUdid: "${sim_udid}"
  simulatorPlatform: "iOS Simulator"

incrementalBuildsEnabled: true
parallelTestingEnabled: true
dapRequestTimeoutMs: 60000

enabledWorkflows:
  - "simulator"
  - "ui-automation"

filePathRenderStyle: "tree"
showTestTiming: true
EOF
else
cat > .xcodebuildmcp/config.yaml << EOF
schemaVersion: 1

sessionDefaults:
  workspace: "${ws_name}"
  scheme: "${scheme}"
  configuration: "Debug"
  simulatorName: "${sim_name}"
  simulatorPlatform: "iOS Simulator"

incrementalBuildsEnabled: true
parallelTestingEnabled: true
dapRequestTimeoutMs: 60000

enabledWorkflows:
  - "simulator"
  - "ui-automation"

filePathRenderStyle: "tree"
showTestTiming: true
EOF
fi
