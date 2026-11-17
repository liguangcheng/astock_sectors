# -*- coding: utf-8 -*-
"""通过 proxy.finance.qq.com 抓取 2023-11 起的前复权月K线（线程池 + 硬超时 + 断点续抓）。"""
import json
import os
import ssl
import time
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
RAW = os.path.join(DATA, "kline_month2")
os.makedirs(RAW, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      "Referer": "https://gu.qq.com/"}
API = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
START, END = "2023-11-01", "2026-11-15"


def prefix(code):
    if code.startswith(("60", "68", "51", "58", "11", "90")):
        return "sh"
    if code.startswith(("00", "30", "12", "15", "16", "20", "39")):
        return "sz"
    return "sz"


with open(os.path.join(DATA, "selection.json"), encoding="utf-8") as f:
    sel = json.load(f)
codes = sorted({s["code"] for v in sel.values() for s in v["stocks"]})
BENCH = {"sh000300": "沪深300", "sh000001": "上证指数"}
targets = [(c, prefix(c) + c) for c in codes] + list(BENCH.items())
todo = [(lab, sym) for lab, sym in targets
        if not (os.path.exists(os.path.join(RAW, f"{lab}.json")) and os.path.getsize(os.path.join(RAW, f"{lab}.json")) > 100)]
print("targets", len(targets), "todo", len(todo), flush=True)


def fetch_one(item):
    label, sym = item
    param = f"{sym},month,{START},{END},300,qfq"
    url = API + "?" + urllib.parse.urlencode({"param": param})
    last = None
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
                js = json.loads(r.read().decode("utf-8", errors="replace"))
            d = (js.get("data") or {}).get(sym) or {}
            rows = d.get("qfqmonth") or d.get("month") or []
            if not rows:
                return label, "EMPTY", list(d.keys())
            with open(os.path.join(RAW, f"{label}.json"), "w", encoding="utf-8") as f:
                json.dump({"symbol": sym, "label": label, "rows": rows}, f, ensure_ascii=False)
            return label, "OK", len(rows)
        except Exception as e:
            last = e
            time.sleep(1.0 * (i + 1))
    return label, "FAIL", repr(last)[:120]


t0 = time.time()
results = {}
batch = 12
for bi in range(0, len(todo), batch):
    chunk = todo[bi : bi + batch]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(fetch_one, it) for it in chunk]
        for fu in as_completed(futs):
            label, status, info = fu.result()
            results[label] = (status, info)
            if status != "OK":
                print("BAD", label, status, info, flush=True)
    print("done", min(bi + batch, len(todo)), "/", len(todo), f"{time.time()-t0:.0f}s", flush=True)
    time.sleep(0.4)

print("finished", len(results), f"{time.time()-t0:.0f}s", Counter(v[0] for v in results.values()))
print("files on disk", len([f for f in os.listdir(RAW) if f.endswith(".json")]))
