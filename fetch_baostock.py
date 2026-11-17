# -*- coding: utf-8 -*-
"""用 baostock 前复权日线重建全部龙头的月末收盘序列（含沪深300），带断线重连。"""
import json
import os
import sys
import time

BASE = r"D:\deepseek\astock_sectors"
sys.path.insert(0, os.path.join(BASE, "vendor"))
import baostock as bs

DATA = os.path.join(BASE, "data")
with open(os.path.join(DATA, "selection.json"), encoding="utf-8") as f:
    sel = json.load(f)
codes = sorted({s["code"] for v in sel.values() for s in v["stocks"]})

path = os.path.join(DATA, "bs_month.json")
have = {}
if os.path.exists(path):
    with open(path, encoding="utf-8") as f:
        have = json.load(f)
need = [c for c in codes if c not in have or len(have[c]) < 400]
print("have", len(have), "need", len(need), flush=True)


def bs_code(c):
    return ("sh." if c.startswith("6") else "sz.") + c


def login():
    for _ in range(3):
        lg = bs.login()
        if lg.error_code == "0":
            return True
        time.sleep(2)
    return False


def fetch(code, tries=4):
    for i in range(tries):
        try:
            rs = bs.query_history_k_data_plus("sh.000300" if code == "000300" else bs_code(code),
                                             "date,close", start_date="2023-12-01", end_date="2026-11-14",
                                             frequency="d", adjustflag="3" if code == "000300" else "2")
            if rs.error_code != "0":
                raise RuntimeError(rs.error_msg)
            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
            if not rows:
                raise RuntimeError("empty")
            bym = {}
            for d, c in rows:
                if c and float(c) > 0:
                    bym[d[:7]] = float(c)
            return bym
        except Exception as e:
            print("  retry", code, repr(e)[:80], flush=True)
            try:
                bs.logout()
            except Exception:
                pass
            time.sleep(2)
            login()
    return None


if not login():
    raise SystemExit("login failed")

t0 = time.time()
for i, code in enumerate(need, 1):
    r = fetch(code)
    if r:
        have[code] = r
    else:
        print("FAIL", code, flush=True)
    if i % 10 == 0:
        print("done", i, "/", len(need), f"{time.time()-t0:.0f}s", flush=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(have, f, ensure_ascii=False)
    time.sleep(0.05)

bench = fetch("000300")
if bench:
    have["000300"] = bench
with open(path, "w", encoding="utf-8") as f:
    json.dump(have, f, ensure_ascii=False)
bs.logout()
print("total stocks", len([k for k in have if k != '000300']), "benchmark", "000300" in have, flush=True)
