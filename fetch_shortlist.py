# -*- coding: utf-8 -*-
"""选取各行业权重前8的成分股，并用腾讯实时行情补全市值与简称，便于核对与筛选。"""
import json
import os
import ssl
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      "Referer": "https://gu.qq.com/"}

TOP_N = 8


def prefix(code):
    if code.startswith(("60", "68", "51", "58", "11", "90")):
        return "sh"
    if code.startswith(("00", "30", "12", "15", "16", "20", "39")):
        return "sz"
    if code.startswith(("43", "83", "87", "88", "92")):
        return "bj"
    return "sz"


def get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(1 + i)
    raise last


with open(os.path.join(DATA, "sw_components.json"), encoding="utf-8") as f:
    comps = json.load(f)

shortlist = {}
all_codes = set()
for key, v in comps.items():
    stocks = sorted(v["stocks"], key=lambda s: -s["weight"])[:TOP_N]
    shortlist[key] = {"name": v["name"], "count": v["count"], "stocks": stocks}
    for s in stocks:
        all_codes.add(s["code"])

codes = sorted(all_codes)
print("shortlist industries", len(shortlist), "unique codes", len(codes))

quotes = {}
for i in range(0, len(codes), 40):
    batch = codes[i : i + 40]
    syms = ",".join(prefix(c) + c for c in batch)
    raw = get(f"https://qt.gtimg.cn/q={syms}")
    txt = raw.decode("gbk", errors="replace")
    for line in txt.split(";"):
        line = line.strip()
        if not line.startswith("v_") or "=" not in line:
            continue
        body = line.split("=", 1)[1].strip().strip('"')
        parts = body.split("~")
        if len(parts) < 50:
            continue
        code = parts[2]
        quotes[code] = {
            "name": parts[1],
            "price": parts[3],
            "prev_close": parts[4],
            "open": parts[5],
            "volume": parts[6],
            "high": parts[33] if len(parts) > 33 else "",
            "low": parts[34] if len(parts) > 34 else "",
            "pct": parts[32] if len(parts) > 32 else "",
            "turnover": parts[38] if len(parts) > 38 else "",
            "pe": parts[39] if len(parts) > 39 else "",
            "amplitude": parts[43] if len(parts) > 43 else "",
            "circ_mktcap": parts[44] if len(parts) > 44 else "",
            "total_mktcap": parts[45] if len(parts) > 45 else "",
            "pb": parts[46] if len(parts) > 46 else "",
            "time": parts[30] if len(parts) > 30 else "",
        }
    time.sleep(0.15)

print("quotes", len(quotes))
missing = [c for c in codes if c not in quotes]
print("missing quotes", len(missing), missing[:20])

with open(os.path.join(DATA, "shortlist.json"), "w", encoding="utf-8") as f:
    json.dump({"top_n": TOP_N, "industries": shortlist, "quotes": quotes}, f, ensure_ascii=False, indent=1)

for key, v in shortlist.items():
    print("\n", key, v["name"], f"(成分{v['count']})")
    for s in v["stocks"]:
        q = quotes.get(s["code"], {})
        print(f"   {s['code']} {s['name']:<6} 权重{s['weight']:6.2f}%  市值{q.get('total_mktcap','?'):>10}亿  现价{q.get('price','?')}")
