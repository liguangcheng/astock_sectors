# -*- coding: utf-8 -*-
"""尝试安装/加载 baostock（纯 Python，socket 协议），并抓取少量前复权日线做口径对比。"""
import io
import json
import os
import ssl
import sys
import zipfile
import urllib.request

BASE = r"D:\deepseek\astock_sectors"
VENDOR = os.path.join(BASE, "vendor")
sys.path.insert(0, VENDOR)

if not os.path.isdir(os.path.join(VENDOR, "baostock")):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    UA = {"User-Agent": "Mozilla/5.0"}
    js = json.loads(urllib.request.urlopen(
        urllib.request.Request("https://pypi.org/pypi/baostock/json", headers=UA), timeout=30, context=ctx).read())
    whl = [f for f in js["urls"] if f["filename"].endswith(".whl")][0]
    print("download", whl["filename"])
    data = urllib.request.urlopen(urllib.request.Request(whl["url"], headers=UA), timeout=60, context=ctx).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(VENDOR)
    print("extracted")

import baostock as bs

lg = bs.login()
print("login:", lg.error_code, lg.error_msg)

rs = bs.query_history_k_data_plus("sh.600519", "date,code,open,high,low,close,volume,amount,adjustflag",
                                 start_date="2023-12-01", end_date="2026-11-14",
                                 frequency="d", adjustflag="2")
print("query:", rs.error_code, rs.error_msg)
rows = []
while rs.next():
    rows.append(rs.get_row_data())
print("rows", len(rows), rows[:2], rows[-2:])
bs.logout()
