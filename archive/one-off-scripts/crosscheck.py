# -*- coding: utf-8 -*-
"""抽样校验：用新浪日K线（前复权）计算月末收盘，与腾讯口径对比，检查数据一致性。"""
import json
import os
import ssl
import urllib.request

BASE = r"D:\deepseek\astock_sectors"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}

with open(os.path.join(BASE, "data", "panel.json"), encoding="utf-8") as f:
    panel = json.load(f)

checks = [("801120.SI", "600519", "贵州茅台"), ("801980.SI", "300896", "爱美客"),
          ("801770.SI", "300308", "中际旭创"), ("801780.SI", "600036", "招商银行")]

for key, code, name in checks:
    s = [x for x in panel["industries"][key]["leaders"] if x["code"] == code][0]
    want = {x["month"]: x["close"] for x in s["series"] if x["month"] in ("2024-01", "2024-02", "2025-06", "2026-11")}
    sym = ("sh" if code.startswith("6") else "sz") + code
    url = (f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
           f"?symbol={sym}&scale=240&ma=no&datalen=800")
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
            rows = json.loads(r.read().decode("utf-8", errors="replace"))
        bym = {}
        for r0 in rows:
            m = r0["day"][:7]
            bym[m] = float(r0["close"])   # 后出现的（更晚的交易日）覆盖前面的
        print(f"{name}({code})")
        for m, v in want.items():
            print(f"   {m}: 腾讯 {v:.2f} | 新浪日线月末 {bym.get(m, 'NA')}")
    except Exception as e:
        print(name, "FAIL", repr(e)[:120])
