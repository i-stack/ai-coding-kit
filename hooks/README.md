# hooks

项目级钩子脚本目录。

## xmcp-init.sh

自动检测当前目录是否为 Xcode 项目，如果是则创建 `.xcodebuildmcp/config.yaml` 配置文件。

```bash
bash hooks/xmcp-init.sh
```

脚本会：
- 检测 `.xcworkspace` 判断是否为 Xcode 项目
- 自动发现可用 iPhone 模拟器（优先 iPhone 16）
- 生成包含 workspace、scheme、simulator 名称/UDID 的 `config.yaml`

## 与 .githooks 的区别

| 目录 | 用途 |
|------|------|
| `hooks/` | 项目功能钩子脚本（如 xmcp 初始化） |
| [.githooks/](../.githooks/) | Git 钩子（pre-commit / pre-push 守卫） |
