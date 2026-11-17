# -*- coding: utf-8 -*-
"""数据库引擎与表结构（SQLAlchemy Core，SQLite / MySQL 共用）。"""
from sqlalchemy import (Boolean, Column, Float, ForeignKey, Integer, MetaData, String, Table, Text,
                        create_engine)

from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True,
                       connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

metadata = MetaData()

industry = Table(
    "industry", metadata,
    Column("code", String(16), primary_key=True),
    Column("name", String(32), nullable=False),
    Column("stock_count", Integer, nullable=False, default=0),
    Column("sort_order", Integer, nullable=False, default=0),
)

stock = Table(
    "stock", metadata,
    Column("code", String(8), primary_key=True),
    Column("name", String(32), nullable=False),
    Column("industry_code", String(16), ForeignKey("industry.code"), nullable=False, index=True),
    Column("weight", Float, nullable=False, default=0.0),
    Column("rank", Integer, nullable=False, default=0),
    Column("mktcap", Float, nullable=True),
    Column("is_leader", Boolean, nullable=False, default=True),
    Column("updated_at", String(32), nullable=True),
)

price_daily = Table(
    "price_daily", metadata,
    Column("code", String(8), primary_key=True),
    Column("trade_date", String(10), primary_key=True),
    Column("close", Float, nullable=False),
    Column("volume", Float, nullable=True),
    Column("source", String(16), nullable=False, default="baostock"),
)

sync_state = Table(
    "sync_state", metadata,
    Column("key", String(64), primary_key=True),
    Column("value", String(512), nullable=True),
)

sync_log = Table(
    "sync_log", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("started_at", String(32), nullable=False),
    Column("finished_at", String(32), nullable=True),
    Column("trigger", String(16), nullable=False, default="manual"),
    Column("window_start", String(10), nullable=True),
    Column("window_end", String(10), nullable=True),
    Column("added_rows", Integer, nullable=False, default=0),
    Column("rebuilt", Integer, nullable=False, default=0),
    Column("status", String(16), nullable=False, default="running"),
    Column("message", Text, nullable=True),
)


def init_db() -> None:
    metadata.create_all(engine)
