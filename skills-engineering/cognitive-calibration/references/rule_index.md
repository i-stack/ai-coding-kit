<!-- last-verified: 2026-08 -->
# 规则真值索引（cognitive-calibration）

> 本文件是 `cognitive-calibration` skill 规则 ID 的**唯一真值索引**。SKILL.md 声明的 ID 必须在此定义；此处 active 行必须被 SKILL.md 声明（双向一致，由 `validate_rule_ids.sh` 校验）。
>
> 元数据字段说明（机器可解析，非单 precedence 数字，因安全/时序/格式所有权是不同维度）：
> - `owner`：规则归属 skill
> - `scope`：global（全局）| platform（平台）
> - `phase`：evidence（证据）| structure（结构）| safety（安全）| timing（时序）
> - `precedence`：同 phase 内的数值优先级，越大越高
> - `conflicts_with`：可能冲突的规则 ID 列表
> - `merges_into`：可合并进的目标字段（避免块叠加）
> - `field_owner`：输出字段级所有权（多维裁决用）

| rule_id | owner | scope | phase | precedence | conflicts_with | merges_into | field_owner |
|---------|-------|-------|-------|------------|---------------|-------------|-------------|
| CAM-001 | cognitive-calibration | global | timing | 300 | [] | [] | {} |
| CAM-002 | cognitive-calibration | global | timing | 300 | [] | [] | {} |
| CAM-003 | cognitive-calibration | global | structure | 300 | [] | engineering-discipline.GR-004.why | {confidence: cognitive-calibration} |
| CAM-004 | cognitive-calibration | global | structure | 300 | [] | [] | {} |
| CAM-005 | cognitive-calibration | global | evidence | 300 | [] | epistemic-integrity.GR-011 | {confidence: cognitive-calibration} |

## 演进注意

- CAM-* 前缀即表达 owner = cognitive-calibration；`ios-engineer` 内的 CAM 引用经 `depends_on: [cognitive-calibration]` 依赖闭包可达，不依赖相对路径硬链接。
- 新增规则必须在此登记；退役 ID 必须同步删除 SKILL.md 内联引用（GC 校验见 `gc_evolution_history.sh`）。
