# A股行业龙头股月度行情 · 项目总览

> 31 个申万一级行业 × 每行业权重前五龙头 × 2024 年以来月度股价。
> 本目录包含「研究报告（离线脚本）」与「本地 Web 服务」两部分。
>
> **接手项目请先读 [`AGENTS.md`](AGENTS.md)**（项目完整长期记忆；工作区根 `../AGENTS.md` 只是加载器），
> 再读 [`service/docs/README.md`](service/docs/README.md)。
> 当前状态看 [`service/docs/10-当前状态.md`](service/docs/10-当前状态.md)，计划看 [`service/docs/11-路线图.md`](service/docs/11-路线图.md)。

---

## 1. 目录结构

```
astock_sectors\
├─ service\                     ★ 日常维护对象：本地 Web 服务
│  ├─ backend\                   FastAPI + SQLAlchemy + baostock 同步
│  ├─ frontend\                  React + Vite + ECharts
│  ├─ data\astock.db             SQLite 数据库（5,616 行行情）
│  ├─ docs\                      工程文档 00~09 + 自检脚本
│  ├─ start.sh                   一键启动（bash，3999）
│  ├─ stop.sh                    停止服务（按端口）
│  └─ docker-compose.mysql.yml   阶段二 MySQL
│
├─ data\                        研究数据（服务种子来源）
│  ├─ selection.json             31 行业 × 前五 + 权重
│  ├─ bs_month.json              155 只 + 沪深300 月度收盘（baostock）
│  ├─ sw_components.json         申万全量成分与权重
│  ├─ shortlist.json             候选前八 + 市值
│  ├─ panel.json                 研究面板（图表/报告输入）
│  └─ kline_month\               早期腾讯月K缓存（仅 select_leaders 判定数据月数用）
│
├─ 交付\                        最终交付物（唯一权威副本）
│  ├─ ...研究_2024-2026.pdf       42 页研究报告
│  ├─ ...研究_2024-2026.docx      可编辑版
│  ├─ ...行情数据_2024-2026.xlsx  数据工作簿（含 31 张图）
│  ├─ 图表PNG\                    32 张 PNG
│  ├─ 原始数据CSV\                6 个 CSV
│  └─ 00_龙头股一览表.md
│
├─ archive\                     归档：一次性脚本、失败的探针、旧数据
│  ├─ one-off-scripts\           17 个一次性脚本（probe/腾讯抓取/校验）
│  └─ data-probes\               交叉校验报告、旧 kline 元数据
│
├─ vendor\                      Python 依赖（matplotlib/docx/lxml/baostock 等，离线用）
├─ 服务化设计方案.md              改造前的方案分析
└─ *.py                         研究报告管道（10 个脚本，见 §3）
```

---

## 2. 日常使用（服务）

```bash
cd service
./start.sh           # → http://127.0.0.1:3999（Git Bash）
./stop.sh            # 停止
```

- 页面：总览 / 行业详情
- 接口文档：<http://127.0.0.1:3999/docs>
- 详细说明：[service/README.md](service/README.md)、[service/docs/](service/docs/README.md)

---

## 3. 重新生成研究报告（v0.1 管道）

按顺序执行（工作目录 `astock_sectors\`，需联网）：

| 步骤 | 脚本 | 产出 |
|---|---|---|
| 1 | `python fetch_sw_components.py` | `data/sw_components.json`（31 行业成分与权重） |
| 2 | `python fetch_shortlist.py` | `data/shortlist.json`（候选前八 + 市值） |
| 3 | `python select_leaders.py` | `data/selection.json`（每行业前五，依赖 `data/kline_month` 判月数） |
| 4 | `python fetch_baostock.py` | `data/bs_month.json`（前复权月度收盘） |
| 5 | `python build_panel.py` | `data/panel.json`（月末序列 + 指标） |
| 6 | `python make_charts.py` | `charts/`（32 张 PNG，运行后重建） |
| 7 | `python make_docx.py` | 根目录 `*.docx` |
| 8 | `python make_xlsx.py` | 根目录 `*.xlsx` |
| 9 | `python export_data.py` | `out_data/`（CSV） |
| 10 | `python assemble.py` | 汇总到 `交付/`（PNG/CSV/清单） |

> 依赖：`vendor\`（matplotlib、python-docx、XlsxWriter、lxml、baostock）。
> 第 7 步需要本机 Word（用 COM 导出 PDF）。
> 第 7~9 步会先在根目录生成 docx/xlsx/CSV 中间产物，第 10 步复制到 `交付\`；全部完成后可删除根目录中间产物，**只保留 `交付\` 这一份**。

---

## 4. 清理记录（2026-11-15）

为降低维护噪音，做了以下清理，净减少约 **139 MB**（清理前约 372 MB → 现在 233 MB）、约 530 个文件：

| 处理 | 对象 | 原因 |
|---|---|---|
| 删除 | `_tmp\`（90.6 MB）、`_mplcache\`、`__pycache__` | 构建/调试临时产物，可重建 |
| 删除 | 根目录同名 `.docx`/`.pdf`/`.xlsx` | 与 `交付\` 完全重复（哈希一致） |
| 删除 | `charts\`、`out_data\` | 与 `交付\图表PNG\`、`交付\原始数据CSV\` 重复 |
| 删除 | `data\kline_month2\`、`kline2_meta.json` | 腾讯方案已废弃，改 baostock |
| 删除 | `data\sina_industry.json`、`sw_first_raw.csv` | 失败的探查数据 |
| 删除 | `vendor\pymupdf`、`fitz`（14.8 MB） | PyMuPDF 在 Python 3.13 上不可用，未使用 |
| 删除 | `tools\PdfToPng.cs` | 失败的尝试 |
| 归档 | 17 个一次性脚本 → `archive\one-off-scripts\` | 留档不参与运行 |
| 归档 | `crosscheck_report.json`、`kline_meta.json` → `archive\data-probes\` | 校验证据，体积小 |

保留项及理由：

- `data\kline_month\`（0.6 MB）：`select_leaders.py` 用它判定「月度数据是否 ≥30 个月」，删了会破坏前五筛选的可复现性。
- `vendor\`（63 MB）：离线依赖；matplotlib 等仅研究报告管道需要，服务只用其中的 baostock。
- `service\frontend\node_modules\`（114 MB）：离线重新构建前端所需。
- `交付\`：交付物唯一权威副本，不再在根目录保留第二份。

### 2026-11-17 追加

| 处理 | 对象 | 说明 |
|---|---|---|
| 转存并删除 | 工作区根 `_acl_reports\` | ACL 修复的备份与报告（3 个文件）→ `_local_only\system-acl-2026-11-15\`（仓库外） |
| 删除 | 工作区根 `_tmp\` | 空目录（matplotlib 缓存残留） |
| 删除 | 79 个 `__pycache__`（10.5 MB） | 由 `clean.ps1` 清理（现为 `clean.sh`） |
| 移动 | `AGENTS.md` 主体 | 迁入 `astock_sectors\AGENTS.md`；工作区根只留加载器 |

> 工作区根 `D:\deepseek` 现在只有 `astock_sectors\` 与 `AGENTS.md`。

---

## 5. 维护约定

1. **服务改动**：先读 `service/docs/00`、`02`、`03`、`06`；改完跑 `python service/docs/_check_docs.py`。
2. **口径改动**：`service/backend/app/config.py` / `seed.py` / `service/docs/00` 三处同步。
3. **不要混用行情源**（腾讯/新浪/baostock 前复权口径不同）。
4. **交付物只改 `交付\`**，不要在根目录再放一份。
5. 建议对本目录执行 `git init` 并提交（`.gitignore` 已准备好，排除了 `node_modules`、`vendor`、数据库与临时文件）。
