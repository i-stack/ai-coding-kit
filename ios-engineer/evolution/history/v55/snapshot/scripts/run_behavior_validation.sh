#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[behavior 1/5] Active snapshot consistency"
if [ "${SKIP_SNAPSHOT_CONSISTENCY:-0}" = "1" ]; then
  echo "Skipped (SKIP_SNAPSHOT_CONSISTENCY=1)"
else
  bash scripts/check_snapshot_consistency.sh
fi

echo "[behavior 2/5] Proposal script rejection paths"
bash scripts/test_proposal_scripts.sh

echo "[behavior 3/5] Repository template usability"
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

echo "[behavior 4/5] Code review output contract"
ruby <<'RUBY'
skill = File.read("SKILL.md")
review = File.read("references/review_checklists.md")
examples = File.read("references/examples.md")

unless skill.include?("代码审查 / PR Review 例外") &&
       skill.include?("findings-first") &&
       skill.include?("[review_checklists.md](references/review_checklists.md)")
  warn "SKILL.md no longer routes code review to findings-first review_checklists.md"
  exit 1
end

required_sections = ["审查结论", "严重问题", "一般问题", "验证缺口", "最终要求"]
missing = required_sections.reject { |section| review.include?(section) }
unless missing.empty?
  warn "review_checklists.md missing findings-first section(s): #{missing.join(', ')}"
  exit 1
end

if examples =~ /代码审查[\s\S]{0,300}根因\s*[-→>].*为什么\s*[-→>].*修法\s*[-→>].*验证/m
  warn "examples.md appears to redefine code review as root-cause four-step output"
  exit 1
end
RUBY

echo "[behavior 5/5] Network cache and error-modeling contract"
ruby <<'RUBY'
skill = File.read("SKILL.md")
network = File.read("references/networking_patterns.md")
domain = File.read("references/domain_modeling.md")
templates = File.read("references/code_templates.md")

unless skill.include?("请求失败 / 重试异常 / 鉴权刷新 / 分页重复或漏数据 / 缓存污染") &&
       skill.include?("[networking_patterns.md](references/networking_patterns.md)") &&
       skill.include?("错误建模追加 [domain_modeling.md](references/domain_modeling.md)")
  warn "SKILL.md no longer routes network/cache issues to networking_patterns.md plus domain_modeling.md"
  exit 1
end

unless network.include?("缓存模式") &&
       network.include?("必须定义缓存键") &&
       network.include?("不得让 ViewModel 直接感知缓存实现细节")
  warn "networking_patterns.md missing cache behavior constraints"
  exit 1
end

unless domain.include?("ErrorModel") &&
       domain.include?("传输错误") &&
       domain.include?("状态码错误") &&
       domain.include?("解码错误") &&
       domain.include?("鉴权错误") &&
       domain.include?("业务错误") &&
       domain.include?("展示错误")
  warn "domain_modeling.md missing ErrorModel layered error contract"
  exit 1
end

if templates.include?("try? cache.read") || templates.include?("try? cache.write")
  warn "code_templates.md regressed to silent cache errors"
  exit 1
end

unless templates.include?("缓存读失败不得压成单一 nil 分支") &&
       templates.include?("缓存写失败必须记录")
  warn "code_templates.md missing explicit cache failure behavior"
  exit 1
end
RUBY

echo "Behavior validation passed"
