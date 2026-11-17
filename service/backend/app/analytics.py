# -*- coding: utf-8 -*-
"""行情分析：月末聚合、累计收益、年化、最大回撤、波动率、归一化。"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable, Sequence

from .config import BASE_MONTH


def to_monthly(daily: Iterable[dict]) -> list[dict]:
    """把日线聚合成月末序列：每月取最后一个交易日收盘价。"""
    last: dict[str, dict] = {}
    for r in daily:
        m = r["trade_date"][:7]
        prev = last.get(m)
        if prev is None or r["trade_date"] > prev["trade_date"]:
            last[m] = r
    months = sorted(last)
    out = []
    base_close = None
    prev_close = None
    for m in months:
        close = float(last[m]["close"])
        if m == BASE_MONTH:
            base_close = close
        ret = None
        if prev_close:
            ret = round((close / prev_close - 1) * 100, 2)
        out.append({
            "month": m,
            "trade_date": last[m]["trade_date"],
            "close": round(close, 3),
            "ret": ret,
            "norm": round(close / base_close * 100, 2) if base_close else None,
        })
        prev_close = close
    return out


def metrics(monthly: Sequence[dict], base_month: str = BASE_MONTH) -> dict:
    """基于月末序列计算区间指标（起点为 base_month 月末）。"""
    base = next((x for x in monthly if x["month"] == base_month), None)
    ser = [x for x in monthly if base is None or x["month"] >= base_month]
    if not ser or base is None:
        return {"cum_return": None, "cagr": None, "mdd": None, "annual_vol": None,
                "best": None, "worst": None, "last_close": None, "base_close": None,
                "last_month": None, "months": 0}
    vals = [x["close"] for x in ser]
    cum = (vals[-1] / base["close"] - 1) * 100
    rets = [x["ret"] for x in ser if x["ret"] is not None]
    n = len(rets)
    vol = math.sqrt(sum((r - sum(rets) / n) ** 2 for r in rets) / (n - 1)) if n > 1 else 0.0
    cagr = ((vals[-1] / base["close"]) ** (12 / n) - 1) * 100 if n > 0 else None
    peak, mdd = -1e18, 0.0
    for v in vals:
        peak = max(peak, v)
        if peak > 0:
            mdd = min(mdd, v / peak - 1)
    best = max(ser, key=lambda x: x["ret"] if x["ret"] is not None else -1e9)
    worst = min(ser, key=lambda x: x["ret"] if x["ret"] is not None else 1e9)
    return {
        "base_close": round(base["close"], 3),
        "last_close": round(vals[-1], 3),
        "last_month": ser[-1]["month"],
        "months": n,
        "cum_return": round(cum, 2),
        "cagr": round(cagr, 2) if cagr is not None else None,
        "mdd": round(mdd * 100, 2),
        "annual_vol": round(vol * math.sqrt(12), 2),
        "best": {"month": best["month"], "ret": best["ret"]},
        "worst": {"month": worst["month"], "ret": worst["ret"]},
    }


def group_by_code(rows: Iterable[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        out[r["code"]].append(r)
    return out


def month_range(start: str, end: str) -> list[str]:
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out
