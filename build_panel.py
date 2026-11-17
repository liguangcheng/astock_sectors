# -*- coding: utf-8 -*-
"""用 baostock 前复权月末收盘重建 panel.json（价格口径统一：以最新真实价格为基准的前复权）。"""
import json
import math
import os

BASE = r"D:\deepseek\astock_sectors"
DATA = os.path.join(BASE, "data")
BASE_MONTH = "2023-12"
FIRST, LAST = "2024-01", "2026-11"

with open(os.path.join(DATA, "bs_month.json"), encoding="utf-8") as f:
    bs = json.load(f)
with open(os.path.join(DATA, "selection.json"), encoding="utf-8") as f:
    sel = json.load(f)
with open(os.path.join(DATA, "shortlist.json"), encoding="utf-8") as f:
    short = json.load(f)
quotes = short["quotes"]


def clean_name(n):
    return (n or "").replace(" ", "").replace("\u3000", "").replace("Ａ", "A").replace("Ｂ", "B")


panel = {}
missing = []
for key, v in sel.items():
    rows = []
    for s in v["stocks"]:
        code = s["code"]
        bym = bs.get(code) or {}
        if BASE_MONTH not in bym:
            missing.append(code)
            continue
        months = sorted(m for m in bym if BASE_MONTH <= m <= LAST)
        base_close = bym[BASE_MONTH]
        closes, prev = [], base_close
        for m in months:
            c = bym[m]
            closes.append({"month": m, "close": round(c, 3),
                           "ret": round((c / prev - 1) * 100, 2) if prev else None,
                           "norm": round(c / base_close * 100, 2)})
            prev = c
        ser = [x for x in closes if x["month"] >= FIRST]
        vals = [x["close"] for x in ser]
        cum = (vals[-1] / base_close - 1) * 100 if vals else None
        peak, mdd = -1e18, 0.0
        for x in vals:
            peak = max(peak, x)
            if peak > 0:
                mdd = min(mdd, x / peak - 1)
        r = [x["ret"] for x in ser if x["ret"] is not None]
        vol = math.sqrt(sum((y - sum(r) / len(r)) ** 2 for y in r) / (len(r) - 1)) if len(r) > 2 else 0
        years = len(r) / 12
        cagr = ((vals[-1] / base_close) ** (1 / years) - 1) * 100 if (years > 0 and vals) else None
        best = max(closes, key=lambda x: x["ret"] if x["ret"] is not None else -1e9)
        worst = min(closes, key=lambda x: x["ret"] if x["ret"] is not None else 1e9)
        rows.append({
            "code": code, "name": clean_name(s["name"]), "weight": s["weight"],
            "mktcap": s.get("mktcap"), "base_close": round(base_close, 3),
            "last_close": round(vals[-1], 3) if vals else None,
            "cum_return": round(cum, 2) if cum is not None else None,
            "cagr": round(cagr, 2) if cagr is not None else None,
            "mdd": round(mdd * 100, 2), "annual_vol": round(vol * math.sqrt(12), 2),
            "best": {"month": best["month"], "ret": best["ret"]},
            "worst": {"month": worst["month"], "ret": worst["ret"]},
            "series": closes,
        })
    allm = sorted({x["month"] for r in rows for x in r["series"] if x["month"] >= FIRST})
    eq, lvl = [], 100.0
    for m in allm:
        rr = [x["ret"] for r in rows for x in r["series"] if x["month"] == m and x["ret"] is not None]
        e = {"month": m, "ret": round(sum(rr) / len(rr), 2) if rr else None}
        if e["ret"] is not None:
            lvl *= 1 + e["ret"] / 100
        e["norm"] = round(lvl, 2)
        eq.append(e)
    panel[key] = {"name": v["name"], "count": v["count"], "leaders": rows, "equal_weight": eq}

# 基准：沪深300（不复权，指数无复权问题）
b = bs.get("000300") or {}
bmonths = sorted(m for m in b if FIRST <= m <= LAST)
prev = b.get(BASE_MONTH)
bench, blvl = [], 100.0
for m in bmonths:
    c = b[m]
    r = (c / prev - 1) * 100 if prev else None
    if r is not None:
        blvl *= 1 + r / 100
    bench.append({"month": m, "close": round(c, 2), "ret": round(r, 2) if r is not None else None,
                  "norm": round(blvl, 2)})
    prev = c

with open(os.path.join(DATA, "panel.json"), "w", encoding="utf-8") as f:
    json.dump({"base_month": BASE_MONTH, "source": "baostock 前复权",
               "benchmark": {"name": "沪深300", "series": bench}, "industries": panel},
              f, ensure_ascii=False, indent=1)

print("行业", len(panel), "缺失", len(missing), missing[:10])
print("基准累计", round(bench[-1]["norm"] - 100, 2), "%")
allcum = [s["cum_return"] for v in panel.values() for s in v["leaders"]]
print("股票数", len(allcum), "上涨", sum(1 for x in allcum if x > 0),
      "中位", sorted(allcum)[len(allcum) // 2], "均值", round(sum(allcum) / len(allcum), 2))
rank = sorted([(max(x["cum_return"] for x in v["leaders"]), v["name"]) for v in panel.values()], reverse=True)
print("行业龙头最强:", rank[:5])
print("行业龙头最弱:", rank[-5:])
n_div = 0
for k, v in panel.items():
    ls = sorted(v["leaders"], key=lambda x: -x["cum_return"])
    top, avg = ls[0]["cum_return"], sum(x["cum_return"] for x in ls) / 5
    if top - avg > 30:
        n_div += 1
print("分化>30pp的行业数", n_div)
for code in ("600519", "300896", "300308", "688256", "600066"):
    for v in panel.values():
        for s in v["leaders"]:
            if s["code"] == code:
                print(code, s["name"], "base", s["base_close"], "last", s["last_close"], "cum", s["cum_return"])
