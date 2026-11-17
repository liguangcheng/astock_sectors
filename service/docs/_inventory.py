# -*- coding: utf-8 -*-
"""盘点服务现状：路由、表结构、行数、依赖版本，供文档核对。"""
import os
import sqlite3
import sys

from pathlib import Path
SERVICE = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, os.path.join(SERVICE, "backend", "vendor"))
sys.path.insert(0, os.path.join(os.path.dirname(SERVICE), "vendor"))
sys.path.insert(0, os.path.join(SERVICE, "backend"))

from app.main import app  # noqa: E402

print("=== ROUTES ===")
for r in app.routes:
    methods = ",".join(sorted(getattr(r, "methods", []) or []))
    if methods:
        print(f"{methods:14s} {getattr(r, 'path', '')}")

print("\n=== TABLES ===")
db = os.path.join(SERVICE, "data", "astock.db")
c = sqlite3.connect(db)
for (name,) in c.execute("select name from sqlite_master where type='table' order by name"):
    cnt = c.execute(f"select count(*) from {name}").fetchone()[0]
    print(f"{name:14s} rows={cnt}")
    for row in c.execute(f"pragma table_info({name})"):
        cid, col, typ, notnull, default, pk = row
        print(f"    {col:16s} {typ:12s} notnull={notnull} pk={pk} default={default}")
    for idx in c.execute(f"pragma index_list({name})"):
        print(f"    INDEX {idx[1]} unique={idx[2]}")

print("\n=== VERSIONS ===")
import fastapi, sqlalchemy, uvicorn, pydantic  # noqa: E402
print("fastapi", fastapi.__version__)
print("sqlalchemy", sqlalchemy.__version__)
print("uvicorn", uvicorn.__version__)
print("pydantic", pydantic.VERSION)
print("python", sys.version.split()[0])
