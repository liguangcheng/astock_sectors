# -*- coding: utf-8 -*-
"""生成图表：31个申万一级行业龙头股月度股价折线图 + 总览图（v2 版式）。"""
import json
import os
import sys
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "vendor"))
os.environ.setdefault("MPLCONFIGDIR", os.path.join(BASE, "_mplcache"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager

DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "charts")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(BASE, "_mplcache"), exist_ok=True)

for f in ["msyh.ttc", "msyhbd.ttc", "simhei.ttf"]:
    p = os.path.join(r"C:\Windows\Fonts", f)
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DengXian"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 9.5

COLORS = ["#C0392B", "#2471A3", "#1E8449", "#B7950B", "#6C3483"]
GRID = dict(color="#D5D8DC", linewidth=0.7, alpha=0.9)

with open(os.path.join(DATA, "panel.json"), encoding="utf-8") as f:
    panel = json.load(f)
industries = panel["industries"]
bench = panel["benchmark"]
base_month = panel["base_month"]


def months_to_dates(months):
    return [date(int(m[:4]), int(m[5:7]), 1) for m in months]


def style_axis(ax):
    ax.grid(True, axis="y", **GRID)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#AAB7B8")
    ax.spines["bottom"].set_color("#AAB7B8")
    ax.tick_params(colors="#34495E", labelsize=8.6)


def fmt_pct(v):
    return "—" if v is None else f"{v:+.1f}%"


order = sorted(industries.items(), key=lambda kv: -max(x["cum_return"] for x in kv[1]["leaders"]))

for key, info in order:
    leaders = sorted(info["leaders"], key=lambda s: -s["weight"])
    fig = plt.figure(figsize=(12.4, 7.1), dpi=150)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.5, 1], hspace=0.30,
                          left=0.075, right=0.775, top=0.845, bottom=0.10)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)

    fig.text(0.075, 0.955, f"{info['name']}行业龙头前五 · 月度股价走势",
             fontsize=17, fontweight="bold", color="#1B2631", va="top")
    fig.text(0.075, 0.905,
             f"申万一级行业（{info['count']}只成分股）　2024年1月—2026年11月　前复权月末收盘价　"
             f"基期：{base_month}月末",
             fontsize=9.5, color="#5D6D7E", va="top")

    ends = []
    for i, s in enumerate(leaders):
        xs = months_to_dates([x["month"] for x in s["series"]])
        ys = [x["close"] for x in s["series"]]
        c = COLORS[i]
        ax1.plot(xs, ys, color=c, linewidth=2.3 if i == 0 else 1.5,
                 label=f"{s['name']}（{s['code']}）", zorder=4 - i * 0.2)
        ax1.scatter([xs[-1]], [ys[-1]], s=24, color=c, zorder=6)
        ends.append([ys[-1], i, xs[-1], c])

    # 末端价格标签防重叠：按价格排序后保证最小垂直间距
    ends.sort(key=lambda t: t[0])
    ylo, yhi = ax1.get_ylim()
    min_gap = (yhi - ylo) * 0.055
    placed = []
    for e in ends:
        y = e[0] if not placed else max(e[0], placed[-1] + min_gap)
        placed.append(y)
        e.append(y)
    for y0, i, x0, c, yl in ends:
        ax1.annotate(f"{y0:.2f}", xy=(x0, y0), xytext=(x0 + timedelta(days=8), yl),
                     textcoords="data", fontsize=8.4, color=c, va="center", fontweight="bold",
                     arrowprops=dict(arrowstyle="-", color=c, lw=0.6, alpha=0.55,
                                     shrinkA=0, shrinkB=2) if abs(yl - y0) > (yhi - ylo) * 0.004 else None)

    ax1.set_ylabel("月末收盘价（元，前复权）", fontsize=9.5, color="#34495E")
    style_axis(ax1)
    leg = ax1.legend(loc="upper left", ncol=1, fontsize=9, frameon=True, framealpha=0.93,
                     edgecolor="#D5D8DC", handlelength=2.0, borderpad=0.6)
    leg.set_zorder(10)

    # 下部：归一化对比
    bx = months_to_dates([x["month"] for x in bench["series"]])
    ax2.plot(bx, [x["norm"] for x in bench["series"]], color="#7F8C8D", linewidth=1.5,
             linestyle="--", label="沪深300", zorder=2)
    ax2.axhline(100, color="#AAB7B8", linewidth=0.8)
    for i, s in enumerate(leaders):
        xs = months_to_dates([x["month"] for x in s["series"]])
        ax2.plot(xs, [x["norm"] for x in s["series"]], color=COLORS[i],
                 linewidth=2.1 if i == 0 else 1.35, zorder=3)
    ax2.set_ylabel(f"以{base_month}月末=100", fontsize=9)
    style_axis(ax2)
    ax1.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.tick_params(labelbottom=False)
    ax2.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_minor_locator(mdates.MonthLocator())
    ax2.set_xlim(months_to_dates([leaders[0]["series"][0]["month"]])[0] - timedelta(days=25),
                 months_to_dates([leaders[0]["series"][-1]["month"]])[0] + timedelta(days=100))

    # 右侧信息卡
    fig.text(0.795, 0.845, "区间累计涨跌幅", fontsize=10.5, color="#1B2631", fontweight="bold", va="top")
    fig.text(0.795, 0.815, f"（{base_month}末 → 2026-11-13）", fontsize=8.4, color="#7B7D7D", va="top")
    y = 0.765
    for i, s in enumerate(leaders):
        tag = "龙头" if i == 0 else f"No.{i+1}"
        fig.text(0.795, y, f"{tag}　{s['name']}", fontsize=10.2, color=COLORS[i], fontweight="bold", va="top")
        fig.text(0.795, y - 0.038, f"{s['code']}　申万权重 {s['weight']:.2f}%", fontsize=8.4, color="#5D6D7E", va="top")
        fig.text(0.795, y - 0.068, fmt_pct(s["cum_return"]), fontsize=11.5, color=COLORS[i], va="top")
        y -= 0.125
    fig.text(0.795, y - 0.005, "沪深300 同期", fontsize=9.2, color="#5D6D7E", va="top")
    fig.text(0.795, y - 0.035, fmt_pct(bench["series"][-1]["norm"] - 100), fontsize=10.5, color="#5D6D7E", va="top")

    fig.text(0.075, 0.028,
             "注：前复权月K线（baostock），按各月最后一个交易日收盘价统计；2026年11月为截至11月13日的月内数据；"
             "龙头按申万宏源研究所最新行业权重排序（已剔除上市不足30个月的新股）。",
             fontsize=7.6, color="#7B7D7D")
    fig.savefig(os.path.join(OUT, f"{key.replace('.SI','')}_{info['name']}.png"),
                facecolor="white", bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)

print("sector charts:", len(order))

# 总览图
names = [info["name"] for _, info in order]
top_vals = [info["leaders"][0]["cum_return"] for _, info in order]
avg_vals = [sum(x["cum_return"] for x in info["leaders"]) / len(info["leaders"]) for _, info in order]
bmark = bench["series"][-1]["norm"] - 100

fig, ax = plt.subplots(figsize=(12.6, 7.6), dpi=150)
fig.subplots_adjust(left=0.075, right=0.975, top=0.85, bottom=0.27)
x = list(range(len(names)))
w = 0.4
b1 = ax.bar([i - w / 2 for i in x], top_vals, width=w, color="#C0392B", label="板块龙头（申万权重第一）")
b2 = ax.bar([i + w / 2 for i in x], avg_vals, width=w, color="#5DADE2", label="龙头前五等权平均")
ax.axhline(bmark, color="#34495E", linestyle="--", linewidth=1.4, label=f"沪深300同期 {bmark:+.1f}%")
ax.axhline(0, color="#566573", linewidth=1)
for rect, v in list(zip(b1, top_vals)) + list(zip(b2, avg_vals)):
    ax.annotate(f"{v:+.0f}%", xy=(rect.get_x() + rect.get_width() / 2, v),
                xytext=(0, 2 if v >= 0 else -2), textcoords="offset points",
                ha="center", va="bottom" if v >= 0 else "top",
                fontsize=6.4, color="#2C3E50", rotation=90)
ax.set_xticks(x)
ax.set_xticklabels(names, rotation=42, ha="right", fontsize=8.8)
ax.set_ylabel("区间累计涨跌幅（%）", fontsize=10.5)
fig.text(0.075, 0.955, "31个申万一级行业：龙头股与龙头前五组合的区间累计涨跌幅",
         fontsize=17, fontweight="bold", color="#1B2631", va="top")
fig.text(0.075, 0.905, "区间：2023年12月末收盘（基期）→ 2026年11月13日　按龙头区间涨幅由高到低排列",
         fontsize=9.5, color="#5D6D7E", va="top")
style_axis(ax)
ax.legend(loc="upper right", fontsize=9.2, frameon=True, framealpha=0.95, edgecolor="#D5D8DC")
fig.text(0.075, 0.03, "数据来源：申万宏源研究所行业分类与权重、baostock 前复权月K线。仅统计各行业权重前五的龙头股，不代表全行业表现。",
         fontsize=8, color="#7B7D7D")
fig.savefig(os.path.join(OUT, "00_总览_行业龙头累计涨跌幅.png"), facecolor="white", bbox_inches="tight", pad_inches=0.2)
plt.close(fig)
print("overview saved")



