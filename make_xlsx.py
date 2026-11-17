# -*- coding: utf-8 -*-
"""生成 Excel 数据工作簿：龙头总表、行业汇总、月度收盘价/涨跌幅矩阵、基准指数，并内嵌月度走势图。"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "vendor"))
import xlsxwriter

DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "out_data")

with open(os.path.join(DATA, "panel.json"), encoding="utf-8") as f:
    panel = json.load(f)
industries = panel["industries"]
bench = panel["benchmark"]
base_month = panel["base_month"]
months = [x["month"] for x in bench["series"]]

order = sorted(industries.items(), key=lambda kv: -max(x["cum_return"] for x in kv[1]["leaders"]))
allcum = [s["cum_return"] for v in industries.values() for s in v["leaders"]]
bmark = bench["series"][-1]["norm"] - 100

path = os.path.join(BASE, "A股31个申万一级行业龙头股月度行情数据_2024-2026.xlsx")
wb = xlsxwriter.Workbook(path, {"nan_inf_to_errors": True})
wb.set_properties({
    "title": "A股31个申万一级行业龙头股月度行情数据（2024-2026）",
    "subject": "申万一级行业龙头股月度股价",
    "author": "行业研究数据整理",
    "comments": "数据来源：申万宏源研究所、baostock；数据截止2026-11-13",
})

F = {
    "title": wb.add_format({"bold": True, "font_size": 16, "font_color": "#1B2631", "font_name": "微软雅黑"}),
    "sub": wb.add_format({"font_size": 10, "font_color": "#5D6D7E", "font_name": "微软雅黑"}),
    "header": wb.add_format({"bold": True, "font_size": 9, "font_color": "#FFFFFF", "bg_color": "#1B2631",
                              "align": "center", "valign": "vcenter", "text_wrap": True, "border": 1,
                              "border_color": "#3B4A59", "font_name": "微软雅黑"}),
    "cell": wb.add_format({"font_size": 9, "border": 1, "border_color": "#D5D8DC", "font_name": "微软雅黑",
                            "valign": "vcenter"}),
    "cell_c": wb.add_format({"font_size": 9, "border": 1, "border_color": "#D5D8DC", "font_name": "微软雅黑",
                              "align": "center", "valign": "vcenter"}),
    "name": wb.add_format({"font_size": 9, "bold": True, "border": 1, "border_color": "#D5D8DC",
                            "font_name": "微软雅黑", "valign": "vcenter"}),
    "num2": wb.add_format({"font_size": 9, "num_format": "0.00", "border": 1, "border_color": "#D5D8DC",
                            "font_name": "微软雅黑", "align": "center"}),
    "pct": wb.add_format({"font_size": 9, "num_format": "+0.0%;-0.0%", "border": 1, "border_color": "#D5D8DC",
                           "font_name": "微软雅黑", "align": "center", "font_color": "#C0392B"}),
    "pct_neg": wb.add_format({"font_size": 9, "num_format": "+0.0%;-0.0%", "border": 1, "border_color": "#D5D8DC",
                               "font_name": "微软雅黑", "align": "center", "font_color": "#1E8449"}),
    "pct_plain": wb.add_format({"font_size": 9, "num_format": "0.0%", "border": 1, "border_color": "#D5D8DC",
                                 "font_name": "微软雅黑", "align": "center"}),
    "pct0": wb.add_format({"font_size": 8, "num_format": "+0%;-0%", "border": 1, "border_color": "#D5D8DC",
                            "font_name": "微软雅黑", "align": "center"}),
    "month": wb.add_format({"font_size": 8, "num_format": "+0.0%;-0.0%", "border": 1, "border_color": "#E5E8E8",
                             "font_name": "微软雅黑", "align": "center"}),
    "idx": wb.add_format({"font_size": 9, "bold": True, "bg_color": "#F4F6F7", "border": 1,
                           "border_color": "#D5D8DC", "font_name": "微软雅黑"}),
    "note": wb.add_format({"font_size": 9, "font_color": "#7B7D7D", "font_name": "微软雅黑", "text_wrap": True,
                            "valign": "top"}),
}


def write_title(ws, text, sub, ncols):
    ws.set_row(0, 30)
    ws.merge_range(0, 0, 0, max(ncols - 1, 5), text, F["title"])
    ws.merge_range(1, 0, 1, max(ncols - 1, 5), sub, F["sub"])


# ---------- Sheet: 说明 ----------
ws = wb.add_worksheet("说明")
ws.set_column("A:A", 3)
ws.set_column("B:B", 26)
ws.set_column("C:C", 100)
ws.set_row(0, 34)
ws.write(0, 1, "A股31个申万一级行业龙头股月度行情数据（2024—2026）", F["title"])
ws.write(1, 1, "数据截止：2026-11-13收盘　|　行业：申万一级31个　|　龙头股：155只", F["sub"])
rows = [
    ("行业分类", "申万宏源研究所《申万行业分类（2021版）》一级行业，共31个，覆盖全部A股。"),
    ("龙头认定", "每个行业按申万官方行业指数权重由高到低排序，取前5名作为龙头；剔除2024年后上市、"
                 "月度数据不足30个月的次新股（如长鑫科技、华电新能）。"),
    ("权重来源", "申万宏源研究所官网行业指数成分股与权重接口（swsresearch.com），最新一期发布数据。"),
    ("价格口径", "baostock 前复权月K线，取每月最后一个交易日收盘价；2026年11月为截至11月13日的月内数据。"),
    ("区间", "2023年12月末收盘（基期，归一化=100）至2026年11月13日。"),
    ("区间累计涨跌", "最新收盘 ÷ 基期收盘 − 1。"),
    ("年化收益", "(最新收盘 ÷ 基期收盘)^(12 ÷ 月数) − 1。"),
    ("最大回撤", "月度收盘价序列自峰值的最大跌幅。"),
    ("年化波动率", "月度收益率标准差 × √12。"),
    ("工作表", "01_行业龙头总表、02_行业汇总、03_月度收盘价、04_月度涨跌幅、05_沪深300基准、"
               "07_行业走势图（31张月度折线图）。"),
    ("免责声明", "本数据基于公开信息整理，仅供研究参考，不构成任何投资建议。"),
]
r = 3
for k, v in rows:
    ws.write(r, 1, k, F["name"])
    ws.write(r, 2, v, F["cell"])
    ws.set_row(r, 30)
    r += 1

# ---------- Sheet: 01 龙头总表 ----------
ws = wb.add_worksheet("01_行业龙头总表")
ws.freeze_panes(3, 0)
header = ["申万一级行业", "行业代码", "排名", "股票代码", "股票简称", "申万权重", "总市值(亿元)",
          "基期收盘(元)", "最新收盘(元)", "区间累计涨跌", "年化收益", "最大回撤", "年化波动率",
          "最佳月份", "最佳月涨跌", "最差月份", "最差月涨跌"]
write_title(ws, "31个申万一级行业 · 龙头前五明细（155只）",
            "按申万行业代码排序；排名1为权重第一的龙头；涨跌为2023年12月末至2026年11月13日的累计值", len(header))
for i, h in enumerate(header):
    ws.write(2, i, h, F["header"])
widths = [12, 10, 7, 10, 12, 9, 11, 11, 11, 11, 10, 10, 11, 10, 11, 10, 11]
for i, w in enumerate(widths):
    ws.set_column(i, i, w)
r = 3
for key, info in sorted(industries.items(), key=lambda kv: kv[0]):
    for i, s in enumerate(sorted(info["leaders"], key=lambda x: -x["weight"])):
        ws.write(r, 0, info["name"], F["cell"])
        ws.write(r, 1, key.replace(".SI", ""), F["cell_c"])
        ws.write(r, 2, "龙头" if i == 0 else i + 1, F["name"] if i == 0 else F["cell_c"])
        ws.write(r, 3, s["code"], F["cell_c"])
        ws.write(r, 4, s["name"], F["name"] if i == 0 else F["cell"])
        ws.write_number(r, 5, s["weight"] / 100, F["pct_plain"])
        ws.write_number(r, 6, float(s["mktcap"]) if s.get("mktcap") else 0, F["num2"])
        ws.write_number(r, 7, s["base_close"], F["num2"])
        ws.write_number(r, 8, s["last_close"], F["num2"])
        ws.write_number(r, 9, s["cum_return"] / 100, F["pct"] if s["cum_return"] >= 0 else F["pct_neg"])
        ws.write_number(r, 10, (s["cagr"] or 0) / 100, F["pct_plain"])
        ws.write_number(r, 11, s["mdd"] / 100, F["pct_plain"])
        ws.write_number(r, 12, s["annual_vol"] / 100, F["pct_plain"])
        ws.write(r, 13, s["best"]["month"] if s["best"] else "", F["cell_c"])
        ws.write_number(r, 14, (s["best"]["ret"] or 0) / 100 if s["best"] else 0, F["pct_plain"])
        ws.write(r, 15, s["worst"]["month"] if s["worst"] else "", F["cell_c"])
        ws.write_number(r, 16, (s["worst"]["ret"] or 0) / 100 if s["worst"] else 0, F["pct_plain"])
        r += 1
ws.autofilter(2, 0, r - 1, len(header) - 1)

# ---------- Sheet: 02 行业汇总 ----------
ws = wb.add_worksheet("02_行业汇总")
header = ["排名", "申万一级行业", "行业代码", "成分股数", "龙头", "龙头代码", "龙头权重",
          "龙头累计涨跌", "前五平均涨跌", "前五最大涨幅", "前五最大跌幅"]
write_title(ws, "31个申万一级行业 · 龙头与龙头组合区间表现",
            "按龙头累计涨跌由高到低排列；数据区间2023年12月末—2026年11月13日", len(header))
for i, h in enumerate(header):
    ws.write(2, i, h, F["header"])
for i, w in enumerate([6, 12, 10, 9, 12, 10, 10, 12, 12, 12, 12]):
    ws.set_column(i, i, w)
r = 3
for i, (key, info) in enumerate(order, 1):
    ls = info["leaders"]
    top = max(ls, key=lambda x: x["weight"])
    avg = sum(x["cum_return"] for x in ls) / len(ls)
    vals = [i, info["name"], key.replace(".SI", ""), info["count"], top["name"], top["code"]]
    for j, v in enumerate(vals):
        ws.write(r, j, v, F["name"] if j == 1 else F["cell_c"])
    ws.write_number(r, 6, top["weight"] / 100, F["pct_plain"])
    for j, v in [(7, top["cum_return"]), (8, avg), (9, max(x["cum_return"] for x in ls)),
                 (10, min(x["cum_return"] for x in ls))]:
        ws.write_number(r, j, v / 100, F["pct"] if v >= 0 else F["pct_neg"])
    r += 1
ws.write(r + 1, 0, f"基准（沪深300）同期累计涨跌：{bmark:+.2f}%；155只龙头中上涨 "
                   f"{sum(1 for x in allcum if x > 0)} 只、下跌 {sum(1 for x in allcum if x <= 0)} 只。", F["note"])
ws.autofilter(2, 0, r - 1, len(header) - 1)

# ---------- Sheet: 03 月度收盘价 ----------
ws = wb.add_worksheet("03_月度收盘价")
ws.freeze_panes(3, 3)
header = ["申万一级行业", "股票代码", "股票简称"] + months
write_title(ws, "155只龙头股月度收盘价（前复权，元）",
            "2024-01至2026-11，共35个月度观测；2026-11为截至11月13日的月内收盘", len(header))
for i, h in enumerate(header):
    ws.write(2, i, h, F["header"])
ws.set_column(0, 0, 12)
ws.set_column(1, 2, 11)
ws.set_column(3, len(header) - 1, 8.2, F["num2"])
r = 3
for key, info in sorted(industries.items(), key=lambda kv: kv[0]):
    for s in sorted(info["leaders"], key=lambda x: -x["weight"]):
        m = {x["month"]: x["close"] for x in s["series"]}
        ws.write(r, 0, info["name"], F["cell"])
        ws.write(r, 1, s["code"], F["cell_c"])
        ws.write(r, 2, s["name"], F["name"])
        for j, mm in enumerate(months, 3):
            if mm in m:
                ws.write_number(r, j, m[mm], F["num2"])
        r += 1
ws.autofilter(2, 0, r - 1, len(header) - 1)

# ---------- Sheet: 04 月度涨跌幅 ----------
ws = wb.add_worksheet("04_月度涨跌幅")
ws.freeze_panes(3, 3)
write_title(ws, "155只龙头股月度涨跌幅",
            "月度收益率 = 当月月末收盘 ÷ 上月月末收盘 − 1；2024-01以2023-12月末为基期", len(header))
for i, h in enumerate(header):
    ws.write(2, i, h, F["header"])
ws.set_column(0, 0, 12)
ws.set_column(1, 2, 11)
ws.set_column(3, len(header) - 1, 8.2, F["month"])
r = 3
for key, info in sorted(industries.items(), key=lambda kv: kv[0]):
    for s in sorted(info["leaders"], key=lambda x: -x["weight"]):
        m = {x["month"]: x["ret"] for x in s["series"]}
        ws.write(r, 0, info["name"], F["cell"])
        ws.write(r, 1, s["code"], F["cell_c"])
        ws.write(r, 2, s["name"], F["name"])
        for j, mm in enumerate(months, 3):
            if mm in m and m[mm] is not None:
                ws.write_number(r, j, m[mm] / 100, F["month"])
        r += 1
ws.autofilter(2, 0, r - 1, len(header) - 1)

# ---------- Sheet: 05 基准 ----------
ws = wb.add_worksheet("05_沪深300基准")
header = ["月份", "沪深300收盘", "月度涨跌", "以2023-12=100"]
write_title(ws, "沪深300指数月度表现（参照基准）", "2024-01至2026-11", len(header))
for i, h in enumerate(header):
    ws.write(2, i, h, F["header"])
for i, w in enumerate([12, 14, 12, 20]):
    ws.set_column(i, i, w)
r = 3
for x in bench["series"]:
    ws.write(r, 0, x["month"], F["cell_c"])
    ws.write_number(r, 1, x["close"], F["num2"])
    ws.write_number(r, 2, (x["ret"] or 0) / 100, F["pct_plain"])
    ws.write_number(r, 3, x["norm"], F["num2"])
    r += 1

# ---------- Sheet: 06 图表数据（隐藏，供行业走势图引用） ----------
wdata = wb.add_worksheet("06_图表数据")
wdata.hide()
wdata.write(0, 0, "block", F["header"])
block_row = 2
blocks = {}
for key, info in order:
    ls = sorted(info["leaders"], key=lambda x: -x["weight"])
    placed = []
    for i, s in enumerate(ls):
        wdata.write(block_row, 0, f"{info['name']}|{s['name']}", F["cell"])
        wdata.write(block_row, 1, "月份", F["header"])
        wdata.write(block_row, 2, s["name"], F["header"])
        for k, pt in enumerate(s["series"]):
            wdata.write(block_row + 1 + k, 1, pt["month"], F["cell_c"])
            wdata.write_number(block_row + 1 + k, 2, pt["close"], F["num2"])
        placed.append((s, block_row, len(s["series"])))
        block_row += 40
    blocks[key] = placed

# ---------- Sheet: 07 行业走势图（每行业一张折线图，纵向排布） ----------
ws = wb.add_worksheet("07_行业走势图")
ws.set_column("A:A", 2)
ws.set_column("B:B", 11)
ws.set_column("C:G", 9.5)
ws.set_row(0, 30)
ws.merge_range(0, 1, 0, 7, "31个申万一级行业 · 龙头前五月度股价折线图", F["title"])
ws.merge_range(1, 1, 1, 7, "每张图对应一个行业；数据取自“06_图表数据”工作表；纵向滚动查看", F["sub"])

row_cursor = 3
colors = ["#C0392B", "#2471A3", "#1E8449", "#B7950B", "#6C3483"]
for key, info in order:
    ws.merge_range(row_cursor, 1, row_cursor, 7, f"{info['name']}（{key.replace('.SI','')}）龙头前五月度股价（元）",
                   wb.add_format({"bold": True, "font_size": 11, "font_color": "#1B2631", "font_name": "微软雅黑"}))
    chart = wb.add_chart({"type": "line"})
    for i, (s, block_top, n) in enumerate(blocks[key]):
        chart.add_series({
            "name": f"{s['name']} {s['code']}",
            "categories": ["06_图表数据", block_top + 1, 1, block_top + n, 1],
            "values": ["06_图表数据", block_top + 1, 2, block_top + n, 2],
            "line": {"color": colors[i], "width": 1.75 if i == 0 else 1.25},
        })
    chart.set_title({"name": f"{info['name']} · 龙头前五月度收盘价", "name_font": {"size": 10, "bold": True}})
    chart.set_x_axis({"num_font": {"size": 7, "rotation": -45}, "major_gridlines": {"visible": False}})
    chart.set_y_axis({"num_font": {"size": 7},
                      "major_gridlines": {"visible": True, "line": {"color": "#E5E8E8"}}})
    chart.set_legend({"position": "bottom", "font": {"size": 7}})
    chart.set_size({"width": 900, "height": 300})
    chart.set_chartarea({"border": {"color": "#D5D8DC"}, "fill": {"color": "#FFFFFF"}})
    ws.insert_chart(row_cursor + 1, 1, chart)
    row_cursor += 17

wb.close()
print("saved", path, round(os.path.getsize(path) / 1024 / 1024, 2), "MB")


