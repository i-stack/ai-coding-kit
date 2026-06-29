#!/usr/bin/env bash
# Auto-create .xcodebuildmcp/config.yaml if this is an iOS/macOS Xcode project

[ -f .xcodebuildmcp/config.yaml ] && exit 0

ws=$(find . -maxdepth 2 -name "*.xcworkspace" ! -path "*/Pods/*" 2>/dev/null | head -1)
[ -z "$ws" ] && exit 0

ws_name=$(basename "$ws")
scheme="${ws_name%.xcworkspace}-Debug"

mkdir -p .xcodebuildmcp
cat > .xcodebuildmcp/config.yaml << EOF
schemaVersion: 1

sessionDefaults:
  workspace: "${ws_name}"
  scheme: "${scheme}"
  configuration: "Debug"
  simulatorName: "iPhone 16"
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
