# AGENTS.md · 项目长期记忆（astock_sectors）

> 本文件是 **A 股行业龙头股月度行情项目**的完整记忆，位于项目根目录。
> 工作区根目录 `D:\deepseek\AGENTS.md` 是一个极简「加载器」，只负责指向本文件。
> 接手任务前：**先读本文件 → `service/docs/10-当前状态.md` → `service/docs/11-路线图.md`**。
> 最后更新：2026-11-17　|　服务版本：v0.2.2

---

## 1. 项目是什么

两阶段合一的本地项目：

1. **v0.1 研究报告**（离线 Python 脚本）：31 个申万一级行业 × 每行业权重前五龙头 × 2024 年以来月度股价，
   产出 42 页 PDF、Excel、32 张 PNG，交付物在 `交付/`。
2. **v0.2 本地服务**（当前主战场）：把研究结果做成前后端分离服务，
   FastAPI（`127.0.0.1:3999`）+ React/Vite/ECharts + SQLite，支持增量同步。
   代码在 `service/`，文档在 `service/docs/`。

---

## 2. 快速命令

```powershell
# 启动服务（自动开浏览器；.cmd 绕过 PowerShell 执行策略）
cd D:\deepseek\astock_sectors\service
.\start.cmd

# 仅后端（看日志）
cd D:\deepseek\astock_sectors\service\backend
python run.py

# 前端开发（热更新，5173 代理到 3999）
cd D:\deepseek\astock_sectors\service\frontend
npm run dev

# 重新构建前端
cd D:\deepseek\astock_sectors\service\frontend
npm run build

# 重置数据库并导入种子
cd D:\deepseek\astock_sectors\service\backend
$env:PYTHONPATH=".;.\vendor;..\..\vendor"
python -m app.seed

# 清理缓存（不动数据/依赖）
cd D:\deepseek\astock_sectors
.\clean.cmd
```

健康检查：`Invoke-RestMethod http://127.0.0.1:3999/api/health`

---

## 3. 关键事实（别猜，直接记）

| 项 | 值 |
|---|---|
| 项目根 | `D:\deepseek\astock_sectors` |
| 服务目录 | `D:\deepseek\astock_sectors\service` |
| 服务端口 | 3999（`ASTOCK_PORT` 可改），只绑 `127.0.0.1` |
| 前端 | React 18 + TS + Vite 5 + ECharts 5；生产由后端托管 `frontend/dist` |
| 后端 | Python 3.13 + FastAPI 0.163 + SQLAlchemy 2.1（Core，非 ORM） |
| 数据库 | SQLite `service/data/astock.db`，5 张表；种子 5,616 行，当前行数以 `docs/10` 为准 |
| 数据范围 | 31 行业 / 155 龙头 + 沪深300 / 2023-12 起 / 前复权 |
| 行情源 | **只用 baostock**（个股 adjustflag=2，指数 adjustflag=3） |
| 行业与权重 | 申万宏源官网 `institute-sw/api/index_publish/details/component_stocks/` |
| 归一化基期 | 2023-12（=100） |
| 基准 | 沪深300，代码 `000300`，存在 `price_daily` 但不在 `stock` 表 |
| 依赖安装 | 已 vendor 到 `service/backend/vendor`（Python）与 `frontend/node_modules`（Node） |
| 文档 | `service/docs/00`~`12`，索引 `service/docs/README.md` |

---

## 4. 不可违反的约定

1. **只有 `repo.py` 能访问数据库**；新查询加方法，不要在 `api.py` 里 `engine.connect()`。
2. **不要在 `api.py` 里 import baostock**；同步逻辑只在 `sync_service.py`。
3. **不要混用行情源**：腾讯/新浪与 baostock 的前复权口径不同（实测差 1~13 个百分点，个别 187）。
4. **前复权会漂移**：必须保留「精确重叠日校验 + 偏差 >0.5% 整只重建 + 上月兜底」。
5. **种子有截断日**：`seed.py` 的 `SEED_CUTOFF = "2026-11-13"`，防止未来日期进入水位线。
6. **改口径三处同步**：`config.py` / `seed.py` / `service/docs/00-项目记忆.md`，然后重跑 seed。
7. **接口/表结构变更必须更新文档**：`docs/03`、`docs/04`、`docs/09`。
8. **每次发布或事件后更新 `docs/10-当前状态.md`**；每个版本勾选 `docs/11-路线图.md`。
9. **交付物只放 `交付/`**，不要在根目录再生成第二份；一次性脚本放 `archive/one-off-scripts/`。

---

## 5. 本机环境坑（已踩过，别重复踩）

| 坑 | 表现 | 处理 |
|---|---|---|
| 工作区 ACL 异常 | 写 `D:\deepseek` 报 `Windows ACL workspace grant failed` | 用 DSH `diagnose-windows-sandbox-acl` 修复；报告已存 `_local_only/system-acl-2026-11-15/`（仓库外） |
| pip 安装 | 临时目录权限 + pypi 极慢，经常卡死 | **不要用 pip**；用 `service/vendor_backend2.py`（清华镜像）解压 wheel |
| npm install / vite build | 沙箱里 `spawn EPERM` | 需 `danger-full-access` 一次性执行，`TMP/TEMP` 指到工作区 |
| Edge 无头截图 | mojo/命名管道被拒 | 需 `danger-full-access` + `--no-sandbox` + 工作区 `--user-data-dir` |
| PowerShell 写 UTF-8 | `Set-Content -Encoding UTF8` 加 BOM，Vite 解析 `package.json` 失败 | 用 write 工具；`.ps1` 必须带 BOM（5.1 才能解析中文） |
| PowerShell 执行策略 | 直接跑 `.ps1` 报「禁止运行脚本」 | 用 `start.cmd` / `clean.cmd` |
| 没有 LibreOffice | `office_render` 渲染 docx 失败 | Word COM 导出 PDF；PDF 转图用无头 Edge 截图 HTML |
| baostock 不稳定 | 偶发 `timed out` / `接收数据异常`，同步可能长时间卡住 | 已加 20s socket 超时与启动自愈；仍在 v0.2.3 增加总超时/熔断（见 11） |

---

## 6. 数据口径速查

- 行业：申万一级 31 个（2021 版）。
- 龙头：行业权重前五（`stock.rank` 1~5），剔除 2024 后上市不足 30 个月的次新股。
- 价格：baostock 前复权，月末最后一个交易日；2026-11 起含逐日增量。
- 指标：区间累计、年化（按实际月数）、最大回撤（月末序列）、年化波动（月收益标准差 × √12）。
- 2026-11-15 快照：沪深300 `+17.06%`，155 只中 114 只上涨，中位数 `+29.2%`，均值 `+59.3%`。
- 特殊样本：松发股份（603268）2024 年重组，`+892.7%` 反映重组预期，引用时必须加注脚。

---

## 7. 当前状态与计划（指向权威文档）

| 想知道 | 看哪里 |
|---|---|
| 现在什么状态（行数/最新交易日/事件/已知问题） | `service/docs/10-当前状态.md` |
| 接下来做什么（v0.2.3 → v1.0） | `service/docs/11-路线图.md` |
| 任务池、14 条技术债、风险 | `service/docs/07-待办与技术债.md` |
| 关键决策理由 | `service/docs/08-决策记录.md` |

**速览**：P1–P4 已完成；P5 维护页、P6 MySQL、P7 工程化未做。
下一步 **v0.2.3 同步稳定性**：总超时/熔断、任务落库、失败清单、进度展示。

---

## 8. 文档索引

| 想知道什么 | 读哪篇 |
|---|---|
| 业务背景、口径、术语、坑 | `service/docs/00-项目记忆.md` |
| 为什么做、验收标准 | `service/docs/01-背景与目标.md` |
| 分层、请求链路、并发、部署 | `service/docs/02-架构设计.md` |
| 表结构、数据流、MySQL 映射 | `service/docs/03-数据结构.md` |
| 12 个接口的参数与响应 | `service/docs/04-接口文档.md` |
| 启动、环境变量、排障 | `service/docs/05-运行与部署.md` |
| 加接口/加页面/换库 | `service/docs/06-开发指南.md` |
| 任务池、技术债、风险 | `service/docs/07-待办与技术债.md` |
| 关键决策理由 | `service/docs/08-决策记录.md` |
| 改了什么 | `service/docs/09-变更日志.md` |
| **当前状态** | `service/docs/10-当前状态.md` |
| **路线图** | `service/docs/11-路线图.md` |
| 开源前敏感信息扫描 | `service/docs/12-开源发布检查.md`、`_secret_scan.py` |
| 改造前的方案分析 | `服务化设计方案.md` |

---

## 9. 修改后的自检

1. `python run.py` 起得来，`/api/health` 200。
2. `npm run build` 通过（tsc 无报错）。
3. 页面能出图，行业下钻正常。
4. 动过数据/表结构 → 31 行业、155 龙头、156 个代码（含基准），`lastTradeDate` = 应到交易日。
5. `service/docs/10-当前状态.md` 已更新（版本/行数/最新日期/已知问题）。
6. `service/docs/11-路线图.md` 已勾选/调整。
7. `service/docs/09-变更日志.md` 已追加。
8. 无 `running` 残留 `sync_log`；`python service/docs/_check_docs.py` 通过。
9. 推送 GitHub 前：`python service/docs/_secret_scan.py` 高危为 0（见 `docs/12`）。

---

## 10. 目录结构

```
astock_sectors\
├─ service\        ★ 服务（backend/frontend/data/docs/start.cmd）
├─ data\           研究数据（selection/bs_month/sw_components/shortlist/panel/kline_month）
├─ 交付\           交付物唯一权威副本（pdf/docx/xlsx/PNG/CSV）
├─ archive\        one-off-scripts（17）、data-probes（2）；ACL 报告已移出仓库
├─ vendor\         研究管道 Python 依赖
├─ README.md       项目总览
├─ clean.cmd/.ps1  缓存清理
└─ *.py            10 个研究报告脚本
```

历史清理（2026-11-15）：删除 `_tmp`/`_mplcache`/`__pycache__`/重复交付物/`charts`/`out_data`/`kline_month2`/`pymupdf`，净减约 139 MB。
2026-11-17：根目录 `_acl_reports`、`_tmp` 已清空删除（ACL 报告转存 `_local_only/system-acl-2026-11-15/`（仓库外）），工作区根只保留 `astock_sectors/` 与加载器 `AGENTS.md`。
