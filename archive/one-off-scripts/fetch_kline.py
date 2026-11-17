# -*- coding: utf-8 -*-
"""抓取候选股的腾讯前复权月K线（2024-01-01 至 2026-11-15），落盘 data/kline_month/{code}.json。"""
import json
import os
import ssl
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
RAW = os.path.join(DATA, "kline_month")
os.makedirs(RAW, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      "Referer": "https://gu.qq.com/"}

START, END = "2024-01-01", "2026-11-15"


def prefix(code):
    if code.startswith(("60", "68", "51", "58", "11", "90")):
        return "sh"
    if code.startswith(("00", "30", "12", "15", "16", "20", "39")):
        return "sz"
    if code.startswith(("43", "83", "87", "88", "92")):
        return "bj"
    return "sz"


def fetch(symbol, kind="month", count=300):
    param = f"{symbol},{kind},{START},{END},{count},qfq"
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode({"param": param})
    last = None
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
                js = json.loads(r.read().decode("utf-8", errors="replace"))
            return js
        except Exception as e:
            last = e
            time.sleep(1.2 * (i + 1))
    raise last


with open(os.path.join(DATA, "shortlist.json"), encoding="utf-8") as f:
    short = json.load(f)

codes = sorted({s["code"] for v in short["industries"].values() for s in v["stocks"]})
print("codes", len(codes))

meta = {}
if os.path.exists(os.path.join(DATA, "kline_meta.json")):
    with open(os.path.join(DATA, "kline_meta.json"), encoding="utf-8") as f:
        meta = json.load(f)

for i, code in enumerate(codes, 1):
    path = os.path.join(RAW, f"{code}.json")
    if os.path.exists(path) and os.path.getsize(path) > 100:
        continue
    sym = prefix(code) + code
    try:
        js = fetch(sym, "month")
        d = (js.get("data") or {}).get(sym) or {}
        rows = d.get("qfqmonth") or d.get("month") or []
        if not rows:
            meta[code] = {"symbol": sym, "status": "EMPTY", "keys": list(d.keys())}
            print("EMPTY", code, sym, list(d.keys()), flush=True)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"symbol": sym, "rows": rows, "keys": list(d.keys())}, f, ensure_ascii=False)
            meta[code] = {"symbol": sym, "status": "OK", "n": len(rows), "first": rows[0][0], "last": rows[-1][0]}
    except Exception as e:
        meta[code] = {"symbol": sym, "status": "FAIL", "err": repr(e)[:150]}
        print("FAIL", code, repr(e)[:100], flush=True)
    if i % 25 == 0:
        print("progress", i, "/", len(codes), flush=True)
    time.sleep(0.12)

with open(os.path.join(DATA, "kline_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)

from collections import Counter
print(Counter(v["status"] for v in meta.values()))
bad = {k: v for k, v in meta.items() if v["status"] != "OK"}
for k, v in list(bad.items())[:20]:
    print("BAD", k, v)
