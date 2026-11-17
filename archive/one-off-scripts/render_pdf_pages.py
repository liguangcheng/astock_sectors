# -*- coding: utf-8 -*-
"""把 PDF 的指定页面渲染为 PNG（基于 PyMuPDF 1.24.9 的 cp312 wheel 在 3.13 上尝试加载）。"""
import os
import sys

BASE = r"D:\deepseek\astock_sectors"
sys.path.insert(0, os.path.join(BASE, "vendor"))

import pymupdf  # noqa

pdf_path = os.path.join(BASE, "_tmp", "report.pdf")
pages = [int(x) for x in sys.argv[1:]] or [1, 2, 3]
doc = pymupdf.open(pdf_path)
print("pages", doc.page_count)
for pno in pages:
    page = doc[pno - 1]
    pix = page.get_pixmap(dpi=110)
    out = os.path.join(BASE, "_tmp", f"page_{pno:02d}.png")
    pix.save(out)
    print("saved", out, pix.width, pix.height)
