# -*- coding: utf-8 -*-
"""校验 Excel 工作簿：工作表清单、行列数、内嵌图表数量。"""
import os
import sys
import zipfile

BASE = r"D:\deepseek\astock_sectors"
sys.path.insert(0, os.path.join(BASE, "vendor"))
import openpyxl

path = os.path.join(BASE, "A股31个申万一级行业龙头股月度行情数据_2024-2026.xlsx")
wb = openpyxl.load_workbook(path, data_only=False)
print("sheets:", wb.sheetnames)
for ws in wb.worksheets:
    print(f"  {ws.title}: dims={ws.dimensions} max_row={ws.max_row} max_col={ws.max_column} "
          f"charts={len(ws._charts)} hidden={ws.sheet_state}")
with zipfile.ZipFile(path) as z:
    charts = [n for n in z.namelist() if n.startswith("xl/charts/chart")]
    print("chart parts:", len(charts))
    bad = z.testzip()
    print("zip test:", "OK" if bad is None else bad)
