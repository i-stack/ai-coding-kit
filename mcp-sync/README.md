# mcp-sync

Single-source **`mcp-servers.json`** → sync MCP servers to **Cursor** (symlink), **OpenAI Codex** & **Xcode Coding Assistant** (TOML merge), and **Claude Code** / **Xcode Claude Agent** (JSON merge). Bash + Python.

以**一份** MCP 清单同步到 Cursor、Codex（终端与 Xcode 内）、Claude Code 与 Xcode Coding Intelligence，免去多端重复维护。

[![Bash](https://img.shields.io/badge/shell-bash-4EAA25?style=flat-square&logo=gnu-bash&logoColor=white)](https://www.gnu.org/software/bash/)
[![Python 3](https://img.shields.io/badge/Python-3-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-555555?style=flat-square)](https://github.com/i-stack/mcp-sync)
[![MCP](https://img.shields.io/badge/MCP-config-663399?style=flat-square)](https://modelcontextprotocol.io/)

[![Cursor](https://img.shields.io/badge/Cursor-mcp.json%20%E2%86%92%20%E4%BB%93%E5%BA%93-24292f?style=flat-square&logo=cursor&logoColor=white)](https://cursor.com)
[![Codex](https://img.shields.io/badge/Codex-%E7%BB%88%E7%AB%AF%20%C2%B7%20Xcode-10A37F?style=flat-square)](https://developers.openai.com/codex/)
[![Claude Code](https://img.shields.io/badge/Claude_Code-%E5%90%88%E5%B9%B6%20.claude.json-cc785c?style=flat-square)](https://www.anthropic.com/claude-code)
[![Xcode](https://img.shields.io/badge/Xcode-Coding%20Intelligence-147EFB?style=flat-square&logo=xcode&logoColor=white)](https://developer.apple.com/documentation/Xcode/setting-up-coding-intelligence)

**MCP 配置同步**：数据源为本仓库中的 `mcp-servers.json`（可由 `mcp-servers.json.example` 复制）；脚本负责 Cursor 符号链接、Codex TOML 合并、Claude JSON 合并及 Xcode Coding Assistant 相关路径（详见下方表格）。可选 Git 钩子：推送前自动执行 `sync_all.sh`。

| 项目 | 说明 |
|------|------|
| 工程名 | **mcp-sync** |
| 默认远程 | `https://github.com/i-stack/mcp-sync.git`（见下方「克隆」） |

## 功能概览

| 目标 | 同步方式 | 说明 |
|------|----------|------|
| **Cursor** | 符号链接 | `~/.cursor/mcp.json` → 本仓库的 `mcp-servers.json`，改源文件即生效 |
| **Codex（终端 / CLI）** | 生成 TOML + 合并 | 写入 `~/.codex/mcp.generated.toml`，并把 `[mcp_servers.*]` 合并进 `~/.codex/config.toml` 中带标记的区块，**不覆盖**你在该文件中的其他设置 |
| **Codex（Xcode 内）** | 同上 | 与上相同的生成与合并逻辑，写入 **`~/Library/Developer/Xcode/CodingAssistant/codex/`**（`mcp.generated.toml` + `config.toml`）。仅影响在 Xcode 里启动的 Codex，与 `~/.codex` 独立（见 Apple [Setting up coding intelligence](https://developer.apple.com/documentation/Xcode/setting-up-coding-intelligence)） |
| **Claude Code（终端）** | JSON 合并 | 将 `mcpServers` 合并进 `~/.claude.json`，**仅更新** MCP 相关键，其它配置保留 |
| **Claude Agent（Xcode 内）** | JSON 合并 | 将 `mcpServers` 合并进 **`~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json`**。Xcode 侧 MCP 挂在 **`projects` → 各工程路径 → `mcpServers`**：脚本会对**已有**的每个工程条目合并（同名 key 以仓库为准覆盖），其它键保留；若无 `projects` 则写入根级 `mcpServers` |

一次执行 `sync_all.sh` 即可完成：Cursor 软链 → Codex（含 Xcode 目录）→ Claude（含 Xcode 配置）。

### 在 Cursor / Codex / Claude 里怎么用

同步完成后，三端的 MCP **列表都来自同一份** `mcpServers`，只是落地路径不同；**无需**在每一处单独抄写 JSON。

| 客户端 | 配置落点（由脚本处理） | 你需要做的事 |
|--------|------------------------|--------------|
| **Cursor** | `~/.cursor/mcp.json` → 本仓库 `mcp-servers.json`（符号链接） | 打开 **Cursor → Settings → MCP**（或「Features / Model Context Protocol」），确认各服务器已列出；若列表未刷新，**完全退出并重开 Cursor**。对话里是否自动调用工具取决于模型与当前会话策略。 |
| **Codex（终端 CLI）** | `~/.codex/mcp.generated.toml` 合并进 `~/.codex/config.toml` | **重启**正在跑 Codex 的终端会话或进程，使新的 `[mcp_servers.*]` 生效。 |
| **Codex（Xcode 内）** | 同上逻辑，目录为 `~/Library/Developer/Xcode/CodingAssistant/codex/` | **重启 Xcode** 后再打开 Coding Assistant（与 Apple [Coding Intelligence](https://developer.apple.com/documentation/Xcode/setting-up-coding-intelligence) 说明一致）。 |
| **Claude Code（终端）** | `mcpServers` 合并进 `~/.claude.json` | **重启 Claude Code** 或新开会话，确保读取到新 MCP。 |
| **Claude Agent（Xcode 内）** | 合并进 `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json` | **重启 Xcode**；脚本对已有工程路径做按工程合并（详见上文表格）。 |

若某项 MCP 在本机启动失败（例如缺 Node、未装 Xcode）对应客户端里会显示错误；修好环境后重新运行 `./sync_all.sh` 并重启客户端即可。

### 当前清单里多出来的 MCP（相对 `mcp-servers.json.example`）

在示例模板之外，你还可以按需加入例如：

| 键名 | 作用 | 备注 |
|------|------|------|
| **`filesystem`** | `@modelcontextprotocol/server-filesystem`，由 MCP 访问本地目录 | `args` **最后一项**为允许访问的根路径；**只挂当前工程目录**，避免把整个 `$HOME` 交给模型。 |
| **`shell`** | `shell-mcp-server`，通过 MCP 执行 shell | **权限等价于你的登录用户能跑的终端**，见下文「Shell MCP 与安全」。 |
| **`XcodeBuildMCP`** | `xcodebuildmcp@latest`，驱动 Xcode / xcodebuild | 需 **macOS + Xcode 16.x + Node 18+**；官方客户端接入示例见 [MCP Clients](https://xcodebuildmcp.com/docs/clients)。配置里一般为 `npx -y xcodebuildmcp@latest mcp`。 |

另有 **`github`**（HTTP MCP，`url` + `Authorization: Bearer …`）等与示例里基于 `command` 的 GitHub MCP **不是同一种接法**，按需二选一即可，勿重复配置冲突。

## 环境要求

- macOS / Linux（需 `bash`）
- Python 3（用于 Codex / Claude 同步脚本）
- 使用 **Xcode 内 Codex / Claude Agent** 时需在 **macOS**，且 Xcode 已按 [Apple 文档](https://developer.apple.com/documentation/Xcode/setting-up-coding-intelligence) 在 Intelligence 中启用相应能力（配置目录为 `~/Library/Developer/Xcode/CodingAssistant/`）

## 克隆仓库

```bash
git clone https://github.com/i-stack/mcp-sync.git
cd mcp-sync
```

克隆后若要用 **Git 钩子** 在推送前自动同步，在外层 `ai-coding-kit/` 根目录执行一次 `bash install-hooks.sh`（详见下文）。

## 快速开始

1. 进入本仓库目录（克隆见上；本地文件夹名可自定）。

2. 准备本地配置（勿提交密钥）：

   ```bash
   cp mcp-servers.json.example mcp-servers.json
   ```

   编辑 `mcp-servers.json`，填入你的 Token、项目 ID 等。

   `mcpServers` 里每一项的**键名**由你自定，会在 Cursor / 客户端里作为该 MCP 的显示名；**建议按功能命名**（见 `mcp-servers.json.example`，如 `browser-automation`、`api-documentation`），不必与底层包名一致。

3. 执行同步：

   ```bash
   chmod +x sync_all.sh   # 仅需首次
   ./sync_all.sh
   ```

4. （可选）启用 **`pre-push` 钩子**：希望每次 `git push` 前先跑一遍同步时，在外层 `ai-coding-kit/` 根目录执行 `bash install-hooks.sh`。说明见下一节。

5. 重启或重新加载 **Cursor / Codex / Claude Code**（若当前会话未自动读取新配置）。若在 **Xcode** 中使用 Coding Assistant，建议**重启 Xcode** 后再试。

## Git 钩子（可选）

合并入 `ai-coding-kit` 后，钩子由仓库根目录统一管理（一个 git repo 只有一个 `core.hooksPath`，根级 `pre-push` 同时跑 skills-engineering 同步链与本目录的 `sync_all.sh`）。在 `git push` 把对象发往远程**之前**会自动调用 `sync_all.sh`，让 Cursor / Codex / Claude / Xcode 一侧的 MCP 配置先与本仓库对齐。

**说明：** Git 客户端只有与 push 相关的 **`pre-push`**，没有官方的 **`post-push`**（无法在「远端已接收完毕」后再用本地钩子跑脚本；若需要那种时机，只能用远端 bare 仓库的 `post-receive`、CI 等）。

**启用（每个克隆只做一次，在外层 `ai-coding-kit/` 根目录执行）：**

```bash
chmod +x sync_all.sh   # 若尚未可执行
cd <ai-coding-kit-root>
bash install-hooks.sh
```

该脚本会把外层仓库的 `core.hooksPath` 设为 `.githooks`，并为根级 `pre-commit` / `pre-push` 加上可执行权限。详见外层根 README 的「Git 钩子」章节。

**跳过单次钩子（仍会执行 push）：**

```bash
git push --no-verify
```

若 `sync_all.sh` 失败（例如 Python 报错），`pre-push` 会以非零退出码结束，**本次 push 会被 Git 中止**，便于先修好本机环境再推送。

## 脚本说明

| 文件 | 作用 |
|------|------|
| `sync_all.sh` | 一键：Cursor 软链 → `sync_mcp.py`（含 Xcode `codex` 目录）→ `sync_claude.py`（含 Xcode `ClaudeAgentConfig`） |
| `sync_mcp.py` | 生成 Codex 用 TOML，并合并进 `~/.codex/config.toml` 与 **`~/Library/Developer/Xcode/CodingAssistant/codex/config.toml`** |
| `sync_claude.py` | 将 `mcpServers` 合并进 `~/.claude.json` 与 **`~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json`**（Xcode 侧为按工程 `projects.*.mcpServers` 合并） |
| `mcp-servers.json` | **唯一数据源**（本地密钥文件；勿提交，忽略规则见仓库根 `.gitignore` 中的 `mcp-sync/mcp-servers.json`） |
| `mcp-servers.json.example` | 无密钥的模板，可安全提交到 Git |

> 仓库级 git 钩子由外层 `ai-coding-kit/install-hooks.sh` 统一注册；本目录不再持有独立的 `githooks/` 与 `install-hooks.sh`。根 `pre-push` 会在 push 前自动调用本目录的 `sync_all.sh`。

也可单独运行：

```bash
python3 sync_mcp.py
python3 sync_claude.py
```

单独执行 `sync_mcp.py` 时仍会更新 **本机 Codex** 与 **Xcode Codex** 目录下的 TOML / `config.toml`；单独执行 `sync_claude.py` 会更新 **`~/.claude.json`** 与 **Xcode 内** `.claude.json`。Cursor 需自行保证 `~/.cursor/mcp.json` 指向本仓库的 `mcp-servers.json`（或直接运行 `sync_all.sh`）。

## 蓝湖 MCP（可选）

`lanhu-mcp/` 为蓝湖相关 MCP 服务实现，需单独按目录内说明启动服务；`mcp-servers.json` 中通过 `url` 指向本地 HTTP 端点即可，与上述同步逻辑独立。

## Shell MCP 与安全（不要用过高权限）

本仓库若配置了 **`shell`**（`shell-mcp-server`）：

- 该 npm 包当前实现是对传入字符串做 **`exec`/bash**，**没有内置命令白名单、工作目录锁或沙箱**；模型一旦调用成功，效果接近「在你的账户下执行终端命令」。
- **不要把 shell MCP 当成「低权限工具」**：若不需要代理自动跑终端，请直接从 `mcp-servers.json` 删掉该项再同步，或在 Cursor MCP 设置里关闭该服务器。
- **想用 MCP 执行命令又不想全开**：优先换用 **自带命令允许列表** 的 shell 类 MCP（以具体包的 README 为准，常见形态为环境变量里的允许命令列表或正则白名单），并把列表收窄到 `git`、`npm test`、少量构建脚本等；仍建议定期审计日志。
- **系统层降级**（成本高）：用单独 macOS 用户、虚拟机或容器跑 MCP 进程，并缩小文件系统挂载范围；与 **`filesystem`** MCP 只暴露单个仓库目录的思路一致。
- **`filesystem`** 同理：`args` 里的路径越大，模型可读写的范围越大，尽量保持**最小目录**。

## 安全提示

- 勿将含真实 Token 的 `mcp-servers.json` 提交到远程仓库。
- 若密钥曾泄露，请在对应平台**轮换** Token。
