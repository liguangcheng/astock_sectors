# -*- coding: utf-8 -*-
"""生成 Word 研究报告：31个申万一级行业龙头股月度股价走势 + 汇总表 + 附录明细。"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "vendor"))

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
CHARTS = os.path.join(BASE, "charts")
OUT = os.path.join(BASE, "out_data")

with open(os.path.join(DATA, "panel.json"), encoding="utf-8") as f:
    panel = json.load(f)
industries = panel["industries"]
bench = panel["benchmark"]
base_month = panel["base_month"]
bmark = bench["series"][-1]["norm"] - 100

SW_CODES = {}
for k in industries:
    SW_CODES[k] = k.replace(".SI", "")

order = sorted(industries.items(), key=lambda kv: -max(x["cum_return"] for x in kv[1]["leaders"]))

FONT_CN = "微软雅黑"
FONT_HEI = "微软雅黑"
NAVY = RGBColor(0x1B, 0x26, 0x31)
GRAY = RGBColor(0x5D, 0x6D, 0x7E)
RED = RGBColor(0xC0, 0x39, 0x2B)
GREEN = RGBColor(0x1E, 0x84, 0x49)


def set_font(run, name=FONT_CN, size=None, bold=None, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


def para(doc, text="", size=10.5, bold=False, color=None, align=None, space_before=0, space_after=6,
         line=1.45, indent=None, name=FONT_CN):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if indent:
        pf.first_line_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        set_font(r, name, size, bold, color)
    return p


def pct(v, digits=1):
    if v is None:
        return "—"
    return f"{v:+.{digits}f}%"


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_cell(cell, text, size=8.6, bold=False, color=None, align=WD_ALIGN_PARAGRAPH.CENTER, name=FONT_CN):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(1.5)
    p.paragraph_format.space_after = Pt(1.5)
    r = p.add_run(str(text))
    set_font(r, name, size, bold, color)


def table_borders(table, color="D5D8DC", sz=4):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def add_heading(doc, text, level=1, color=NAVY, size=None, space_before=14, space_after=8):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    set_font(r, FONT_HEI, size or (18 if level == 1 else 13.5), True, color)
    return p


def add_page_number_footer(section, text_left="A股申万一级行业龙头股月度股价研究（2024—2026）"):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text_left + "    第 ")
    set_font(r, FONT_CN, 8, False, GRAY)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run_el = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "16")
    rpr.append(sz)
    run_el.append(rpr)
    t = OxmlElement("w:t")
    t.text = "1"
    run_el.append(t)
    fld.append(run_el)
    p._p.append(fld)
    r2 = p.add_run(" 页")
    set_font(r2, FONT_CN, 8, False, GRAY)


doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.left_margin = Cm(2.2)
sec.right_margin = Cm(2.2)
sec.top_margin = Cm(2.0)
sec.bottom_margin = Cm(1.9)

style = doc.styles["Normal"]
style.font.name = FONT_CN
style.font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_CN)

# ===================== 封面 =====================
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(90)
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
r = p.add_run("A股行业研究")
set_font(r, FONT_HEI, 15, True, RGBColor(0x84, 0x8B, 0x94))

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(10)
p.paragraph_format.line_spacing = 1.2
r = p.add_run("2024年以来中国A股\n31个申万一级行业龙头股\n月度股价走势全景")
set_font(r, FONT_HEI, 31, True, NAVY)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(24)
r = p.add_run("覆盖 31 个行业 · 155 只龙头股 · 35 个月度观测\n2024年1月 — 2026年11月")
set_font(r, FONT_CN, 13, False, GRAY)

# 封面分隔线
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(28)
pPr = p._p.get_or_add_pPr()
pbdr = OxmlElement("w:pBdr")
bottom = OxmlElement("w:bottom")
bottom.set(qn("w:val"), "single")
bottom.set(qn("w:sz"), "12")
bottom.set(qn("w:space"), "1")
bottom.set(qn("w:color"), "C0392B")
pbdr.append(bottom)
pPr.append(pbdr)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(150)
r = p.add_run("数据来源：申万宏源研究所（行业分类与权重）、baostock（前复权日线/月K线）\n"
              "数据截止：2026年11月13日收盘　|　报告生成：2026年11月15日\n"
              "本报告仅作数据整理与研究参考，不构成任何投资建议")
set_font(r, FONT_CN, 9, False, GRAY)
p.paragraph_format.line_spacing = 1.6

doc.add_page_break()

# ===================== 摘要 =====================
add_heading(doc, "一、报告摘要与数据说明", 1, space_before=0)

para(doc, "本报告回答三个问题：2024年以来A股有哪些行业板块；每个板块的龙头股分别是谁；"
          "这些龙头股自2024年1月起的月度股价如何演变。", 10.5, False, NAVY, indent=0.0)

para(doc, f"行业划分采用申万宏源研究所《申万行业分类（2021版）》31个一级行业，覆盖全部A股；"
          f"行业成分股及权重取自申万宏源研究所官方发布数据。每个行业内按申万官方权重由高到低排序，"
          f"取前5名作为“龙头”，并剔除2024年后上市、月度数据不足30个月的次新股，最终得到 155 只个股。"
          f"股价采用 baostock 前复权日线收盘价，按月取最后一个交易日收盘价，区间为2024年1月至2026年11月，"
          f"共35个月度观测（2026年11月为截至11月13日的月内数据）。为便于横向比较，图表下半部分以"
          f"{base_month}月末收盘价=100做归一化。", 10.5, indent=0.74)

allcum = [s["cum_return"] for v in industries.values() for s in v["leaders"]]
win = sum(1 for x in allcum if x > 0)
avg_cum = sum(allcum) / len(allcum)
med_cum = sorted(allcum)[len(allcum) // 2]

para(doc, "核心结论", 12, True, RED, space_before=10, space_after=4)
bullets = [
    f"区间内155只龙头股中 {win} 只上涨、{len(allcum)-win} 只下跌，中位数涨幅 {med_cum:+.1f}%，"
    f"平均涨幅 {avg_cum:+.1f}%，同期沪深300上涨 {bmark:+.1f}%，龙头股整体跑赢大盘。",
    "成长方向显著占优：电子（寒武纪 +981.6%）、国防军工（松发股份 +892.7%）、通信（新易盛 +650.4%、"
    "中际旭创 +480.7%、天孚通信 +284.2%）三条AI算力与高端制造链条贡献了最强的区间收益。",
    "传统消费与地产链持续承压：房地产（万科A -70.8%、保利发展 -43.7%）、美容护理（爱美客 -57.7%）、"
    "食品饮料（泸州老窖 -51.0%、五粮液 -41.2%）为跌幅最深的板块。",
    "行业内部分化极大：31个行业中有25个行业，其最强龙头与行业前五平均涨幅的差距超过30个百分点"
    "（电子、国防军工差距分别达685和709个百分点），“买对行业”之外“买对龙头”同样关键。",
]
for b in bullets:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.4
    r = p.add_run(b)
    set_font(r, FONT_CN, 10, False, RGBColor(0x21, 0x2F, 0x3D))

para(doc, "指标口径", 12, True, RED, space_before=10, space_after=4)
items = [
    ("区间累计涨跌", "最新收盘价 ÷ 2023年12月末收盘价 − 1，即2024年以来的累计收益率。"),
    ("年化收益", "以35个月的实际时长折算的复合年化收益率。"),
    ("最大回撤", "月度收盘价序列自历史峰值的最大跌幅，衡量区间内的最大账面损失。"),
    ("年化波动率", "月度收益率标准差 × √12，衡量股价波动幅度。"),
    ("龙头认定", "申万宏源研究所发布的最新行业权重，权重越高代表该股在行业指数中的市值与代表性越强。"),
]
for k, v in items:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.line_spacing = 1.4
    r = p.add_run(f"· {k}：")
    set_font(r, FONT_CN, 10, True, NAVY)
    r2 = p.add_run(v)
    set_font(r2, FONT_CN, 10, False, RGBColor(0x21, 0x2F, 0x3D))

doc.add_picture(os.path.join(CHARTS, "00_总览_行业龙头累计涨跌幅.png"), width=Cm(16.4))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
para(doc, "图0　31个申万一级行业龙头股与龙头前五组合区间累计涨跌幅（2023年12月末—2026年11月13日）",
     8.6, False, GRAY, WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

# ===================== 行业与龙头总表（横向） =====================
new_sec = doc.add_section(WD_SECTION.NEW_PAGE)
new_sec.orientation = WD_ORIENT.LANDSCAPE
new_sec.page_width = Cm(29.7)
new_sec.page_height = Cm(21.0)
new_sec.left_margin = Cm(1.8)
new_sec.right_margin = Cm(1.8)
new_sec.top_margin = Cm(1.6)
new_sec.bottom_margin = Cm(1.4)

add_heading(doc, "二、31个申万一级行业及其龙头前五（总表）", 1, space_before=0, space_after=6)
para(doc, "下表按龙头股区间涨幅由高到低排列。权重为申万官方行业指数权重，区间涨跌为2024年1月至2026年11月13日的累计涨幅。",
     9, False, GRAY, space_after=6)

header = ["行业", "龙头（权重第一）", "区间涨跌", "No.2", "涨跌", "No.3", "涨跌", "No.4", "涨跌", "No.5", "涨跌", "前五均值"]
t = doc.add_table(rows=1, cols=len(header))
t.alignment = WD_TABLE_ALIGNMENT.CENTER
table_borders(t)
widths = [1.6, 2.7, 1.8, 2.7, 1.8, 2.7, 1.8, 2.6, 1.8, 2.6, 1.8, 1.8]
for i, h in enumerate(header):
    c = t.rows[0].cells[i]
    set_cell(c, h, 8.4, True, RGBColor(0xFF, 0xFF, 0xFF))
    shade(c, "1B2631")
for key, info in order:
    ls = sorted(info["leaders"], key=lambda x: -x["weight"])
    row = t.add_row().cells
    set_cell(row[0], info["name"], 8.4, True, NAVY)
    for j, s in enumerate(ls):
        set_cell(row[1 + j * 2], s["name"], 8.4)
        set_cell(row[2 + j * 2], pct(s["cum_return"]), 8.2, False,
                 RED if s["cum_return"] > 0 else GREEN)
    avg = sum(x["cum_return"] for x in ls) / len(ls)
    set_cell(row[11], pct(avg), 8.2, True, RED if avg > 0 else GREEN)
for i, wd in enumerate(widths):
    for row in t.rows:
        row.cells[i].width = Cm(wd)

para(doc, "注：松发股份（603268）2024年完成重大资产重组、主业由陶瓷转向船舶制造，其股价反映重组预期，"
          "并非传统军工业务的内生增长，解读时需注意口径。", 7.8, False, GRAY, space_before=6)

# ===================== 分行业图表（纵向） =====================
new_sec = doc.add_section(WD_SECTION.NEW_PAGE)
new_sec.orientation = WD_ORIENT.PORTRAIT
new_sec.page_width = Cm(21.0)
new_sec.page_height = Cm(29.7)
new_sec.left_margin = Cm(2.2)
new_sec.right_margin = Cm(2.2)
new_sec.top_margin = Cm(2.0)
new_sec.bottom_margin = Cm(1.9)

add_heading(doc, "三、分行业龙头股月度股价走势", 1, space_before=0, space_after=4)
para(doc, "每个行业一页：上图为5只龙头股的月度收盘价（前复权），下图为以2023年12月末=100的归一化走势，"
          "灰虚线为沪深300同期表现；右侧为区间累计涨跌幅；页末表格为各龙头股的区间表现与风险指标。",
     10, False, GRAY, space_after=8)

for idx, (key, info) in enumerate(order, 1):
    ls = sorted(info["leaders"], key=lambda x: -x["weight"])
    if idx > 1:
        doc.add_page_break()
    add_heading(doc, f"3.{idx}　{info['name']}（{SW_CODES[key]}）", 2, space_before=0, space_after=2)
    avg = sum(x["cum_return"] for x in ls) / len(ls)
    best = max(ls, key=lambda x: x["cum_return"])
    worst = min(ls, key=lambda x: x["cum_return"])
    lead = ls[0]
    rel = avg - bmark
    txt = (f"区间内该行业龙头前五等权平均涨跌 {pct(avg)}，"
           f"{'跑赢' if rel >= 0 else '跑输'}沪深300 {abs(rel):.1f}个百分点。"
           f"其中 {best['name']} 表现最强（{pct(best['cum_return'])}），{worst['name']} 表现最弱（{pct(worst['cum_return'])}）；"
           f"权重第一的龙头 {lead['name']}（申万权重 {lead['weight']:.2f}%）区间{pct(lead['cum_return'])}，"
           f"最大回撤 {lead['mdd']:.1f}%，年化波动率 {lead['annual_vol']:.1f}%。")
    para(doc, txt, 9.3, False, RGBColor(0x21, 0x2F, 0x3D), space_after=4, line=1.3)

    doc.add_picture(os.path.join(CHARTS, f"{SW_CODES[key]}_{info['name']}.png"), width=Cm(16.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    header = ["排名", "股票", "申万权重", "基期价", "最新价", "区间涨跌", "年化收益", "最大回撤", "年化波动", "最佳月", "最差月"]
    t = doc.add_table(rows=1, cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_borders(t, "E5E8E8", 4)
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        set_cell(c, h, 7.6, True, RGBColor(0xFF, 0xFF, 0xFF))
        shade(c, "34495E")
    for i, s in enumerate(ls):
        row = t.add_row().cells
        set_cell(row[0], "龙头" if i == 0 else f"No.{i+1}", 7.6, i == 0, RED if i == 0 else GRAY)
        set_cell(row[1], f"{s['name']}\n{s['code']}", 7.4, i == 0, NAVY)
        set_cell(row[2], f"{s['weight']:.2f}%", 7.6)
        set_cell(row[3], f"{s['base_close']:.2f}", 7.6)
        set_cell(row[4], f"{s['last_close']:.2f}", 7.6, True)
        set_cell(row[5], pct(s["cum_return"]), 7.6, True, RED if s["cum_return"] > 0 else GREEN)
        set_cell(row[6], pct(s["cagr"]), 7.6)
        set_cell(row[7], f"{s['mdd']:.1f}%", 7.6)
        set_cell(row[8], f"{s['annual_vol']:.1f}%", 7.6)
        set_cell(row[9], f"{s['best']['month']}\n{pct(s['best']['ret'])}", 7.2, False,
                 RED if s["best"]["ret"] > 0 else GREEN)
        set_cell(row[10], f"{s['worst']['month']}\n{pct(s['worst']['ret'])}", 7.2, False,
                 RED if s["worst"]["ret"] > 0 else GREEN)
    col_w = [1.25, 2.35, 1.3, 1.25, 1.25, 1.45, 1.35, 1.25, 1.25, 1.75, 1.75]
    for i, wd in enumerate(col_w):
        for row in t.rows:
            row.cells[i].width = Cm(wd)
    para(doc, "注：基期价为2023年12月末收盘价，最新价为2026年11月13日收盘价，均为前复权价；"
              "最大回撤、年化波动率基于月末收盘序列计算。", 7.2, False, GRAY, space_before=3, space_after=0)

# ===================== 附录：全部155只明细（横向） =====================
new_sec = doc.add_section(WD_SECTION.NEW_PAGE)
new_sec.orientation = WD_ORIENT.LANDSCAPE
new_sec.page_width = Cm(29.7)
new_sec.page_height = Cm(21.0)
new_sec.left_margin = Cm(1.5)
new_sec.right_margin = Cm(1.5)
new_sec.top_margin = Cm(1.5)
new_sec.bottom_margin = Cm(1.4)

add_heading(doc, "附录　155只行业龙头股区间表现明细", 1, space_before=0, space_after=4)
para(doc, "按申万行业代码排序；区间涨跌、年化收益、最大回撤、波动率的统计口径与正文一致。", 8.6, False, GRAY, space_after=4)

header = ["行业", "排名", "代码", "名称", "权重", "市值\n(亿元)", "基期价", "最新价",
          "区间涨跌", "年化收益", "最大回撤", "年化波动", "最佳月", "最差月"]
t = doc.add_table(rows=1, cols=len(header))
t.alignment = WD_TABLE_ALIGNMENT.CENTER
table_borders(t, "E5E8E8", 4)
for i, h in enumerate(header):
    c = t.rows[0].cells[i]
    set_cell(c, h, 7.4, True, RGBColor(0xFF, 0xFF, 0xFF))
    shade(c, "1B2631")

for key, info in sorted(industries.items(), key=lambda kv: kv[0]):
    for i, s in enumerate(sorted(info["leaders"], key=lambda x: -x["weight"])):
        row = t.add_row().cells
        set_cell(row[0], info["name"], 7.2)
        set_cell(row[1], "龙头" if i == 0 else f"{i+1}", 7.2, i == 0, RED if i == 0 else GRAY)
        set_cell(row[2], s["code"], 7.2)
        set_cell(row[3], s["name"], 7.2, i == 0, NAVY)
        set_cell(row[4], f"{s['weight']:.2f}%", 7.0)
        set_cell(row[5], f"{float(s['mktcap']):,.0f}" if s.get("mktcap") else "—", 7.0)
        set_cell(row[6], f"{s['base_close']:.2f}", 7.0)
        set_cell(row[7], f"{s['last_close']:.2f}", 7.0)
        set_cell(row[8], pct(s["cum_return"]), 7.2, True, RED if s["cum_return"] > 0 else GREEN)
        set_cell(row[9], pct(s["cagr"]), 7.0)
        set_cell(row[10], f"{s['mdd']:.1f}%", 7.0)
        set_cell(row[11], f"{s['annual_vol']:.1f}%", 7.0)
        set_cell(row[12], f"{s['best']['month']} {pct(s['best']['ret'])}", 6.8)
        set_cell(row[13], f"{s['worst']['month']} {pct(s['worst']['ret'])}", 6.8)
col_w = [1.9, 1.25, 1.65, 2.3, 1.5, 1.7, 1.4, 1.4, 1.7, 1.7, 1.6, 1.6, 2.7, 2.7]
for i, wd in enumerate(col_w):
    for row in t.rows:
        row.cells[i].width = Cm(wd)

para(doc, "免责声明：本报告基于公开数据整理，行业权重与价格数据可能存在发布时点差异；历史表现不代表未来收益，"
          "报告内容不构成投资建议。", 8, False, GRAY, space_before=6)

add_page_number_footer(doc.sections[0])
add_page_number_footer(doc.sections[1])
add_page_number_footer(doc.sections[2])
add_page_number_footer(doc.sections[3])

docx_path = os.path.join(BASE, "A股31个申万一级行业龙头股月度股价走势研究_2024-2026.docx")
doc.save(docx_path)
print("saved", docx_path, round(os.path.getsize(docx_path) / 1024 / 1024, 2), "MB")

