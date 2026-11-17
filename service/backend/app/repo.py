# -*- coding: utf-8 -*-
"""仓储层：所有读写都走这里，换成 MySQL 只需换 DATABASE_URL。"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .db import engine, industry, price_daily, stock, sync_log, sync_state

TZ = ZoneInfo("Asia/Shanghai")


def now_str() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")


class Repo:
    # ---------- 维度 ----------
    def list_industries(self) -> list[dict]:
        with engine.connect() as c:
            rows = c.execute(select(industry).order_by(industry.c.sort_order, industry.c.code)).mappings().all()
        return [dict(r) for r in rows]

    def list_stocks(self, industry_code: str | None = None) -> list[dict]:
        stmt = select(stock)
        if industry_code:
            stmt = stmt.where(stock.c.industry_code == industry_code)
        stmt = stmt.order_by(stock.c.industry_code, stock.c.rank)
        with engine.connect() as c:
            return [dict(r) for r in c.execute(stmt).mappings().all()]

    def get_stock(self, code: str) -> dict | None:
        with engine.connect() as c:
            return c.execute(select(stock).where(stock.c.code == code)).mappings().first()

    def upsert_industries(self, rows: Iterable[dict]) -> None:
        rows = list(rows)
        if not rows:
            return
        with engine.begin() as c:
            for r in rows:
                exists = c.execute(select(industry.c.code).where(industry.c.code == r["code"])).first()
                if exists:
                    c.execute(update(industry).where(industry.c.code == r["code"]).values(**r))
                else:
                    c.execute(insert(industry).values(**r))

    def upsert_stocks(self, rows: Iterable[dict]) -> None:
        rows = list(rows)
        if not rows:
            return
        with engine.begin() as c:
            for r in rows:
                r.setdefault("updated_at", now_str())
                exists = c.execute(select(stock.c.code).where(stock.c.code == r["code"])).first()
                if exists:
                    c.execute(update(stock).where(stock.c.code == r["code"]).values(**r))
                else:
                    c.execute(insert(stock).values(**r))

    # ---------- 行情 ----------
    def upsert_prices(self, rows: Sequence[dict]) -> int:
        if not rows:
            return 0
        dialect = engine.dialect.name
        if dialect == "mysql":
            stmt = mysql_insert(price_daily).values(list(rows))
            stmt = stmt.on_duplicate_key_update(
                close=stmt.inserted.close, volume=stmt.inserted.volume, source=stmt.inserted.source)
        else:
            stmt = sqlite_insert(price_daily).values(list(rows))
            stmt = stmt.on_conflict_do_update(
                index_elements=["code", "trade_date"],
                set_={"close": stmt.excluded.close, "volume": stmt.excluded.volume,
                      "source": stmt.excluded.source},
            )
        with engine.begin() as c:
            c.execute(stmt)
        return len(rows)

    def replace_symbol(self, code: str, rows: Sequence[dict]) -> None:
        with engine.begin() as c:
            c.execute(delete(price_daily).where(price_daily.c.code == code))
            if rows:
                c.execute(insert(price_daily), list(rows))

    def prices_for(self, codes: Sequence[str], start: str | None = None, end: str | None = None) -> list[dict]:
        if not codes:
            return []
        stmt = select(price_daily).where(price_daily.c.code.in_(list(codes)))
        if start:
            stmt = stmt.where(price_daily.c.trade_date >= start)
        if end:
            stmt = stmt.where(price_daily.c.trade_date <= end)
        stmt = stmt.order_by(price_daily.c.code, price_daily.c.trade_date)
        with engine.connect() as c:
            return [dict(r) for r in c.execute(stmt).mappings().all()]

    def month_close(self, code: str, month: str) -> float | None:
        with engine.connect() as c:
            row = c.execute(
                select(price_daily.c.close)
                .where(price_daily.c.code == code, price_daily.c.trade_date >= f"{month}-01")
                .where(price_daily.c.trade_date <= f"{month}-31")
                .order_by(price_daily.c.trade_date.desc()).limit(1)
            ).first()
        return float(row[0]) if row else None

    def close_on(self, code: str, trade_date: str) -> float | None:
        """取某只股票在指定交易日的收盘价（用于复权重叠校验）。"""
        with engine.connect() as c:
            row = c.execute(
                select(price_daily.c.close)
                .where(price_daily.c.code == code, price_daily.c.trade_date == trade_date)
            ).first()
        return float(row[0]) if row else None

    def max_trade_date(self, code: str | None = None) -> str | None:
        stmt = select(func.max(price_daily.c.trade_date))
        if code:
            stmt = stmt.where(price_daily.c.code == code)
        with engine.connect() as c:
            v = c.execute(stmt).scalar()
        return str(v) if v else None

    def count_rows(self) -> int:
        with engine.connect() as c:
            return int(c.execute(select(func.count()).select_from(price_daily)).scalar() or 0)

    # ---------- 同步状态 ----------
    def get_state(self, key: str, default: str | None = None) -> str | None:
        with engine.connect() as c:
            row = c.execute(select(sync_state.c.value).where(sync_state.c.key == key)).first()
        return row[0] if row else default

    def set_state(self, key: str, value: str) -> None:
        with engine.begin() as c:
            exists = c.execute(select(sync_state.c.key).where(sync_state.c.key == key)).first()
            if exists:
                c.execute(update(sync_state).where(sync_state.c.key == key).values(value=value))
            else:
                c.execute(insert(sync_state).values(key=key, value=value))

    def add_log(self, **kw) -> int:
        with engine.begin() as c:
            res = c.execute(insert(sync_log).values(**kw))
            return int(res.inserted_primary_key[0])

    def update_log(self, log_id: int, **kw) -> None:
        with engine.begin() as c:
            c.execute(update(sync_log).where(sync_log.c.id == log_id).values(**kw))

    def list_logs(self, limit: int = 20) -> list[dict]:
        with engine.connect() as c:
            rows = c.execute(select(sync_log).order_by(sync_log.c.id.desc()).limit(limit)).mappings().all()
        return [dict(r) for r in rows]

    def mark_stale_sync_logs(self, note: str = "aborted: 服务重启（任务状态在内存，已丢失）") -> int:
        """启动时把上次残留的 running 日志标记为失败，避免审计数据永远停在 running。"""
        with engine.begin() as c:
            res = c.execute(
                update(sync_log)
                .where(sync_log.c.status == "running")
                .values(status="failed", finished_at=now_str(), message=note)
            )
            return int(res.rowcount or 0)


repo = Repo()
