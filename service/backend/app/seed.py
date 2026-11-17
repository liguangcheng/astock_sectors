# -*- coding: utf-8 -*-
"""初始化种子数据：从既有研究成果（selection.json / bs_month.json / sw_components.json）导入。

用法（在 service/backend 下）：
    python -m app.seed
"""
from __future__ import annotations

import calendar
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from . import analytics
from .config import BASE_MONTH, SERVICE_DIR
from .db import init_db
from .repo import now_str, repo

SRC = SERVICE_DIR.parent / "data"
SEED_CUTOFF = "2026-11-13"   # 现有研究成果的数据截止日，避免把「未来日期」写进水位线


def last_weekday(year: int, month: int) -> str:
    d = date(year, month, calendar.monthrange(year, month)[1])
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    iso = d.isoformat()
    return min(iso, SEED_CUTOFF)


def main() -> None:
    init_db()
    with open(SRC / "selection.json", encoding="utf-8") as f:
        selection = json.load(f)
    with open(SRC / "bs_month.json", encoding="utf-8") as f:
        monthly = json.load(f)
    with open(SRC / "sw_components.json", encoding="utf-8") as f:
        comps = json.load(f)

    industries, stocks, prices = [], [], []
    for order, (key, info) in enumerate(selection.items()):
        code = key.replace(".SI", "")
        count = int(info.get("count") or comps.get(key, {}).get("count") or 0)
        industries.append({"code": code, "name": info["name"], "stock_count": count, "sort_order": order})
        for rank, s in enumerate(sorted(info["stocks"], key=lambda x: -x["weight"]), start=1):
            name = (s["name"] or "").replace(" ", "")
            stocks.append({"code": s["code"], "name": name, "industry_code": code,
                           "weight": float(s["weight"]), "rank": rank,
                           "mktcap": float(s["mktcap"]) if s.get("mktcap") else None,
                           "is_leader": True, "updated_at": now_str()})
            series = monthly.get(s["code"]) or {}
            for m, close in sorted(series.items()):
                if m < BASE_MONTH:
                    continue
                y, mo = int(m[:4]), int(m[5:7])
                prices.append({"code": s["code"], "trade_date": last_weekday(y, mo),
                               "close": float(close), "volume": None, "source": "seed"})

    # 沪深300 基准
    for m, close in sorted((monthly.get("000300") or {}).items()):
        if m < BASE_MONTH:
            continue
        y, mo = int(m[:4]), int(m[5:7])
        prices.append({"code": "000300", "trade_date": last_weekday(y, mo), "close": float(close),
                       "volume": None, "source": "seed-index"})

    repo.upsert_industries(industries)
    repo.upsert_stocks(stocks)
    added = repo.upsert_prices(prices)
    repo.set_state("seeded_at", now_str())
    print(f"行业 {len(industries)}，龙头 {len(stocks)}，价格行 {added}")
    print(f"数据库行数 {repo.count_rows()}，最新交易日 {repo.max_trade_date()}")


if __name__ == "__main__":
    sys.exit(main())
