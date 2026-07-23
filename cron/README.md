# cron — 定时同步自动化

对齐 Hermes Agent 的 `cron/` 思路：把 `sync.sh` 注册为系统定时任务，实现「set-and-forget」配置同步与校验。

## 包含的脚本

| 文件 | 作用 |
|------|------|
| `run-sync.sh` | 定时执行体：运行 MCP 同步 + 技能同步 + preamble + 校验，日志写入 `~/.ai-coding-kit-cron/logs/`。仅当 `env/secrets.json` 存在时才真正同步。 |
| `install.sh` | 注册定时任务（macOS 默认 launchd，可用 `--cron` 改用 crontab）。 |
| `uninstall.sh` | 移除定时任务（launchd + crontab 一并清理）。 |

## 用法

```bash
# 默认每天 09:00（launchd，仅 macOS）
bash cron/install.sh

# 自定义时间：每天 03:30
bash cron/install.sh --hour 3 --minute 30

# 改用 crontab（非 macOS 或偏好 cron）
bash cron/install.sh --cron
bash cron/install.sh --cron --schedule "0 3 * * *"

# 卸载
bash cron/uninstall.sh
```

## 设计要点

- **不破坏既有守卫**：`run-sync.sh` 复用 `sync.sh` 与 `skills-engineering/scripts/*`，与 `pre-push` 钩子走同一套同步逻辑。
- **安全跳过**：缺少 `env/secrets.json` 时只记录 SKIP 日志，不报错、不写未解析的 `${...}` 占位符。
- **日志滚动**：保留最近 30 份执行日志，便于排查同步失败。
- **幂等注册**：`install.sh` 重复运行会先卸载旧代理再注册，避免重复条目。
