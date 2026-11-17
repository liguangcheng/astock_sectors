# -*- coding: utf-8 -*-
"""增量同步：baostock 前复权日线 → SQLite/MySQL。单飞执行，页面刷新触发。"""
from __future__ import annotations

import socket
import sys
import threading
import time
import uuid
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .config import BAOSTOCK_VENDOR, HISTORY_START, OVERLAP_TOLERANCE, SEED_FROM
from .repo import now_str, repo

if BAOSTOCK_VENDOR not in sys.path:
    sys.path.insert(0, BAOSTOCK_VENDOR)

TZ = ZoneInfo("Asia/Shanghai")
_LOCK = threading.Lock()
_JOBS: dict[str, dict[str, Any]] = {}
_RUNNING: dict[str, Any] = {"jobId": None}


def _bs():
    import baostock as bs  # noqa: WPS433 (vendored, 延迟导入)
    return bs


def _symbol(code: str) -> str:
    # 基准指数 000300 在上交所；其余按 6/9 开头归沪市，其余归深市
    if code == "000300":
        return "sh.000300"
    return ("sh." if code.startswith(("6", "9")) else "sz.") + code


def _query(code: str, start: str, end: str) -> list[dict]:
    bs = _bs()
    adjust = "3" if code == "000300" else "2"   # 指数不除权；个股前复权
    rs = bs.query_history_k_data_plus(_symbol(code), "date,close,volume",
                                     start_date=start, end_date=end, frequency="d", adjustflag=adjust)
    if rs.error_code != "0":
        raise RuntimeError(f"{code}: {rs.error_msg}")
    out = []
    while rs.next():
        d, close, vol = rs.get_row_data()
        if close and float(close) > 0:
            out.append({"code": code, "trade_date": d, "close": float(close),
                        "volume": float(vol) if vol else None, "source": "baostock"})
    return out


def _today() -> str:
    return datetime.now(TZ).date().isoformat()


def expected_trade_date() -> str:
    """最近一个应当已有收盘数据的交易日（15:05 前算上一个工作日）。"""
    now = datetime.now(TZ)
    d = now.date()
    if now.weekday() < 5 and (now.hour, now.minute) >= (15, 5):
        return d.isoformat()
    d = d - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.isoformat()


def job_status(job_id: str) -> dict | None:
    return _JOBS.get(job_id)


def current_job() -> dict | None:
    jid = _RUNNING.get("jobId")
    return _JOBS.get(jid) if jid else None


def _set(job: dict, **kw) -> None:
    job.update(kw)


def _prev_month(ym: str) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    m -= 1
    if m == 0:
        y, m = y - 1, 12
    return f"{y:04d}-{m:02d}"


def _drift(code: str, rows: list[dict], sym_last: str | None, global_last: str) -> float | None:
    """复权漂移检测。

    优先用「库内最后交易日」这一个精确重叠日比较收盘价——不会被新交易日涨跌干扰；
    若该日期不是真实交易日（种子数据按月末工作日近似过），退化为「上一个完整月份」的月末收盘比较。
    """
    by_date = {r["trade_date"]: r["close"] for r in rows}
    if sym_last and sym_last in by_date:
        db_close = repo.close_on(code, sym_last)
        if db_close:
            return abs(by_date[sym_last] / db_close - 1)
        return None
    check_month = _prev_month(global_last[:7])
    db_close = repo.month_close(code, check_month)
    fetched_close = next((r["close"] for r in reversed(rows) if r["trade_date"][:7] == check_month), None)
    if db_close and fetched_close:
        return abs(fetched_close / db_close - 1)
    return None


def _run(job: dict) -> None:
    bs = _bs()
    started = time.time()
    log_id = repo.add_log(started_at=now_str(), trigger=job["trigger"], status="running",
                          window_start=None, window_end=_today(), message="")
    added = rebuilt = 0
    try:
        # baostock 的 socket 读取默认无超时，卡住会让同步永不结束
        socket.setdefaulttimeout(20)
        bs.login()
        codes = [s["code"] for s in repo.list_stocks()] + ["000300"]
        global_last = repo.max_trade_date() or SEED_FROM
        prev_month_start = f"{_prev_month(global_last[:7])}-01"
        # 窗口至少覆盖「上一个完整月份」，保证退化比对有数据可用
        base_start = min((date.fromisoformat(global_last) - timedelta(days=15)).isoformat(), prev_month_start)
        _set(job, window_start=base_start, total=len(codes), done=0)
        repo.update_log(log_id, window_start=base_start)

        for i, code in enumerate(codes, start=1):
            sym_last = repo.max_trade_date(code)
            try:
                rows = _query(code, base_start, _today())
            except Exception as exc:  # 单只失败不影响整体
                _set(job, done=i, message=f"{code} 拉取失败: {exc}")
                continue
            if not rows:
                _set(job, done=i)
                continue

            drift = _drift(code, rows, sym_last, global_last)
            if drift is not None and drift > OVERLAP_TOLERANCE:
                full = _query(code, SEED_FROM, _today())
                repo.replace_symbol(code, full)
                rebuilt += 1
                added += len(full)
            else:
                new_rows = [r for r in rows if not sym_last or r["trade_date"] > sym_last]
                if new_rows:
                    added += repo.upsert_prices(new_rows)
            _set(job, done=i, addedRows=added, rebuilt=rebuilt)

        bs.logout()
        latest = repo.max_trade_date()
        repo.set_state("last_trade_date", latest or "")
        repo.set_state("last_sync_at", now_str())
        repo.set_state("last_sync_status", "ok")
        repo.update_log(log_id, finished_at=now_str(), added_rows=added, rebuilt=rebuilt, status="ok",
                        message=f"耗时 {time.time() - started:.1f}s")
        _set(job, status="done", finishedAt=now_str(), addedRows=added, rebuilt=rebuilt,
             latestDate=latest, durationMs=int((time.time() - started) * 1000), message="")
    except Exception as exc:
        try:
            bs.logout()
        except Exception:
            pass
        repo.set_state("last_sync_status", "failed")
        repo.update_log(log_id, finished_at=now_str(), status="failed", added_rows=added,
                        rebuilt=rebuilt, message=str(exc)[:400])
        _set(job, status="failed", finishedAt=now_str(), error=str(exc)[:400],
             durationMs=int((time.time() - started) * 1000))
    finally:
        _RUNNING["jobId"] = None


def start_sync(trigger: str = "manual") -> dict:
    """启动（或复用进行中的）同步任务，立即返回任务信息。"""
    with _LOCK:
        if _RUNNING.get("jobId"):
            job = _JOBS[_RUNNING["jobId"]]
            job["reused"] = True
            return job
        job_id = uuid.uuid4().hex[:12]
        job = {"jobId": job_id, "status": "running", "trigger": trigger, "startedAt": now_str(),
               "addedRows": 0, "rebuilt": 0, "done": 0, "total": 0, "message": "", "reused": False}
        _JOBS[job_id] = job
        _RUNNING["jobId"] = job_id
        # 只保留最近 20 个任务
        for k in list(_JOBS)[:-20]:
            _JOBS.pop(k, None)
        threading.Thread(target=_run, args=(job,), daemon=True, name=f"sync-{job_id}").start()
        return job


def version_info() -> dict:
    last = repo.max_trade_date()
    expected = expected_trade_date()
    last_sync = repo.get_state("last_sync_at")
    running = _RUNNING.get("jobId")
    return {
        "lastTradeDate": last,
        "expectedTradeDate": expected,
        "lastSyncAt": last_sync,
        "needsRefresh": bool(last and last < expected) or bool(last is None),
        "syncing": bool(running),
        "rows": repo.count_rows(),
    }
