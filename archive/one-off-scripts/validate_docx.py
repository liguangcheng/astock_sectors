# -*- coding: utf-8 -*-
"""校验生成的 docx 结构：页面尺寸、图片数量、表格宽度是否超出可用版心。"""
import os
import sys

BASE = r"D:\deepseek\astock_sectors"
sys.path.insert(0, os.path.join(BASE, "vendor"))
from docx import Document
from docx.shared import Cm

path = os.path.join(BASE, "A股31个申万一级行业龙头股月度股价走势研究_2024-2026.docx")
d = Document(path)
print("paragraphs", len(d.paragraphs), "tables", len(d.tables),
      "inline_shapes", len(d.inline_shapes), "sections", len(d.sections))
print("images", len([r for r in d.part.rels.values() if "image" in r.reltype]))

usable = {i: (s.page_width.cm - s.left_margin.cm - s.right_margin.cm) for i, s in enumerate(d.sections)}
for i, s in enumerate(d.sections):
    print(" sec", i, "w", round(s.page_width.cm, 1), "h", round(s.page_height.cm, 1),
          "usable", round(usable[i], 1))

for i, t in enumerate(d.tables):
    sec_idx = 1 if i == 0 else (2 if i <= 31 else 3)
    total = sum((c.width.cm if c.width else 0) for c in t.rows[0].cells)
    flag = "OK" if total <= usable[sec_idx] - 0.2 else "OVERFLOW"
    print(f" table{i:02d} sec{sec_idx}: rows={len(t.rows)} cols={len(t.columns)} "
          f"width={total:.1f}cm usable={usable[sec_idx]:.1f}cm {flag}")

for sh in d.inline_shapes:
    print("  shape", round(sh.width.cm, 2), "x", round(sh.height.cm, 2), "cm")
heads = [p.text.strip() for p in d.paragraphs if p.text.strip()]
print("章节标题:", [h for h in heads if h.startswith(("一、", "二、", "三、", "附录"))])
print("行业小节数:", len([h for h in heads if h.startswith("3.")]))
print("前8段:", heads[:8])
