# -*- coding: utf-8 -*-
"""检查服务数据库当前状态，供 STATUS 文档取数。"""
import json
import os
import sqlite3

from pathlib import Path
DB = str(Path(__file__).resolve().parents[1] / 'data' / 'astock.db')
c = sqlite3.connect(DB)
q = lambda s: c.execute(s).fetchall()  # noqa: E731

print("rows:", q("select count(*) from price_daily")[0][0])
print("by source:", q("select source,count(*) from price_daily group by source"))
print("distinct codes:", q("select count(distinct code) from price_daily")[0][0])
print("date range:", q("select min(trade_date),max(trade_date) from price_daily"))
print("\nrecent dates:")
for r in q("select trade_date,count(*) from price_daily where trade_date>='2026-11-10' group by trade_date order by trade_date"):
    print("  ", r)

print("\nsync_state:")
for r in q("select key,value from sync_state"):
    print("  ", r)

print("\nsync_log:")
for r in q("select id,started_at,finished_at,trigger,window_start,window_end,added_rows,rebuilt,status,message from sync_log order by id"):
    print("  ", r)

print("\nper-code months/rows (sample):")
for code in ("600519", "300308", "000300"):
    r = q(f"select count(distinct substr(trade_date,1,7)),count(*) from price_daily where code='{code}'")[0]
    print("  ", code, "months=", r[0], "rows=", r[1])

print("\nrebuilt candidates (codes with >120 rows):")
for r in q("select code,count(*) n from price_daily group by code having n>120 order by n desc limit 15"):
    print("  ", r)

print("\nmonthly coverage of 2026-11:")
for r in q("select substr(trade_date,1,7) m,count(*) n,count(distinct code) codes from price_daily where trade_date>='2026-10-01' group by m"):
    print("  ", r)
