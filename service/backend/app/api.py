# -*- coding: utf-8 -*-
"""REST API：查询、总览、增量同步、数据维护。"""
from __future__ import annotations

import csv
import io
from typing import Iterable

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from . import analytics
from .config import ADMIN_TOKEN, BASE_MONTH, HISTORY_START
from .repo import repo
from .sync_service import job_status, start_sync, version_info

router = APIRouter()

BENCH_CODE = "000300"
BENCH_NAME = "沪深300"


def _require_admin(token: str | None) -> None:
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="X-Admin-Token 无效")


def _monthly_for(codes: Iterable[str]) -> dict[str, list[dict]]:
    rows = repo.prices_for(list(codes))
    grouped = analytics.group_by_code(rows)
    return {code: analytics.to_monthly(items) for code, items in grouped.items()}


def _industry_leaders(code: str) -> list[dict]:
    return repo.list_stocks(code)


# ---------------- 基础 ----------------
@router.get("/health")
def health():
    return {"status": "ok", "rows": repo.count_rows(), "lastTradeDate": repo.max_trade_date(),
            "baseMonth": BASE_MONTH}


@router.get("/data/version")
def data_version():
    return version_info()


# ---------------- 行业 / 龙头 ----------------
@router.get("/industries")
def industries():
    inds = repo.list_industries()
    stocks = repo.list_stocks()
    by_code: dict[str, list[dict]] = {}
    for s in stocks:
        by_code.setdefault(s["industry_code"], []).append(s)
    out = []
    for i in inds:
        leaders = sorted(by_code.get(i["code"], []), key=lambda x: x["rank"])
        out.append({**i, "leaders": [{"code": s["code"], "name": s["name"], "weight": s["weight"],
                                      "rank": s["rank"]} for s in leaders]})
    return out


@router.get("/industries/{code}")
def industry_detail(code: str):
    ind = next((i for i in repo.list_industries() if i["code"] == code), None)
    if not ind:
        raise HTTPException(404, "行业不存在")
    leaders = _industry_leaders(code)
    monthly = _monthly_for([s["code"] for s in leaders] + [BENCH_CODE])
    items = []
    for s in leaders:
        m = monthly.get(s["code"], [])
        items.append({**s, "series": m, "metrics": analytics.metrics(m)})
    bench = analytics.metrics(monthly.get(BENCH_CODE, []))
    all_cum = [x["metrics"]["cum_return"] for x in items if x["metrics"]["cum_return"] is not None]
    return {"code": code, "name": ind["name"], "stockCount": ind["stock_count"], "leaders": items,
            "benchmark": {"name": BENCH_NAME, "metrics": bench, "series": monthly.get(BENCH_CODE, [])},
            "avgCumReturn": round(sum(all_cum) / len(all_cum), 2) if all_cum else None,
            "baseMonth": BASE_MONTH}


@router.get("/overview")
def overview():
    inds = repo.list_industries()
    stocks = repo.list_stocks()
    by_ind: dict[str, list[dict]] = {}
    for s in stocks:
        by_ind.setdefault(s["industry_code"], []).append(s)
    monthly = _monthly_for([s["code"] for s in stocks] + [BENCH_CODE])
    out = []
    for i in inds:
        leaders = sorted(by_ind.get(i["code"], []), key=lambda x: x["rank"])
        cums = []
        for s in leaders:
            m = analytics.metrics(monthly.get(s["code"], []))
            cums.append((s, m))
        valid = [m["cum_return"] for _, m in cums if m["cum_return"] is not None]
        top = cums[0][1] if cums else None
        out.append({
            "code": i["code"], "name": i["name"], "stockCount": i["stock_count"],
            "leader": {"code": cums[0][0]["code"], "name": cums[0][0]["name"],
                       "weight": cums[0][0]["weight"]} if cums else None,
            "leaderCumReturn": top["cum_return"] if top else None,
            "avgCumReturn": round(sum(valid) / len(valid), 2) if valid else None,
            "maxCumReturn": max(valid) if valid else None,
            "minCumReturn": min(valid) if valid else None,
        })
    bench = analytics.metrics(monthly.get(BENCH_CODE, []))
    return {"industries": out, "benchmark": {"name": BENCH_NAME, "cumReturn": bench["cum_return"]},
            "baseMonth": BASE_MONTH}


# ---------------- 价格序列 ----------------
@router.get("/prices")
def prices(codes: str = Query(..., description="逗号分隔的股票代码，可含 000300"),
           start: str = Query(HISTORY_START, description="YYYY-MM"),
           end: str | None = Query(None, description="YYYY-MM"),
           normalize: bool = Query(True)):
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        raise HTTPException(400, "codes 不能为空")
    if len(code_list) > 60:
        raise HTTPException(400, "一次最多查询 60 只")
    monthly = _monthly_for(code_list)
    months = sorted({m["month"] for series in monthly.values() for m in series if m["month"] >= start
                     and (end is None or m["month"] <= end)})
    stocks = {s["code"]: s for s in repo.list_stocks()}
    series = []
    for code in code_list:
        raw = {x["month"]: x for x in monthly.get(code, [])}
        points = []
        for m in months:
            p = raw.get(m)
            points.append({"month": m, "close": p["close"] if p else None,
                           "ret": p["ret"] if p else None, "norm": p["norm"] if p else None})
        s = stocks.get(code)
        series.append({
            "code": code,
            "name": s["name"] if s else (BENCH_NAME if code == BENCH_CODE else code),
            "isBenchmark": code == BENCH_CODE,
            "weight": s["weight"] if s else None,
            "metrics": analytics.metrics(monthly.get(code, [])),
            "series": points,
        })
    return {"months": months, "series": series, "normalize": normalize, "baseMonth": BASE_MONTH}


@router.get("/export.csv")
def export_csv(codes: str = Query(...), start: str = Query(HISTORY_START)):
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    monthly = _monthly_for(code_list)
    stocks = {s["code"]: s for s in repo.list_stocks()}
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf)
    writer.writerow(["行业", "代码", "名称", "月份", "月末收盘", "月涨跌%", "归一化"])
    for code in code_list:
        s = stocks.get(code, {})
        for p in monthly.get(code, []):
            if p["month"] < start:
                continue
            writer.writerow([s.get("industry_code", ""), code, s.get("name", BENCH_NAME if code == BENCH_CODE else code),
                             p["month"], p["close"], p["ret"], p["norm"]])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": 'attachment; filename="prices.csv"'})


# ---------------- 同步 ----------------
@router.post("/sync")
def sync_now(trigger: str = Query("page", pattern="^(page|manual|seed)$")):
    job = start_sync(trigger)
    return {"jobId": job["jobId"], "status": job["status"], "reused": job.get("reused", False)}


@router.get("/sync/logs")
def sync_logs(limit: int = Query(20, ge=1, le=200)):
    return repo.list_logs(limit)


@router.get("/sync/{job_id}")
def sync_status(job_id: str):
    job = job_status(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return job


# ---------------- 维护 ----------------
@router.get("/admin/quality")
def quality(x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    stocks = repo.list_stocks()
    inds = {i["code"]: i for i in repo.list_industries()}
    issues = []
    for s in stocks:
        rows = repo.prices_for([s["code"]])
        months = sorted({r["trade_date"][:7] for r in rows})
        expected = analytics.month_range(BASE_MONTH, months[-1]) if months else []
        missing = [m for m in expected if m not in months]
        if missing:
            issues.append({"code": s["code"], "name": s["name"], "type": "missing_month",
                           "detail": ",".join(missing[:12])})
        if s["industry_code"] not in inds:
            issues.append({"code": s["code"], "name": s["name"], "type": "orphan_industry",
                           "detail": s["industry_code"]})
    return {"checked": len(stocks), "issues": issues, "total": len(issues)}


@router.put("/admin/stocks/{code}")
def update_stock(code: str, payload: dict, x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    s = repo.get_stock(code)
    if not s:
        raise HTTPException(404, "股票不存在")
    allowed = {k: payload[k] for k in ("name", "weight", "rank", "is_leader", "mktcap") if k in payload}
    if not allowed:
        raise HTTPException(400, "没有可更新字段")
    repo.upsert_stocks([{**{k: s[k] for k in ("code", "name", "industry_code", "weight", "rank", "mktcap", "is_leader")},
                         **allowed}])
    return {"ok": True, "stock": repo.get_stock(code)}
