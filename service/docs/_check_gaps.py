# -*- coding: utf-8 -*-
"""诊断：基准与最新交易日的缺失情况。"""
import sqlite3

from pathlib import Path
c = sqlite3.connect(str(Path(__file__).resolve().parents[1] / 'data' / 'astock.db'))
q = lambda s: c.execute(s).fetchall()  # noqa: E731

print("000300 recent:", q(
    "select trade_date,close from price_daily where code='000300' and trade_date>='2026-11-10' order by trade_date"))
for d in ("2026-11-16", "2026-11-17"):
    missing = q(f"select code from stock where code not in "
                f"(select code from price_daily where trade_date='{d}')")
    has_bench = q(f"select count(*) from price_daily where code='000300' and trade_date='{d}'")
    print(d, "missing_stocks=", [m[0] for m in missing], "bench_rows=", has_bench[0][0])
print("codes with 2026-11-17:", q("select count(distinct code) from price_daily where trade_date='2026-11-17'")[0][0])
