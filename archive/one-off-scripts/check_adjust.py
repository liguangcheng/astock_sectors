# -*- coding: utf-8 -*-
"""逐笔核对：宇通客车、招商银行 的每月复权因子与前后复权价，判断各数据源复权口径。"""
import json
import os
import sys

BASE = r"D:\deepseek\astock_sectors"
sys.path.insert(0, os.path.join(BASE, "vendor"))
import baostock as bs

bs.login()
for code, name in [("sh.600066", "宇通客车"), ("sh.600036", "招商银行"), ("sz.300896", "爱美客")]:
    print("=" * 20, name, code)
    rs = bs.query_adjust_factor(code=code, start_date="2023-12-01", end_date="2026-11-14")
    print("adjust_factor:", rs.error_code, rs.error_msg)
    rows = []
    while rs.next():
        rows.append(rs.get_row_data())
    for r in rows:
        print("   ", r)

    for flag, label in [("1", "后复权"), ("2", "前复权"), ("3", "不复权")]:
        rs = bs.query_history_k_data_plus(code, "date,close", start_date="2023-12-25",
                                         end_date="2026-11-14", frequency="d", adjustflag=flag)
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        bym = {d[:7]: float(c) for d, c in rows if c}
        if bym:
            ms = sorted(bym)
            print(f"   {label}: 2023-12 {bym.get('2023-12')}, 2024-01 {bym.get('2024-01')}, "
                  f"2026-11 {bym.get(ms[-1])}, 累计 {(bym[ms[-1]]/bym['2023-12']-1)*100:+.1f}%")
bs.logout()
