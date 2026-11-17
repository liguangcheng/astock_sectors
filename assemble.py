# -*- coding: utf-8 -*-
"""整理交付清单：抄写成品到 交付 目录，生成 00_龙头股一览表.md（含31行业×前五龙头）。"""
import json
import os
import shutil

BASE = r"D:\deepseek\astock_sectors"
DELIV = os.path.join(BASE, "交付")
os.makedirs(DELIV, exist_ok=True)
os.makedirs(os.path.join(DELIV, "图表PNG"), exist_ok=True)
os.makedirs(os.path.join(DELIV, "原始数据CSV"), exist_ok=True)

with open(os.path.join(BASE, "data", "panel.json"), encoding="utf-8") as f:
    panel = json.load(f)
industries = panel["industries"]
bench = panel["benchmark"]
bmark = bench["series"][-1]["norm"] - 100
order = sorted(industries.items(), key=lambda kv: -max(x["cum_return"] for x in kv[1]["leaders"]))

names = {
    "A股31个申万一级行业龙头股月度股价走势研究_2024-2026.pdf": "A股31个申万一级行业龙头股月度股价走势研究_2024-2026.pdf",
    "A股31个申万一级行业龙头股月度股价走势研究_2024-2026.docx": "A股31个申万一级行业龙头股月度股价走势研究_2024-2026.docx",
    "A股31个申万一级行业龙头股月度行情数据_2024-2026.xlsx": "A股31个申万一级行业龙头股月度行情数据_2024-2026.xlsx",
}
for fn in names:
    src = os.path.join(BASE, fn)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(DELIV, fn))
        print("copied", fn)

for fn in os.listdir(os.path.join(BASE, "charts")):
    if fn.endswith(".png"):
        shutil.copy2(os.path.join(BASE, "charts", fn), os.path.join(DELIV, "图表PNG", fn))
print("charts copied", len(os.listdir(os.path.join(DELIV, "图表PNG"))))

for fn in os.listdir(os.path.join(BASE, "out_data")):
    shutil.copy2(os.path.join(BASE, "out_data", fn), os.path.join(DELIV, "原始数据CSV", fn))
print("csv copied", len(os.listdir(os.path.join(DELIV, "原始数据CSV"))))

lines = []
lines.append("# A股31个申万一级行业 · 龙头前五与区间表现（2024-01 至 2026-11-13）\n")
lines.append(f"行业分类：申万宏源研究所《申万行业分类（2021版）》一级行业；"
             f"龙头按申万官方行业指数权重排序取前五，剔除上市不足30个月的次新股。")
lines.append(f"同期沪深300累计涨跌：**{bmark:+.2f}%**；155只龙头中上涨 "
             f"{sum(1 for v in industries.values() for s in v['leaders'] if s['cum_return']>0)} 只。\n")
lines.append("| 行业 | 龙头(权重第一) | 区间涨跌 | No.2 | 涨跌 | No.3 | 涨跌 | No.4 | 涨跌 | No.5 | 涨跌 | 前五均值 |")
lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for key, info in order:
    ls = sorted(info["leaders"], key=lambda x: -x["weight"])
    cells = [info["name"]]
    for s in ls:
        cells += [f"{s['name']}({s['code']})", f"{s['cum_return']:+.1f}%"]
    avg = sum(x["cum_return"] for x in ls) / len(ls)
    cells.append(f"**{avg:+.1f}%**")
    lines.append("| " + " | ".join(cells) + " |")

lines.append("\n## 数据说明\n")
lines.append("- 价格：baostock 前复权月K线，取每月最后一个交易日收盘价；2026年11月为截至11月13日的月内数据。")
lines.append("- 区间基准：2023年12月末收盘（=100），终点2026年11月13日。")
lines.append("- 指标：区间累计涨跌、年化收益、最大回撤（月末收盘序列）、年化波动率（月度收益标准差×√12）。")
lines.append("- 特别提示：松发股份（603268）2024年完成重大资产重组、主业由陶瓷转向船舶制造，其涨幅主要反映重组预期。")
lines.append("- 数据仅供研究参考，不构成投资建议。")
with open(os.path.join(DELIV, "00_龙头股一览表.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("manifest written")
print("deliverables:", os.listdir(DELIV))

