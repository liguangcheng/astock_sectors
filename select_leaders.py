# -*- coding: utf-8 -*-
"""筛选各行业龙头前5：按申万官方权重排序，剔除数据不足的新股/次新股，输出 data/selection.json。"""
import json
import os
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
RAW = os.path.join(DATA, "kline_month")

MIN_MONTHS = 30  # 2024-01 ~ 2026-11 共 35 个自然月，至少覆盖 30 个月
TOP_N = 5

with open(os.path.join(DATA, "shortlist.json"), encoding="utf-8") as f:
    short = json.load(f)

quotes = short["quotes"]
industries = short["industries"]


def load(code):
    p = os.path.join(RAW, f"{code}.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    rows = []
    for r in d["rows"]:
        # Tencent: [date, open, close, high, low, volume, ...]
        try:
            rows.append({"date": str(r[0])[:10], "open": float(r[1]), "close": float(r[2]),
                         "high": float(r[3]), "low": float(r[4]), "vol": float(r[5])})
        except (ValueError, IndexError):
            continue
    rows.sort(key=lambda x: x["date"])
    return rows


selection = {}
report = []
for key, v in industries.items():
    cand = []
    for s in v["stocks"]:
        rows = load(s["code"])
        n = len(rows) if rows else 0
        first = rows[0]["date"] if rows else None
        q = quotes.get(s["code"], {})
        item = {"code": s["code"], "name": q.get("name") or s["name"], "weight": s["weight"],
                "mktcap": q.get("total_mktcap"), "months": n, "first": first,
                "last_close": rows[-1]["close"] if rows else None,
                "eligible": n >= MIN_MONTHS}
        cand.append(item)
    eligible = [c for c in cand if c["eligible"]]
    excluded = [c for c in cand if not c["eligible"]]
    picks = eligible[:TOP_N]
    # 若合格数量不足，用剩余股票按数据完整性补充（仍要求 >=3 个月）
    if len(picks) < TOP_N:
        extra = sorted([c for c in excluded if c["months"] >= 3], key=lambda c: (-c["months"], -c["weight"]))
        picks += extra[: TOP_N - len(picks)]
    selection[key] = {"name": v["name"], "count": v["count"], "stocks": picks,
                      "excluded": [{"code": c["code"], "name": c["name"], "weight": c["weight"],
                                    "months": c["months"], "first": c["first"]} for c in excluded]}
    report.append((key, v["name"], picks, excluded))

with open(os.path.join(DATA, "selection.json"), "w", encoding="utf-8") as f:
    json.dump(selection, f, ensure_ascii=False, indent=1)

for key, name, picks, excluded in report:
    print(f"\n{key} {name}: " + " | ".join(f"{p['name']}({p['code']}) {p['weight']:.2f}% {p['months']}月" for p in picks))
    if excluded:
        print("   剔除(数据不足): " + ", ".join(f"{e['name']}({e['months']}月)" for e in excluded))

print("\n合计行业", len(selection), "股票", sum(len(v["stocks"]) for v in selection.values()))
cnt = Counter()
for v in selection.values():
    cnt[len(v["stocks"])] += 1
print("每行业股票数分布", dict(cnt))
