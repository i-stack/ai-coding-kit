#!/usr/bin/env bash
# List all registered skills in the skills-engineering repository.
# Outputs skill name, path, and description (from frontmatter).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== skills-engineering — 已注册技能 ==="
echo ""

format="  %-30s %-60s\n"
printf "$format" "SKILL" "DESCRIPTION"
printf "$format" "-----" "-----------"

for d in "${SE_DIR}"/*/; do
  skill_file="${d}SKILL.md"
  if [[ ! -f "$skill_file" ]]; then
    continue
  fi
  skill_name="$(basename "${d}")"

  # Extract description from YAML frontmatter
  description=""
  in_frontmatter=false
  while IFS= read -r line; do
    if [[ "$line" == "---" ]]; then
      if $in_frontmatter; then
        break
      else
        in_frontmatter=true
        continue
      fi
    fi
    if $in_frontmatter; then
      if [[ "$line" =~ ^description: ]]; then
        # Handle multi-line descriptions (with >- or >)
        if [[ "$line" =~ \>[-]?$ ]]; then
          # Multi-line: read the next line for content
          if IFS= read -r next_line; then
            description="${next_line#"${next_line%%[![:space:]]*}"}"
          fi
        else
          description="$(echo "$line" | sed 's/^description: *//')"
        fi
        break
      fi
    fi
  done < "$skill_file"

  # Truncate to 55 chars for display
  if [[ ${#description} -gt 55 ]]; then
    description="${description:0:52}..."
  fi

  printf "$format" "$skill_name" "$description"
done

echo ""
echo "Total: $(find "${SE_DIR}" -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ') skills"
echo ""
echo "运行 'cat <skill>/AGENT-BRIEF.md' 查看快速决策参考。"
echo "运行 'cat <skill>/SKILL.md' 查看完整规则。"
