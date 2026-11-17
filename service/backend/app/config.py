# -*- coding: utf-8 -*-
"""全局配置：路径、端口、数据库地址、业务口径。

配置优先级：进程环境变量 > service/.env > 代码默认值。
"""
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
SERVICE_DIR = BACKEND_DIR.parent

# 加载 service/.env（若存在且 python-dotenv 可用）；不覆盖已存在的进程环境变量
try:
    from dotenv import load_dotenv

    load_dotenv(SERVICE_DIR / ".env", override=False)
except Exception:  # 依赖缺失时退化为纯环境变量
    pass

DATA_DIR = Path(os.environ.get("ASTOCK_DATA_DIR", SERVICE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 数据库：阶段一 SQLite；阶段二把 ASTOCK_DATABASE_URL 换成 mysql+pymysql://... 即可
DATABASE_URL = os.environ.get("ASTOCK_DATABASE_URL", f"sqlite:///{(DATA_DIR / 'astock.db').as_posix()}")

HOST = os.environ.get("ASTOCK_HOST", "127.0.0.1")
PORT = int(os.environ.get("ASTOCK_PORT", "3999"))

# 业务口径
BASE_MONTH = os.environ.get("ASTOCK_BASE_MONTH", "2023-12")   # 归一化基期
SEED_FROM = os.environ.get("ASTOCK_SEED_FROM", "2023-12-01")  # 全量同步起点
HISTORY_START = os.environ.get("ASTOCK_HISTORY_START", "2024-01")

ADMIN_TOKEN = os.environ.get("ASTOCK_ADMIN_TOKEN", "local-dev-token")
CORS_ORIGINS = [o for o in os.environ.get(
    "ASTOCK_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",") if o]

FRONTEND_DIST = SERVICE_DIR / "frontend" / "dist"

# 上游数据源
BAOSTOCK_VENDOR = (SERVICE_DIR.parent / "vendor").as_posix()  # 复用 astock_sectors/vendor 里的 baostock
OVERLAP_TOLERANCE = 0.005   # 重叠月份收盘价偏差超过 0.5% 判定为复权因子变化，触发单只重建
