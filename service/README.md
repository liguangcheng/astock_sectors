# A股行业龙头股 · 本地前后端分离服务

31 个申万一级行业 × 每行业权重前五龙头 × 月度股价折线图。
后端 FastAPI（`127.0.0.1:3999`），前端 React + Vite + ECharts，数据先用 **SQLite 单文件**，后续可无缝换 MySQL。

> 完整工程文档见 **[docs/README.md](docs/README.md)**：项目记忆、架构、数据结构、接口、部署、开发指南、待办与决策记录。
> 新接手请先读 [docs/00-项目记忆.md](docs/00-项目记忆.md)；**当前状态**看 [docs/10-当前状态.md](docs/10-当前状态.md)，**计划**看 [docs/11-路线图.md](docs/11-路线图.md)。

![总览页](docs/preview-overview.png)

---

## 1. 快速开始

```powershell
cd D:\deepseek\astock_sectors\service
.\start.cmd
```

`start.cmd` 会绕过 Windows 默认的脚本执行策略限制（内部调用 `start.ps1`）：

- 若服务已在运行 → 直接打开浏览器，不会重复启动；
- 缺前端产物 → 自动 `npm install && npm run build`；
- 端口被其他程序占用 → 报错并列出占用进程。

PowerShell 7 用户也可以直接 `.\start.ps1`；Windows PowerShell 5.1 下若提示「禁止运行脚本」，用 `.\start.cmd` 或
`powershell -ExecutionPolicy Bypass -File .\start.ps1`。

手动启动：

```powershell
cd backend
python run.py            # 生产模式，3999 同时提供 API 与页面
python run.py --reload   # 开发模式，改代码自动重载
```

前端开发（热更新，需另开一个终端）：

```powershell
cd frontend
npm run dev              # http://127.0.0.1:5173 ，/api 已代理到 3999
```

---

## 2. 目录结构

```
service/
├─ backend/
│  ├─ app/
│  │  ├─ config.py         # 端口、数据库 URL、业务口径
│  │  ├─ db.py             # SQLAlchemy Core 表结构（SQLite / MySQL 共用）
│  │  ├─ repo.py           # 仓储层：唯一的数据读写出口
│  │  ├─ analytics.py      # 月末聚合、累计收益、回撤、波动率、归一化
│  │  ├─ seed.py           # 从既有研究成果导入 155×35 初始数据
│  │  ├─ sync_service.py   # baostock 增量同步（单飞、复权重叠校验）
│  │  ├─ api.py            # REST API
│  │  └─ main.py           # FastAPI 入口 + 前端静态托管
│  ├─ vendor/              # 随仓库携带的 Python 依赖（离线可用）
│  ├─ requirements.txt
│  └─ run.py               # 启动入口
├─ frontend/
│  ├─ src/pages/           # Overview / Industry 两个页面
│  ├─ src/components/      # ECharts 封装（折线图、总览柱状图）
│  └─ dist/                # 构建产物，由后端托管
├─ data/astock.db          # SQLite 数据库（当前阶段）
├─ docker-compose.mysql.yml# 阶段二 MySQL（3307）
├─ .env.example
└─ start.ps1
```

---

## 3. API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 存活检查 |
| GET | `/api/data/version` | 数据水位线：最新交易日、上次同步时间、是否需要刷新 |
| GET | `/api/industries` | 31 个行业 + 各自前五龙头 |
| GET | `/api/industries/{code}` | 单行业详情：5 只龙头的月度序列 + 指标 + 沪深300 |
| GET | `/api/overview` | 总览：各行业龙头/前五均值区间涨跌 |
| GET | `/api/prices?codes=300308,300502&start=2024-01` | 任意股票组合的月度序列 |
| GET | `/api/export.csv?codes=...` | 导出 CSV |
| POST | `/api/sync` | 触发增量同步（异步任务，返回 jobId） |
| GET | `/api/sync/{jobId}` | 任务进度 |
| GET | `/api/sync/logs` | 同步历史 |
| GET | `/api/admin/quality` | 数据体检（需 `X-Admin-Token`） |
| PUT | `/api/admin/stocks/{code}` | 维护权重/排序（需 `X-Admin-Token`） |

交互式文档：<http://127.0.0.1:3999/docs>

---

## 4. 增量同步怎么工作

1. 页面加载先调 `/api/data/version`，比较「库内最新交易日」与「应到交易日」。
2. 需要刷新时自动 `POST /api/sync`，并轮询任务进度；完成后只把新增月份并入图表。
3. 服务端以「全局水位线 + 单只水位线」决定抓取窗口（通常 1~5 个交易日），
   baostock 按股票逐只拉前复权日线，`INSERT ... ON CONFLICT` 幂等写入。
4. **复权漂移校验**：分红送转会让前复权历史整体重算。同步时比对「同一月份的重叠收盘价」，
   偏差超过 0.5% 就重抓该股全历史并整体替换，避免新旧数据拼接断裂。
5. 同一时刻只允许一个同步任务（单飞锁）；15:05 前不把当天算作已收盘。

---

## 5. 数据初始化 / 重置

```powershell
cd backend
$env:PYTHONPATH=".;.\vendor;..\..\vendor"
python -m app.seed          # 导入 155 只 × 35 个月（覆盖写入）
```

删除 `service/data/astock.db` 后重新执行 `python -m app.seed` 即可重置。

---

## 6. 切换到 MySQL（阶段二）

**推荐：容器化（Docker Desktop）**，端口映射 3307，避免与本机 3306 冲突：

```powershell
cd service
docker compose -f docker-compose.mysql.yml up -d
```

然后：

```powershell
# 1) 安装驱动（或放进 backend/vendor）
python -m pip install pymysql

# 2) 用环境变量指向 MySQL（.env 里放开注释即可）
$env:ASTOCK_DATABASE_URL="mysql+pymysql://astock:astock-pass@127.0.0.1:3307/astock?charset=utf8mb4"

# 3) 建表 + 灌入种子数据（与 SQLite 同一套 DDL）
cd backend
$env:PYTHONPATH=".;.\vendor;..\..\vendor"
python -m app.seed

# 4) 启动，页面数据应与 SQLite 完全一致
python run.py
```

代码里只有 `repo.py` 的 upsert 分方言处理（SQLite / MySQL），其余业务无感。
若暂时不想装 Docker，可用 MySQL 8.4 **ZIP 免安装版**解压到 `D:\mysql` 后
`mysqld --initialize-insecure` + `mysqld --console` 启动，同样监听 3307。

---

## 7. 常见问题

| 现象 | 处理 |
|---|---|
| 端口 3999 被占用 | `Get-NetTCPConnection -LocalPort 3999` 找到 PID 后结束，或改 `ASTOCK_PORT` |
| 页面提示「前端尚未构建」 | 在 `frontend` 执行 `npm install && npm run build` |
| 同步失败、提示 baostock 断线 | 再点一次「同步最新数据」；服务端已有 3 次重试与重新登录 |
| 页面数据不更新 | 非交易日不会产生新数据；15:05 后才把当天计入 |
| 想恢复初始数据 | 删除 `service/data/astock.db` 后重新 `python -m app.seed` |

---

## 8. 与既有研究成果的关系

初始数据来自上一阶段的成果（`../data/selection.json`、`../data/bs_month.json`、`../data/sw_components.json`），
与《A股31个申万一级行业龙头股月度股价走势研究》报告口径一致：申万 2021 版分类、权重前五、前复权月末收盘、2023-12 为归一化基期。
