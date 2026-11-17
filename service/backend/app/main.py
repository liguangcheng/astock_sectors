# -*- coding: utf-8 -*-
"""FastAPI 入口：API + 前端静态资源（生产形态只暴露 3999 一个端口）。"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import router as api_router
from .config import CORS_ORIGINS, FRONTEND_DIST, HOST, PORT
from .db import init_db
from .sync_service import version_info

app = FastAPI(title="A股行业龙头股行情服务", version="1.0.0",
              description="31 个申万一级行业 · 155 只龙头股 · 月度股价与增量同步")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def _startup() -> None:
    init_db()
    from .repo import repo
    fixed = repo.mark_stale_sync_logs()
    if fixed:
        print(f"[astock] 已将 {fixed} 条残留 running 同步日志标记为 failed")
    print(f"[astock] 服务启动 http://{HOST}:{PORT}  {version_info()}")


@app.get("/api")
def api_root():
    return {"service": "astock", "docs": "/docs", "port": PORT}


if FRONTEND_DIST.exists():
    assets = FRONTEND_DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/", include_in_schema=False)
    def placeholder():
        return JSONResponse({"service": "astock", "message": "前端尚未构建，请执行 frontend: npm install && npm run build"})
