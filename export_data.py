# -*- coding: utf-8 -*-
"""导出结构化数据：龙头总表、行业汇总、月度收盘价矩阵、月度涨跌幅矩阵、个股指标。"""
import csv
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "out_data")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(DATA, "panel.json"), encoding="utf-8") as f:
    panel = json.load(f)
industries = panel["industries"]
bench = panel["benchmark"]
base_month = panel["base_month"]

with open(os.path.join(DATA, "sw_components.json"), encoding="utf-8") as f:
    comps = json.load(f)

months = [x["month"] for x in bench["series"]]
print("months", len(months), months[0], months[-1])


def w(path, header, rows):
    with open(os.path.join(OUT, path), "w", encoding="utf-8-sig", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(header)
        cw.writerows(rows)
    print("written", path, len(rows))


# 1) 龙头明细总表
header = ["申万一级行业", "行业代码", "排名", "股票代码", "股票简称", "申万权重(%)", "总市值(亿元)",
          "基期收盘(元)", "最新收盘(元)", "区间累计涨跌(%)", "年化收益(%)", "最大回撤(%)",
          "年化波动率(%)", "最佳月份", "最佳月涨跌(%)", "最差月份", "最差月涨跌(%)"]
rows = []
for key, info in sorted(industries.items(), key=lambda kv: kv[0]):
    for i, s in enumerate(sorted(info["leaders"], key=lambda x: -x["weight"])):
        rows.append([info["name"], key.replace(".SI", ""), i + 1, s["code"], s["name"], f"{s['weight']:.2f}",
                     s["mktcap"], s["base_close"], s["last_close"], s["cum_return"], s["cagr"], s["mdd"],
                     s["annual_vol"],
                     s["best"]["month"] if s["best"] else "", s["best"]["ret"] if s["best"] else "",
                     s["worst"]["month"] if s["worst"] else "", s["worst"]["ret"] if s["worst"] else ""])
w("01_龙头股总表.csv", header, rows)

# 2) 行业汇总
header = ["申万一级行业", "行业代码", "成分股数", "龙头名称", "龙头代码", "龙头权重(%)",
          "龙头累计涨跌(%)", "前五平均累计涨跌(%)", "前五区间最大涨幅(%)", "前五区间最大跌幅(%)"]
rows = []
for key, info in sorted(industries.items(), key=lambda kv: -max(x["cum_return"] for x in kv[1]["leaders"])):
    ls = info["leaders"]
    top = max(ls, key=lambda x: x["weight"])
    avg = sum(x["cum_return"] for x in ls) / len(ls)
    rows.append([info["name"], key.replace(".SI", ""), info["count"], top["name"], top["code"],
                 f"{top['weight']:.2f}", top["cum_return"], round(avg, 2),
                 max(x["cum_return"] for x in ls), min(x["cum_return"] for x in ls)])
w("02_行业汇总.csv", header, rows)

# 3) 月度收盘价矩阵
header = ["行业", "代码", "名称"] + months
rows = []
for key, info in sorted(industries.items(), key=lambda kv: kv[0]):
    for s in sorted(info["leaders"], key=lambda x: -x["weight"]):
        m = {x["month"]: x["close"] for x in s["series"]}
        rows.append([info["name"], s["code"], s["name"]] + [m.get(mm, "") for mm in months])
w("03_月度收盘价.csv", header, rows)

# 4) 月度涨跌幅矩阵
header = ["行业", "代码", "名称"] + months
rows = []
for key, info in sorted(industries.items(), key=lambda kv: kv[0]):
    for s in sorted(info["leaders"], key=lambda x: -x["weight"]):
        m = {x["month"]: x["ret"] for x in s["series"]}
        rows.append([info["name"], s["code"], s["name"]] + [m.get(mm, "") for mm in months])
w("04_月度涨跌幅.csv", header, rows)

# 5) 基准指数
header = ["月份", "沪深300收盘", "月涨跌(%)", "以2023-12=100"]
rows = [[x["month"], x["close"], x["ret"], x["norm"]] for x in bench["series"]]
w("05_沪深300基准.csv", header, rows)

# 6) 说明
with open(os.path.join(OUT, "06_数据说明.txt"), "w", encoding="utf-8") as f:
    f.write(
        "数据说明\n"
        "=======\n"
        "1. 行业分类：申万宏源研究所《申万行业分类（2021版）》一级行业，共31个。\n"
        "2. 成分股与权重：申万宏源研究所官网 index_publish 接口（swsresearch.com），\n"
        "   权重为该股在对应申万一级行业指数中的最新权重（最新一期发布），合计约100%。\n"
        "3. 龙头筛选：在每个行业全部成分股中，按申万官方权重由高到低排序，取前5名；\n"
        "   剔除2024年1月之后上市、月度价格数据不足30个月的次新股（如长鑫科技、华电新能）。\n"
        "4. 价格数据：腾讯财经前复权（qfq）月K线，取每月最后一个交易日收盘价；\n"
        "   2026年11月为截至2026年11月13日的月内数据。\n"
        "5. 区间：基期2023年12月29日收盘（归一化=100），终点2026年11月13日。\n"
        "6. 指标口径：\n"
        "   区间累计涨跌 = 最新收盘 / 基期收盘 - 1；\n"
        "   年化收益 = (最新收盘/基期收盘)^(12/月数) - 1；\n"
        "   最大回撤 = 月度收盘序列自峰值的最大跌幅；\n"
        "   年化波动率 = 月度收益率标准差 × sqrt(12)；\n"
        "   最佳/最差月份取2024-01至2026-11的月度涨跌幅极值。\n"
        "7. 数据抓取时间：2026-11-15。数据仅供研究参考，不构成投资建议。\n"
    )
print("done")
