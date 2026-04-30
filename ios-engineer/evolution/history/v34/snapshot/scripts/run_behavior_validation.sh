#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[behavior 1/3] Active snapshot consistency"
if [ "${SKIP_SNAPSHOT_CONSISTENCY:-0}" = "1" ]; then
  echo "Skipped (SKIP_SNAPSHOT_CONSISTENCY=1)"
else
  bash scripts/check_snapshot_consistency.sh
fi

echo "[behavior 2/3] Proposal script rejection paths"
bash scripts/test_proposal_scripts.sh

echo "[behavior 3/3] Repository template usability"
ruby <<'RUBY'
require "tmpdir"

content = File.read("references/code_templates.md")
section = content[/## Repository 模板.*?(?=\n## APIClient 模板)/m]
abort("Missing Repository template section") unless section

code = section[/```swift\n(.*?)\n```/m, 1]
abort("Missing Repository template Swift block") unless code

required_fragments = {
  "logger field" => "private let logger: LoggerProtocol",
  "logger init parameter" => "logger: LoggerProtocol",
  "logger assignment" => "self.logger = logger",
  "cache read logging" => "logger.error(\"cache read failed",
  "cache write logging" => "logger.error(\"cache write failed"
}

missing = required_fragments.select { |_label, text| !code.include?(text) }
unless missing.empty?
  missing.each { |label, _text| warn "Missing Repository template fragment: #{label}" }
  exit 1
end

if code.include?("try? cache.read") || code.include?("try? cache.write")
  warn "Repository template regressed to silent cache errors"
  exit 1
end

tmp = File.join(Dir.mktmpdir, "RepositoryTemplate.swift")
File.write(tmp, <<~SWIFT)
  import Foundation

  struct FeatureEntity {}

  protocol FeatureRemoteDataSourceProtocol {
      func fetch() async throws -> FeatureEntity
  }

  protocol FeatureCacheProtocol {
      func read() throws -> FeatureEntity?
      func write(_ entity: FeatureEntity) throws
  }

  protocol LoggerProtocol {
      func error(_ message: String)
  }

  #{code}
SWIFT

if system("command -v swiftc >/dev/null 2>&1")
  cache_dir = File.join(Dir.tmpdir, "ios-engineer-swift-module-cache")
  Dir.mkdir(cache_dir) unless Dir.exist?(cache_dir)
  unless system("swiftc", "-module-cache-path", cache_dir, "-typecheck", tmp)
    warn "Repository template Swift typecheck failed"
    exit 1
  end
else
  warn "swiftc not found; skipped Repository template typecheck after textual checks"
end
RUBY

echo "Behavior validation passed"
