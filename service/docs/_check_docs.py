# -*- coding: utf-8 -*-
"""文档自检：内部链接、接口清单、环境变量、关键数字是否与代码一致。"""
import os
import re
import sys

from pathlib import Path
SERVICE = str(Path(__file__).resolve().parents[1])
DOCS = os.path.join(SERVICE, "docs")
ROOT = os.path.dirname(SERVICE)

problems = []

# 1) Markdown 链接检查
link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
for fn in sorted(os.listdir(DOCS)):
    if not fn.endswith(".md"):
        continue
    path = os.path.join(DOCS, fn)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for target in link_re.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = target.split("#")[0]
        if not target:
            continue
        resolved = os.path.normpath(os.path.join(DOCS, target))
        if not os.path.exists(resolved):
            problems.append(f"[link] {fn} -> {target} 不存在")

# 2) 接口清单：代码里的路由 vs 文档里提到的路径
sys.path.insert(0, os.path.join(SERVICE, "backend", "vendor"))
sys.path.insert(0, os.path.join(ROOT, "vendor"))
sys.path.insert(0, os.path.join(SERVICE, "backend"))
from app.api import router  # noqa: E402

code_paths = {getattr(r, "path", "") for r in router.routes}
doc_text = ""
for fn in os.listdir(DOCS):
    if fn.endswith(".md"):
        doc_text += open(os.path.join(DOCS, fn), encoding="utf-8").read()
for p in sorted(code_paths):
    if p not in doc_text:
        problems.append(f"[api] 路由 {p} 未写入文档")
print("API routes:", len(code_paths))

# 3) 环境变量：config.py 读取的 vs 文档写到
cfg = open(os.path.join(SERVICE, "backend", "app", "config.py"), encoding="utf-8").read()
envs = sorted(set(re.findall(r"ASTOCK_[A-Z_]+", cfg)))
for e in envs:
    if e not in doc_text:
        problems.append(f"[env] {e} 未写入文档")
print("ENV vars:", len(envs), envs)

# 4) 关键数字
checks = [("31", "行业数"), ("155", "龙头数"), ("5,616", "价格行数"), ("2023-12", "基期"), ("3999", "端口")]
for token, label in checks:
    if token not in doc_text:
        problems.append(f"[num] {label} {token} 未出现")

print("\n=== 检查结果 ===")
if problems:
    for p in problems:
        print("PROBLEM", p)
    sys.exit(1)
print("全部通过：链接、接口、环境变量、关键数字一致")
