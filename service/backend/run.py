# -*- coding: utf-8 -*-
"""启动入口：把随仓库携带的依赖目录加入 sys.path，再启动 uvicorn。

    python run.py            # 127.0.0.1:3999
    python run.py --reload   # 开发模式热重载
"""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
SERVICE = BACKEND.parent
PARENT_VENDOR = SERVICE.parent / "vendor"      # 复用 astock_sectors/vendor（baostock 等）
LOCAL_VENDOR = BACKEND / "vendor"              # 后端依赖（fastapi/sqlalchemy 等）

for p in (str(LOCAL_VENDOR), str(PARENT_VENDOR)):
    if p not in sys.path and Path(p).exists():
        sys.path.insert(0, p)

# 让 matplotlib 之类不在服务里用到，但保证 MPL 缓存不写到只读目录
os.environ.setdefault("MPLCONFIGDIR", str(BACKEND / ".mplcache"))

import uvicorn  # noqa: E402

from app.config import HOST, PORT  # noqa: E402

if __name__ == "__main__":
    reload = "--reload" in sys.argv
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=reload, log_level="info")
