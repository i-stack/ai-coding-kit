#!/usr/bin/env python3
"""
ios-engineer 去重分析工具
步骤1: 对每个文件提取逻辑指纹
步骤2: 汇总后对比相似度，定位重复逻辑
"""

import os
import re
import json
import hashlib
import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

DEFAULT_ROOT = os.getcwd()
ROOT = DEFAULT_ROOT
OUTPUT = os.path.join(os.getcwd(), ".analysis_output")

# ---- 配置 ----
SKIP_DIRS = {
    "evolution/history", "evolution/proposals", "evolution/approvals",
    "evolution/validations", "evolution/scenarios", ".analysis_output",
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build"
}
NOISY_FUNCTION_NAMES = {"usage"}
MIN_FUNCTION_BODY_LINES = 4
MIN_BLOCK_LINES = 8
MIN_MARKDOWN_PARAGRAPH_CHARS = 120

# ---- 工具函数 ----

def relpath(p):
    return os.path.relpath(p, ROOT)

def directory_label(path):
    label = os.path.basename(os.path.abspath(path)) or "root"
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', label).strip('_') or "target"

def configure_paths(target_root, output_dir=None):
    """Set the analysis root and output directory for one run."""
    global ROOT, OUTPUT
    ROOT = os.path.abspath(target_root)
    OUTPUT = (
        os.path.abspath(output_dir)
        if output_dir
        else os.path.join(os.getcwd(), ".analysis_output", directory_label(ROOT))
    )
    os.makedirs(OUTPUT, exist_ok=True)
    return ROOT, OUTPUT

def should_skip(path):
    norm_parts = os.path.normpath(path).split(os.sep)
    for d in SKIP_DIRS:
        d_parts = d.split('/')
        n = len(d_parts)
        for i in range(len(norm_parts) - n + 1):
            if norm_parts[i:i + n] == d_parts:
                return True
    return False

def sha256(content):
    return hashlib.sha256(content.encode()).hexdigest()

def extract_ids(text):
    """提取 IR-001, ROUTE-001 等规则ID"""
    return set(re.findall(r'\b[A-Z]{2,6}-\d{3,4}\b', text))

def extract_functions(text):
    """提取 shell 函数名"""
    funcs = re.findall(r'^\s*(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)', text, re.MULTILINE)
    return set(funcs)

@dataclass(frozen=True)
class ShellFunction:
    name: str
    start_line: int
    end_line: int
    body: str
    normalized_body: str

    @property
    def body_hash(self):
        return sha256(self.normalized_body)

    @property
    def body_lines(self):
        return len([line for line in self.normalized_body.split('\n') if line])

def normalize_shell_line(line, generalize=False):
    """归一化 shell 逻辑行，保留命令结构但降低变量名和字符串造成的噪声。"""
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        return ""
    stripped = re.sub(r'\s+#.*$', '', stripped)
    if generalize:
        stripped = re.sub(r'"(?:\\.|[^"\\])*"', '"STR"', stripped)
        stripped = re.sub(r"'(?:\\.|[^'\\])*'", "'STR'", stripped)
        stripped = re.sub(r'\$\{?[A-Za-z_][A-Za-z0-9_]*\}?', '$VAR', stripped)
        stripped = re.sub(r'\b[A-Za-z_][A-Za-z0-9_]*=', 'VAR=', stripped)
        stripped = re.sub(r'\bfor\s+[A-Za-z_][A-Za-z0-9_]*\s+in\b', 'for VAR in', stripped)
    stripped = re.sub(r'\s+', ' ', stripped)
    return stripped

def normalize_shell_logic(text):
    lines = [normalize_shell_line(line, generalize=True) for line in text.split('\n')]
    return '\n'.join(line for line in lines if line)

def extract_shell_functions(text):
    """提取 shell 函数体，用于比较函数内部逻辑而不是只比较函数名。"""
    lines = text.splitlines()
    functions = []
    i = 0
    header_re = re.compile(r'^\s*(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)\s*\{?\s*$')

    while i < len(lines):
        match = header_re.match(lines[i])
        if not match:
            i += 1
            continue

        name = match.group(1)
        start = i
        body_start = i + 1
        brace_depth = lines[i].count('{') - lines[i].count('}')

        if brace_depth == 0:
            while body_start < len(lines) and not lines[body_start].strip():
                body_start += 1
            if body_start < len(lines) and lines[body_start].strip() == "{":
                brace_depth = 1
                body_start += 1
            else:
                i += 1
                continue

        j = body_start
        while j < len(lines):
            brace_depth += lines[j].count('{') - lines[j].count('}')
            if brace_depth <= 0:
                body = '\n'.join(lines[body_start:j])
                normalized = normalize_shell_logic(body)
                functions.append(ShellFunction(name, start + 1, j + 1, body, normalized))
                break
            j += 1
        i = max(j + 1, i + 1)

    return functions

def extract_sections(text):
    """提取 markdown 章节标题"""
    sections = re.findall(r'^#{1,4}\s+(.+)', text, re.MULTILINE)
    return set(s.strip().lower() for s in sections)

def extract_shell_patterns(text):
    """提取区分度高的 shell 组合模式（排除过于通用的）"""
    # 更具体的模式：命令+标志组合、特定工具调用
    patterns = [
        r'jq\s+(-r\s+)?\.',           # jq 数据提取
        r'curl\s+-[sS]',              # curl 静默请求
        r'find\s+.*-newer',           # find 按时间
        r'sed\s+-i',                  # sed 原地修改
        r'grep\s+-[qci]',             # grep 静默/计数/忽略大小写
        r'mktemp\s+-d',               # 临时目录
        r'readonly\s+\w+',            # 只读变量
        r'trap\s+',                   # 信号捕获
        r'set\s+-[eu]',               # 安全检查
        r'pushd\s+|popd',             # 目录栈
        r'diff\s+-[ru]',              # diff 对比
        r'git\s+log\s+',              # git log
        r'git\s+diff\s+',             # git diff
        r'git\s+show\s+',             # git show
        r'date\s+\+%',                # 日期格式化
        r'basename\s+\$\{?',          # basename
        r'dirname\s+\$\{?',           # dirname
        r'read\s+-r\s+',              # read -r 安全读取
        r'sort\s+-[tnk]',             # sort 字段排序
        r'uniq\s+-[cd]',              # uniq 计数/重复
        r'cut\s+-d[= ]+-f',           # cut 分隔取列
        r'tee\s+-a',                  # tee 追加
        r'shopt\s+-s',                # bash 选项
        r'source\s+|\.\s+\$\{?',      # source/import
        r'python3\s+-c\s+',           # python 内联
    ]
    # 用模式索引而非匹配文本，确保同类模式跨文件可正确命中
    found = set()
    for i, p in enumerate(patterns):
        if re.search(p, text):
            found.add(i)
    return found

def jaccard(set1, set2):
    if not set1 and not set2:
        return 0.0
    inter = len(set1 & set2)
    union = len(set1 | set2)
    return round(inter / union * 100, 1) if union > 0 else 0.0

def normalize_text(text):
    """归一化文本：去注释、去空行、去首尾空白（保留行顺序）"""
    lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            lines.append(stripped)
    return '\n'.join(lines)

def normalize_markdown_paragraph(text):
    text = re.sub(r'`[^`]+`', '`CODE`', text)
    text = re.sub(r'\b[A-Z]{2,6}-\d{3,4}\b', 'RULE-ID', text)
    text = re.sub(r'\s+', ' ', text.strip().lower())
    return text

def extract_markdown_paragraphs(text):
    paragraphs = []
    current = []
    start_line = 1
    in_fence = False

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            if current:
                paragraphs.append((start_line, '\n'.join(current)))
                current = []
            continue
        if in_fence:
            continue
        if not stripped or stripped.startswith('#') or stripped.startswith('|'):
            if current:
                paragraphs.append((start_line, '\n'.join(current)))
                current = []
            continue
        if not current:
            start_line = lineno
        current.append(stripped)

    if current:
        paragraphs.append((start_line, '\n'.join(current)))

    return [
        (line, para, normalize_markdown_paragraph(para))
        for line, para in paragraphs
        if len(normalize_markdown_paragraph(para)) >= MIN_MARKDOWN_PARAGRAPH_CHARS
    ]

def extract_repeated_blocks(fps, block_size=MIN_BLOCK_LINES):
    """查找跨文件重复的连续逻辑块，报告完整匹配而不是单行巧合。"""
    block_index = defaultdict(list)

    for fp in fps:
        if fp.ext != '.sh':
            continue
        norm_lines = [line for line in (normalize_shell_line(l) for l in fp.content.splitlines()) if line]
        if len(norm_lines) < block_size:
            continue
        for idx in range(0, len(norm_lines) - block_size + 1):
            block = tuple(norm_lines[idx:idx + block_size])
            block_index[sha256('\n'.join(block))].append((fp.rel, idx + 1, block))

    repeated = []
    for _hash, occurrences in block_index.items():
        files = {rel for rel, _line, _block in occurrences}
        if len(files) < 2:
            continue
        sample = occurrences[0][2]
        repeated.append({
            "files": sorted(files),
            "occurrences": occurrences,
            "lines": len(sample),
            "sample": sample,
        })

    repeated.sort(key=lambda item: (-len(item["files"]), -len(item["occurrences"]), item["files"]))
    return repeated

def select_representative_blocks(repeated_blocks, max_per_file_set=1):
    selected = []
    counts = defaultdict(int)
    for item in repeated_blocks:
        key = tuple(item["files"])
        if counts[key] >= max_per_file_set:
            continue
        selected.append(item)
        counts[key] += 1
    return selected

# ---- 步骤1: 提取每个文件的指纹 ----

class FileFingerprint:
    def __init__(self, path):
        self.path = path
        self.rel = relpath(path)
        self.ext = os.path.splitext(path)[1]
        self.size = os.path.getsize(path)
        self.mtime = os.path.getmtime(path)

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            self.content = f.read()

        self.lines = self.content.count('\n') + 1
        self.ids = extract_ids(self.content)
        self.functions = extract_functions(self.content)
        self.shell_functions = extract_shell_functions(self.content) if self.ext == '.sh' else []
        self.sections = extract_sections(self.content)
        self.shell_patterns = extract_shell_patterns(self.content)

        # 归一化内容哈希（用于检测完全相同）
        self.normalized = normalize_text(self.content)
        self.norm_hash = sha256(self.normalized)

    def to_dict(self):
        return {
            "rel": self.rel,
            "ext": self.ext,
            "size": self.size,
            "lines": self.lines,
            "ids": sorted(self.ids),
            "functions": sorted(self.functions),
            "function_bodies": [
                {
                    "name": func.name,
                    "start_line": func.start_line,
                    "end_line": func.end_line,
                    "body_lines": func.body_lines,
                    "body_hash": func.body_hash[:16],
                }
                for func in self.shell_functions
            ],
            "sections": sorted(self.sections),
            "shell_patterns": sorted(self.shell_patterns),
            "norm_hash": self.norm_hash[:16]
        }


def step1_collect(target_dir, label):
    """收集目标目录内所有文件的指纹"""
    fingerprints = []
    count = 0
    for root, dirs, files in os.walk(target_dir):
        # 过滤不需要的目录
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(root, d))]
        for fname in files:
            if fname.startswith('.') or fname == "analyze_duplication.sh":
                continue
            if fname.endswith(('.md', '.sh')):
                fpath = os.path.join(root, fname)
                if should_skip(fpath):
                    continue
                try:
                    fp = FileFingerprint(fpath)
                    fingerprints.append(fp)
                    count += 1
                except Exception as e:
                    print(f"  [SKIP] {relpath(fpath)}: {e}")

    # 保存指纹
    safe_label = re.sub(r'[^A-Za-z0-9_.-]+', '_', label).strip('_') or "target"
    out_file = os.path.join(OUTPUT, f"{safe_label}_fingerprints.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump([fp.to_dict() for fp in fingerprints], f, indent=2, ensure_ascii=False)
    print(f"  [OK] {label}: {count} 个文件 → {out_file}")
    return fingerprints

def collect_target_fingerprints(target_root):
    """Collect all active markdown and shell files under the configured root."""
    fingerprints = []
    for root, dirs, files in os.walk(target_root):
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(root, d))]
        for fname in files:
            if fname.startswith('.') or fname == "analyze_duplication.sh":
                continue
            if not fname.endswith(('.md', '.sh')):
                continue
            fpath = os.path.join(root, fname)
            if should_skip(fpath):
                continue
            try:
                fingerprints.append(FileFingerprint(fpath))
            except Exception as e:
                print(f"  [SKIP] {relpath(fpath)}: {e}")
    return fingerprints


# ---- 步骤2: 对比去重 ----

def step2_analyze(all_fps, report_path):
    """对比分析所有指纹，生成报告"""
    lines = []
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    lines.append(f"# 去重分析报告")
    lines.append(f"# 生成时间: {ts}")
    lines.append(f"# 目标目录: {ROOT}")
    lines.append(f"# 分析范围: {len(all_fps)} 个活跃文件")
    lines.append("")

    sh_fps = [fp for fp in all_fps if fp.ext == '.sh']
    md_fps = [fp for fp in all_fps if fp.ext == '.md']

    # ========================================
    # 一、完全相同文件检测（基于内容哈希）
    # ========================================
    lines.append("## 一、完全相同文件检测 (内容哈希)")
    lines.append("")

    hash_groups = defaultdict(list)
    for fp in all_fps:
        hash_groups[fp.norm_hash].append(fp)

    dups_found = 0
    for h, group in hash_groups.items():
        if len(group) > 1:
            dups_found += 1
            lines.append(f"### 重复组 #{dups_found} (哈希: `{h[:16]}...`)")
            for fp in group:
                lines.append(f"- `{fp.rel}` ({fp.lines} 行, {fp.size:,} bytes)")
            lines.append("")

    if dups_found == 0:
        lines.append("✅ 未发现完全相同的文件。")
    else:
        lines.append(f"⚠️ 发现 {dups_found} 组完全相同文件。")
    lines.append("")

    # ========================================
    # 二、Shell 脚本重复函数检测
    # ========================================
    lines.append("## 二、Shell 脚本重复函数检测")
    lines.append("")

    func_files = defaultdict(list)
    for fp in sh_fps:
        for func in fp.functions:
            func_files[func].append(fp.rel)

    dups = {
        k: v for k, v in func_files.items()
        if len(v) > 1 and k not in NOISY_FUNCTION_NAMES
    }
    noisy_dups = {
        k: v for k, v in func_files.items()
        if len(v) > 1 and k in NOISY_FUNCTION_NAMES
    }
    if dups:
        lines.append("| 函数名 | 出现文件 | 次数 |")
        lines.append("|--------|----------|------|")
        for func in sorted(dups.keys()):
            files = ", ".join(dups[func])
            lines.append(f"| `{func}()` | {files} | {len(dups[func])} |")
        lines.append("")
        lines.append(f"共 {len(dups)} 个函数在多个脚本中重复定义。")
        lines.append("")
        lines.append("💡 **建议**: 考虑抽取到公共 helper，或保留在调用脚本内并加交叉测试。")
    else:
        lines.append("✅ 未发现需要审查的重复函数名。")
    if noisy_dups:
        lines.append("")
        lines.append("以下常见 CLI 辅助函数已降噪，不作为抽公共库建议：")
        for func in sorted(noisy_dups.keys()):
            lines.append(f"- `{func}()` → {', '.join(noisy_dups[func])}")
    lines.append("")

    # ========================================
    # 三、Shell 函数体重复检测
    # ========================================
    lines.append("## 三、Shell 函数体重复检测 (归一化后)")
    lines.append("")
    lines.append("比较函数体内容，忽略注释、空行、变量名和字符串字面量差异；用于发现同逻辑不同函数名。")
    lines.append("")

    body_groups = defaultdict(list)
    for fp in sh_fps:
        for func in fp.shell_functions:
            if func.name in NOISY_FUNCTION_NAMES or func.body_lines < MIN_FUNCTION_BODY_LINES:
                continue
            body_groups[func.body_hash].append((fp, func))

    function_body_dups = [
        group for group in body_groups.values()
        if len({fp.rel for fp, _func in group}) > 1
    ]
    function_body_dups.sort(key=lambda group: (-len(group), group[0][0].rel))

    if function_body_dups:
        lines.append("| 函数体 | 出现位置 | 行数 |")
        lines.append("|--------|----------|------|")
        for index, group in enumerate(function_body_dups[:30], start=1):
            locations = ", ".join(
                f"`{fp.rel}:{func.start_line}` `{func.name}()`"
                for fp, func in group
            )
            lines.append(f"| 重复函数体 #{index} | {locations} | {group[0][1].body_lines} |")
        lines.append("")
        lines.append(f"共 {len(function_body_dups)} 组函数体重复候选。")
    else:
        lines.append("✅ 未发现归一化函数体重复。")
    lines.append("")

    # ========================================
    # 四、Shell 连续代码块重复检测
    # ========================================
    lines.append(f"## 四、Shell 连续代码块重复检测 (≥{MIN_BLOCK_LINES} 行)")
    lines.append("")
    lines.append("比较跨文件连续逻辑块，适合发现锁、校验、参数解析等被复制的片段。")
    lines.append("")

    repeated_blocks = extract_repeated_blocks(sh_fps, MIN_BLOCK_LINES)
    representative_blocks = select_representative_blocks(repeated_blocks)
    if representative_blocks:
        lines.append("| 重复块 | 出现文件 | 示例 |")
        lines.append("|--------|----------|------|")
        for idx, item in enumerate(representative_blocks[:30], start=1):
            files = ", ".join(f"`{file}`" for file in item["files"])
            sample = "<br>".join(item["sample"][:3])
            lines.append(f"| 代码块 #{idx} ({item['lines']} 行) | {files} | `{sample}` |")
        lines.append("")
        lines.append(f"共 {len(repeated_blocks)} 组原始连续代码块候选，展示 {len(representative_blocks)} 组按文件集合去重后的代表候选。")
    else:
        lines.append("✅ 未发现跨文件连续代码块重复。")
    lines.append("")

    # ========================================
    # 五、Shell 脚本相似度矩阵
    # ========================================
    lines.append("## 五、Shell 脚本特定模式相似度 (候选信号，≥50%，≥3个模式)")
    lines.append("")
    lines.append("基于高区分度的 shell 模式（jq/curl/git/diff/trap 等），至少匹配3个模式才比较")
    lines.append("")

    sh_pairs = []
    for i in range(len(sh_fps)):
        for j in range(i + 1, len(sh_fps)):
            fp1, fp2 = sh_fps[i], sh_fps[j]
            # 基于函数名 + shell模式 的综合相似度
            f1 = fp1.functions | fp1.shell_patterns
            f2 = fp2.functions | fp2.shell_patterns
            # 至少一方有 ≥3 个模式才比较，避免"都只有set -eu"这种误报
            if len(f1) < 3 and len(f2) < 3:
                continue
            sim = jaccard(f1, f2)
            if sim >= 50:
                sh_pairs.append((sim, fp1, fp2))

    sh_pairs.sort(key=lambda x: x[0], reverse=True)

    if sh_pairs:
        lines.append("| 文件A | 文件B | 相似度 |")
        lines.append("|-------|-------|--------|")
        for sim, fp1, fp2 in sh_pairs[:50]:  # Top 50
            lines.append(f"| `{fp1.rel}` | `{fp2.rel}` | **{sim}%** |")
        lines.append("")
        lines.append(f"共 {len(sh_pairs)} 对脚本特定模式相似度 ≥ 50%。")
    else:
        lines.append("✅ 未发现指纹相似度 ≥ 50% 的脚本对。")
    lines.append("")

    # ========================================
    # 六、Shell 脚本内容相似度
    # ========================================
    lines.append("## 六、Shell 脚本内容行相似度 (≥60%)")
    lines.append("")

    # 基于归一化行集合的 Jaccard
    content_pairs = []
    for i in range(len(sh_fps)):
        for j in range(i + 1, len(sh_fps)):
            fp1, fp2 = sh_fps[i], sh_fps[j]
            lines1 = set(fp1.normalized.split('\n'))
            lines2 = set(fp2.normalized.split('\n'))
            sim = jaccard(lines1, lines2)
            if sim >= 60:
                content_pairs.append((sim, fp1, fp2))

    content_pairs.sort(key=lambda x: x[0], reverse=True)

    if content_pairs:
        lines.append("| 文件A | 文件B | 行相似度 |")
        lines.append("|-------|-------|----------|")
        for sim, fp1, fp2 in content_pairs[:30]:
            lines.append(f"| `{fp1.rel}` | `{fp2.rel}` | **{sim}%** |")
        lines.append("")
        lines.append(f"共 {len(content_pairs)} 对脚本内容行相似度 ≥ 60%。")
    else:
        lines.append("✅ 未发现内容行相似度 ≥ 60% 的脚本对。")
    lines.append("")

    # ========================================
    # 七、脚本工具链指纹对比
    # ========================================
    lines.append("## 七、脚本工具链指纹对比 (候选信号，≥80%)")
    lines.append("")
    lines.append("检测使用相同外部工具链的脚本（高相似度暗示类似架构）：")
    lines.append("")

    # 提取每个脚本使用的外部命令
    def extract_tools(text):
        tools = set()
        # 常见 Unix 工具和自定义命令
        candidate = re.findall(
            r'\b(jq|curl|find|sed|grep|awk|cut|sort|uniq|xargs|tee|diff|comm|'
            r'git|python3|mktemp|readlink|realpath|shasum|md5|'
            r'pushd|popd|source|dirname|basename|read|trap|'
            r'cat|head|tail|wc|tr|date)\b', text
        )
        return set(c.lower() for c in candidate)

    tool_pairs = []
    for i in range(len(sh_fps)):
        for j in range(i + 1, len(sh_fps)):
            fp1, fp2 = sh_fps[i], sh_fps[j]
            t1 = extract_tools(fp1.content)
            t2 = extract_tools(fp2.content)
            sim = jaccard(t1, t2)
            if sim >= 80:
                tool_pairs.append((sim, fp1, fp2, t1 & t2))

    tool_pairs.sort(key=lambda x: x[0], reverse=True)

    if tool_pairs:
        lines.append("| 文件A | 文件B | 工具链相似度 | 共用工具 |")
        lines.append("|-------|-------|-------------|----------|")
        for sim, fp1, fp2, common_tools in tool_pairs[:20]:
            tools_str = ", ".join(sorted(common_tools)[:8])
            if len(common_tools) > 8:
                tools_str += f" ... (+{len(common_tools)-8})"
            lines.append(f"| `{fp1.rel}` | `{fp2.rel}` | **{sim}%** | {tools_str} |")
        lines.append("")
        lines.append(f"共 {len(tool_pairs)} 对脚本使用高度相似的工具链。")
        lines.append("")
        lines.append("💡 工具链高度重合的脚本可能适合合并或抽取公共模块。")
    else:
        lines.append("✅ 未发现工具链相似度 ≥ 80% 的脚本对。")
    lines.append("")

    # ========================================
    # 八、Markdown 段落级重复检测
    # ========================================
    lines.append(f"## 八、Markdown 段落级重复检测 (≥{MIN_MARKDOWN_PARAGRAPH_CHARS} 字符)")
    lines.append("")
    lines.append("比较跨文件长段落，排除标题、表格和代码块；用于发现规则正文被复制。")
    lines.append("")

    paragraph_groups = defaultdict(list)
    for fp in md_fps:
        for line, para, normalized in extract_markdown_paragraphs(fp.content):
            paragraph_groups[sha256(normalized)].append((fp.rel, line, para))

    paragraph_dups = [
        group for group in paragraph_groups.values()
        if len({rel for rel, _line, _para in group}) > 1
    ]
    paragraph_dups.sort(key=lambda group: (-len(group), group[0][0], group[0][1]))

    if paragraph_dups:
        lines.append("| 段落 | 出现位置 | 摘要 |")
        lines.append("|------|----------|------|")
        for idx, group in enumerate(paragraph_dups[:30], start=1):
            locations = ", ".join(f"`{rel}:{line}`" for rel, line, _para in group)
            summary = group[0][2].replace("|", "\\|")
            if len(summary) > 120:
                summary = summary[:117] + "..."
            lines.append(f"| 重复段落 #{idx} | {locations} | {summary} |")
        lines.append("")
        lines.append(f"共 {len(paragraph_dups)} 组 Markdown 长段落重复候选。")
    else:
        lines.append("✅ 未发现跨文件长段落重复。")
    lines.append("")

    # ========================================
    # 九、Markdown 规则 ID 跨引用
    # ========================================
    lines.append("## 九、Markdown 规则 ID 跨文件引用分析")
    lines.append("")

    rid_files = defaultdict(list)
    for fp in md_fps:
        for rid in fp.ids:
            rid_files[rid].append(fp.rel)

    multi_ref = {k: v for k, v in rid_files.items() if len(v) > 2}
    if multi_ref:
        lines.append("| 规则ID | 引用文件 | 次数 |")
        lines.append("|--------|----------|------|")
        for rid in sorted(multi_ref.keys(), key=lambda x: -len(multi_ref[x])):
            files = ", ".join(sorted(set(multi_ref[rid])))
            lines.append(f"| `{rid}` | {files} | {len(multi_ref[rid])} |")
        lines.append("")
        lines.append(f"共 {len(multi_ref)} 个规则 ID 出现在 ≥3 个文件中。")
    lines.append("")

    # ========================================
    # 十、Markdown 章节结构相似度
    # ========================================
    lines.append("## 十、Markdown 章节结构相似度 (≥35%)")
    lines.append("")

    md_pairs = []
    for i in range(len(md_fps)):
        for j in range(i + 1, len(md_fps)):
            fp1, fp2 = md_fps[i], md_fps[j]
            sim = jaccard(fp1.sections, fp2.sections)
            if sim >= 35:
                md_pairs.append((sim, fp1, fp2))

    md_pairs.sort(key=lambda x: x[0], reverse=True)

    if md_pairs:
        lines.append("| 文件A | 文件B | 章节相似度 |")
        lines.append("|-------|-------|------------|")
        for sim, fp1, fp2 in md_pairs[:30]:
            lines.append(f"| `{fp1.rel}` | `{fp2.rel}` | **{sim}%** |")
        lines.append("")
        lines.append(f"共 {len(md_pairs)} 对 .md 文件章节结构高度相似。")
    else:
        lines.append("✅ 未发现章节结构相似度 ≥ 35% 的 .md 文件对。")
    lines.append("")

    # ========================================
    # 十一、SKILL.md 与 references 重叠
    # ========================================
    lines.append("## 十一、SKILL.md 与 references/ 内容重叠")
    lines.append("")

    skill = next((fp for fp in md_fps if fp.rel == "SKILL.md"), None)
    if skill:
        lines.append("SKILL.md 中出现的规则 ID，在以下 references 中也有定义：")
        lines.append("")
        for rid in sorted(skill.ids):
            refs = [fp.rel for fp in md_fps if rid in fp.ids and fp.rel != "SKILL.md"]
            if refs:
                lines.append(f"- `{rid}` → `{'`, `'.join(refs)}`")
        lines.append("")

        # SKILL.md 章节 vs 各 reference 章节
        lines.append("### SKILL.md 章节与 references 章节重叠")
        lines.append("")
        lines.append("| Reference | 重叠章节数 | 重叠章节 |")
        lines.append("|-----------|-----------|----------|")
        for fp in md_fps:
            if fp.rel == "SKILL.md":
                continue
            common = skill.sections & fp.sections
            if common:
                examples = ", ".join(sorted(common)[:5])
                if len(common) > 5:
                    examples += f" ... (+{len(common)-5})"
                lines.append(f"| `{fp.rel}` | {len(common)} | {examples} |")
        lines.append("")

    # ========================================
    # 十二、总结
    # ========================================
    lines.append("## 十二、去重总结与建议")
    lines.append("")
    lines.append("### 自动化发现")
    lines.append("")
    lines.append(f"1. **完全相同文件**: {dups_found} 组")
    lines.append(f"2. **重复函数名（降噪后）**: {len(dups)} 个函数在多个脚本中定义")
    lines.append(f"3. **重复函数体**: {len(function_body_dups)} 组")
    lines.append(f"4. **重复连续代码块**: {len(representative_blocks)} 组代表候选（原始 {len(repeated_blocks)} 组）")
    lines.append(f"5. **脚本高度相似 (≥60%行)**: {len(content_pairs)} 对")
    lines.append(f"6. **Markdown 长段落重复**: {len(paragraph_dups)} 组")
    lines.append(f"7. **MD 章节高度相似 (≥35%)**: {len(md_pairs)} 对")
    lines.append("")
    lines.append("### 人工审查建议")
    lines.append("")
    lines.append("- **完全相同文件**: 直接删除冗余副本，改为引用或软链接")
    lines.append("- **重复函数体 / 连续代码块**: 优先人工审查，确认行为一致后抽取到公共 helper 或专用脚本库")
    lines.append("- **重复函数名**: 同名但内容不同的 CLI `usage()` 通常不抽取")
    lines.append("- **MD 段落重复**: 若是规则正文重复，保留单一来源并改成交叉引用")
    lines.append("- **MD 章节重叠 / 规则 ID 跨引用**: 判断是索引引用还是内容重复，后者需合并")
    lines.append("- **脚本模式相似 / 工具链相似**: 只作为候选信号，不能单独作为去重依据")
    lines.append("- `references/rule_index.md` 是规则索引，其跨引用是正常设计")
    lines.append("- `evolution/history/` 下的版本快照是故意保留的档案，不在本次分析范围")
    lines.append("")

    # 写报告
    report = '\n'.join(lines)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n  [OK] 报告已生成: {report_path}")


# ---- 主流程 ----

def build_parser():
    parser = argparse.ArgumentParser(
        description="Analyze duplicate logic in markdown and shell files under a target directory."
    )
    parser.add_argument(
        "target",
        help="Directory to analyze.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Directory for the report. Defaults to ./.analysis_output/<target-directory-name>/.",
    )
    parser.add_argument(
        "--write-fingerprints",
        action="store_true",
        help="Also write all_fingerprints.json for debugging. By default only the report is written.",
    )
    return parser

def run_analysis(target, output_dir=None, write_fingerprints=False):
    target_root, output_root = configure_paths(target, output_dir)
    if not os.path.isdir(target_root):
        raise SystemExit(f"Target is not a directory: {target_root}")

    print()
    print("=" * 60)
    print("  去重分析工具")
    print("  Deduplication Analysis Tool")
    print("=" * 60)
    print()
    print(f"  目标目录: {target_root}")
    print(f"  输出目录: {output_root}")
    print()

    # 步骤1: 收集指纹
    print("─" * 40)
    print("  阶段1: 文件单元指纹提取")
    print("─" * 40)

    all_fps = collect_target_fingerprints(target_root)
    print(f"  [OK] target: {len(all_fps)} 个文件")

    if write_fingerprints:
        merged = os.path.join(output_root, "all_fingerprints.json")
        with open(merged, 'w', encoding='utf-8') as f:
            json.dump([fp.to_dict() for fp in all_fps], f, indent=2, ensure_ascii=False)
        print(f"\n  [OK] 指纹汇总: {len(all_fps)} 个文件 → {merged}")
    else:
        print(f"\n  [OK] 指纹汇总: {len(all_fps)} 个文件（未写入，默认只输出报告）")

    # 步骤2: 对比去重
    print()
    print("─" * 40)
    print("  阶段2: 跨文件对比分析")
    print("─" * 40)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = os.path.join(output_root, f"duplication_report_{ts}.md")
    step2_analyze(all_fps, report_path)

    print()
    print("=" * 60)
    print("  分析完成！")
    print(f"  报告: {report_path}")
    print("=" * 60)
    print()
    return report_path

def main(argv=None):
    args = build_parser().parse_args(argv)
    return run_analysis(args.target, args.output_dir, args.write_fingerprints)


if __name__ == "__main__":
    main()
