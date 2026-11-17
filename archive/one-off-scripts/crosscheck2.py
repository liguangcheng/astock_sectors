# -*- coding: utf-8 -*-
"""比较腾讯 qfq 月K与新浪日线月末的“区间收益率”是否一致（检验复权口径差异是否只影响价格标度）。"""
import json
import ssl
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}

with open(r"D:\deepseek\astock_sectors\data\panel.json", encoding="utf-8") as f:
    panel = json.load(f)

checks = [("801120.SI", "600519", "贵州茅台"), ("801980.SI", "300896", "爱美客"),
          ("801770.SI", "300308", "中际旭创"), ("801780.SI", "600036", "招商银行"),
          ("801080.SI", "688256", "寒武纪")]

for key, code, name in checks:
    s = [x for x in panel["industries"][key]["leaders"] if x["code"] == code][0]
    tx = {x["month"]: x["close"] for x in s["series"]}
    sym = ("sh" if code.startswith("6") else "sz") + code
    url = (f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
           f"?symbol={sym}&scale=240&ma=no&datalen=800")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
        rows = json.loads(r.read().decode("utf-8", errors="replace"))
    bym = {}
    for r0 in rows:
        bym[r0["day"][:7]] = float(r0["close"])
    months = [m for m in sorted(tx) if m >= "2024-01" and m in bym]
    diffs = []
    for a, b in zip(months, months[1:]):
        r_tx = tx[b] / tx[a] - 1
        r_sn = bym[b] / bym[a] - 1
        diffs.append(abs(r_tx - r_sn) * 100)
    cum_tx = (tx[months[-1]] / tx["2023-12"] - 1) * 100
    cum_sn = (bym[months[-1]] / bym["2023-12"] - 1) * 100
    print(f"{name}({code}) 月份{len(months)} 月度收益最大差异 {max(diffs):.3f}pp 均值 {sum(diffs)/len(diffs):.4f}pp")
    print(f"   区间累计：腾讯 {cum_tx:+.2f}% | 新浪 {cum_sn:+.2f}%  差 {cum_sn-cum_tx:+.2f}pp")
