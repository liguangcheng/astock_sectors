# -*- coding: utf-8 -*-
"""开源前敏感信息扫描：密钥、口令、个人路径、SID、邮箱等。

用法（任意目录）：
    python service/docs/_secret_scan.py

退出码：0 = 未发现高危项；1 = 发现高危项（需处理后再推送）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # astock_sectors
SKIP_DIRS = {"node_modules", "vendor", ".git", "dist", "__pycache__", ".mplcache", "_local_only"}
TEXT_EXT = {".py", ".md", ".ts", ".tsx", ".js", ".json", ".yml", ".yaml", ".ps1", ".cmd",
            ".html", ".css", ".txt", ".example", ".sql", ".toml", ".ini"}

HIGH = [
    ("私钥", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub Token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")),
    ("AWS Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Slack Token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("通用 API Key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
]
MEDIUM = [
    ("Windows 用户目录", re.compile(r"C:\\Users\\[^\\\s\"']+")),
    ("本机 SID", re.compile(r"S-1-5-21-[0-9-]{10,}")),
    ("硬编码口令", re.compile(r"(?i)(password|passwd|pwd|secret|api[_-]?key)\s*[:=]\s*[\"'][^\"']{6,}[\"']")),
    ("邮箱", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
]
INFO = [
    ("绝对项目路径", re.compile(r"[A-Za-z]:\\[^\s\"']*astock_sectors")),
]


def iter_files():
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXT:
            continue
        parts = set(p.parts)
        if parts & SKIP_DIRS:
            continue
        if "交付" in p.parts:          # 二进制交付物，元数据另行检查
            continue
        yield p


def main() -> int:
    files = list(iter_files())
    findings = {"high": [], "medium": [], "info": []}
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for level, rules in (("high", HIGH), ("medium", MEDIUM), ("info", INFO)):
            for name, rx in rules:
                for m in rx.finditer(text):
                    line = text.count("\n", 0, m.start()) + 1
                    findings[level].append((name, p.relative_to(ROOT), line, m.group(0)[:60]))

    print(f"扫描文件：{len(files)} 个（已排除 node_modules/vendor/.git/dist/交付）")
    for level, label in (("high", "高危"), ("medium", "中危"), ("info", "提示")):
        items = findings[level]
        print(f"\n== {label}：{len(items)}")
        for name, path, line, snippet in items[:20]:
            print(f"   [{name}] {path}:{line}  {snippet}")
        if len(items) > 20:
            print(f"   ... 其余 {len(items) - 20} 条省略")

    if findings["high"]:
        print("\n结论：发现高危项，处理后再推送。")
        return 1
    print("\n结论：未发现密钥类高危项。" + ("（中危项请人工确认）" if findings["medium"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
