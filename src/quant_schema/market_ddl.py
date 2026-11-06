"""market_ddl — ``market.duckdb`` 的结构契约。

一个 DuckDB 文件里放两个组件：

* ``warehouse``：基础行情（股票 / 指数 / ETF / 交易日历），``component='warehouse'``；
* ``factor``：因子层（因子目录、因子值、可交易标记、质量统计），``component='factor'``。

本模块只定义 ``Table`` 对象与静态视图 SQL，不执行任何 DDL。
``data_pipeline/scripts/init_market_db.py`` 与 ``init_factor_db.py``
负责在单个事务里执行这些语句并写入版本行。
"""

from __future__ import annotations

from typing import Final

from . import constants as c
from ._ddl import Table

# ---------------------------------------------------------------------------
# warehouse 组件：基础行情
# ---------------------------------------------------------------------------
WAREHOUSE_TABLES: Final[tuple[Table, ...]] = (
    Table(
        name=c.META_SCHEMA_VERSION,
        columns=(
            ("component", "VARCHAR NOT NULL"),
            ("version", "VARCHAR NOT NULL"),
            ("applied_at", "TIMESTAMPTZ NOT NULL DEFAULT current_timestamp"),
        ),
        constraints=("PRIMARY KEY (component)",),
        description="各组件 schema 版本；warehouse 与 factor 各占一行",
    ),
    Table(
        name=c.META_INGEST_LOG,
        columns=(
            ("table_name", "VARCHAR NOT NULL"),
            ("scope_key", "VARCHAR NOT NULL"),
            ("row_count", "BIGINT NOT NULL DEFAULT 0"),
            ("status", "VARCHAR NOT NULL"),
            ("detail", "VARCHAR"),
            ("started_at", "TIMESTAMPTZ NOT NULL"),
            ("finished_at", "TIMESTAMPTZ"),
        ),
        constraints=("PRIMARY KEY (table_name, scope_key)",),
        description="数据摄入批次日志（幂等覆盖同一 scope）",
    ),
    Table(
        name=c.DIM_STOCK_BASIC,
        columns=(
            ("ts_code", "VARCHAR NOT NULL"),
            ("symbol", "VARCHAR"),
            ("name", "VARCHAR"),
            ("area", "VARCHAR"),
            ("industry", "VARCHAR"),
            ("market", "VARCHAR"),
            ("exchange", "VARCHAR"),
            ("list_status", "VARCHAR NOT NULL"),
            ("list_date", "DATE"),
            ("delist_date", "DATE"),
            ("is_hs", "VARCHAR"),
        ),
        constraints=("PRIMARY KEY (ts_code)",),
        description="股票基础信息（维度表）",
    ),
    Table(
        name=c.DIM_TRADE_CAL,
        columns=(
            ("exchange", "VARCHAR NOT NULL"),
            ("cal_date", "DATE NOT NULL"),
            ("is_open", "BOOLEAN NOT NULL"),
            ("pretrade_date", "DATE"),
        ),
        constraints=("PRIMARY KEY (exchange, cal_date)",),
        description="交易所交易日历",
    ),
    Table(
        name=c.FACT_DAILY,
        columns=(
            ("ts_code", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("open", "DOUBLE"),
            ("high", "DOUBLE"),
            ("low", "DOUBLE"),
            ("close", "DOUBLE"),
            ("pre_close", "DOUBLE"),
            ("chg", "DOUBLE"),
            ("pct_chg", "DOUBLE"),
            ("vol", "DOUBLE"),
            ("amount", "DECIMAL(20,4)"),
        ),
        constraints=("PRIMARY KEY (ts_code, trade_date)",),
        description="股票日线行情（不复权）",
    ),
    Table(
        name=c.FACT_ADJ_FACTOR,
        columns=(
            ("ts_code", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("adj_factor", "DOUBLE"),
        ),
        constraints=("PRIMARY KEY (ts_code, trade_date)",),
        description="股票复权因子",
    ),
    Table(
        name=c.FACT_DAILY_BASIC,
        columns=(
            ("ts_code", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("turnover_rate", "DOUBLE"),
            ("turnover_rate_f", "DOUBLE"),
            ("volume_ratio", "DOUBLE"),
            ("pe", "DOUBLE"),
            ("pe_ttm", "DOUBLE"),
            ("pb", "DOUBLE"),
            ("ps", "DOUBLE"),
            ("ps_ttm", "DOUBLE"),
            ("dv_ratio", "DOUBLE"),
            ("dv_ttm", "DOUBLE"),
            ("total_share", "DOUBLE"),
            ("float_share", "DOUBLE"),
            ("free_share", "DOUBLE"),
            ("total_mv", "DECIMAL(20,4)"),
            ("circ_mv", "DECIMAL(20,4)"),
        ),
        constraints=("PRIMARY KEY (ts_code, trade_date)",),
        description="股票每日指标（市值、换手、估值）",
    ),
    Table(
        name=c.FACT_STK_LIMIT,
        columns=(
            ("ts_code", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("pre_close", "DOUBLE"),
            ("up_limit", "DOUBLE"),
            ("down_limit", "DOUBLE"),
        ),
        constraints=("PRIMARY KEY (ts_code, trade_date)",),
        description="股票每日涨跌停价",
    ),
    Table(
        name=c.FACT_INDEX_DAILY,
        columns=(
            ("index_code", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("open", "DOUBLE"),
            ("high", "DOUBLE"),
            ("low", "DOUBLE"),
            ("close", "DOUBLE"),
            ("pre_close", "DOUBLE"),
            ("chg", "DOUBLE"),
            ("pct_chg", "DOUBLE"),
            ("vol", "DOUBLE"),
            ("amount", "DECIMAL(20,4)"),
        ),
        constraints=("PRIMARY KEY (index_code, trade_date)",),
        description="指数日线行情（外部基准的数据来源）",
    ),
    Table(
        name=c.FACT_INDEX_WEIGHT,
        columns=(
            ("index_code", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("con_code", "VARCHAR NOT NULL"),
            ("weight", "DOUBLE"),
        ),
        constraints=("PRIMARY KEY (index_code, trade_date, con_code)",),
        description="指数成分权重快照（动态标的池的数据来源）",
    ),
    Table(
        name=c.FACT_FUND_DAILY,
        columns=(
            ("ts_code", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("open", "DOUBLE"),
            ("high", "DOUBLE"),
            ("low", "DOUBLE"),
            ("close", "DOUBLE"),
            ("pre_close", "DOUBLE"),
            ("chg", "DOUBLE"),
            ("pct_chg", "DOUBLE"),
            ("vol", "DOUBLE"),
            ("amount", "DECIMAL(20,4)"),
        ),
        constraints=("PRIMARY KEY (ts_code, trade_date)",),
        description="ETF/基金日线行情（ETF 基准的数据来源）",
    ),
)

_QFQ_SQL: Final[str] = """
WITH base AS (
    SELECT d.ts_code, d.trade_date, d.open, d.high, d.low, d.close, d.pre_close,
           d.chg, d.pct_chg, d.vol, d.amount, f.adj_factor
    FROM fact_daily d
    JOIN fact_adj_factor f
      ON f.ts_code = d.ts_code AND f.trade_date = d.trade_date
),
last_adj AS (
    SELECT ts_code, arg_max(adj_factor, trade_date) AS adj_last
    FROM fact_adj_factor GROUP BY ts_code
)
SELECT b.ts_code, b.trade_date,
       b.open      * b.adj_factor / l.adj_last AS open,
       b.high      * b.adj_factor / l.adj_last AS high,
       b.low       * b.adj_factor / l.adj_last AS low,
       b.close     * b.adj_factor / l.adj_last AS close,
       b.pre_close * b.adj_factor / l.adj_last AS pre_close,
       b.chg       * b.adj_factor / l.adj_last AS chg,
       b.pct_chg, b.vol,
       CAST(b.amount * b.adj_factor / l.adj_last AS DECIMAL(20,4)) AS amount,
       b.adj_factor
FROM base b JOIN last_adj l ON l.ts_code = b.ts_code
"""

_HFQ_SQL: Final[str] = """
SELECT d.ts_code, d.trade_date,
       d.open      * f.adj_factor AS open,
       d.high      * f.adj_factor AS high,
       d.low       * f.adj_factor AS low,
       d.close     * f.adj_factor AS close,
       d.pre_close * f.adj_factor AS pre_close,
       d.vol,
       CAST(d.amount * f.adj_factor AS DECIMAL(20,4)) AS amount,
       f.adj_factor
FROM fact_daily d
JOIN fact_adj_factor f ON f.ts_code = d.ts_code AND f.trade_date = d.trade_date
"""

WAREHOUSE_VIEWS: Final[dict[str, str]] = {
    "v_daily_qfq": _QFQ_SQL,
    "v_daily_hfq": _HFQ_SQL,
}

# ---------------------------------------------------------------------------
# factor 组件：因子层（同一个 market.duckdb）
# ---------------------------------------------------------------------------
FACTOR_TABLES: Final[tuple[Table, ...]] = (
    Table(
        name=c.META_FACTOR_REGISTRY,
        columns=(
            ("factor_id", "INTEGER NOT NULL"),
            ("factor_name", "VARCHAR NOT NULL"),
            ("factor_group", "VARCHAR"),
            ("value_type", "VARCHAR NOT NULL"),
            ("direction", "SMALLINT NOT NULL DEFAULT 1"),
            ("lookback_days", "INTEGER"),
            ("formula_hash", "VARCHAR"),
            ("description", "VARCHAR"),
            ("is_active", "BOOLEAN NOT NULL DEFAULT TRUE"),
        ),
        constraints=(
            "PRIMARY KEY (factor_id)",
            "UNIQUE (factor_name)",
        ),
        description="因子目录（活跃因子决定 v_factor_wide 的列）",
    ),
    Table(
        name=c.FACT_FACTOR_DAILY,
        columns=(
            ("ts_code", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("factor_id", "INTEGER NOT NULL"),
            ("value", "DOUBLE"),
            ("is_stale", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("source_batch_id", "BIGINT"),
        ),
        constraints=("PRIMARY KEY (ts_code, trade_date, factor_id)",),
        description="长表因子值",
    ),
    Table(
        name=c.FACT_TRADABLE_FLAG,
        columns=(
            ("ts_code", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("is_suspended", "BOOLEAN NOT NULL"),
            ("is_st", "BOOLEAN NOT NULL"),
            ("is_limit_up", "BOOLEAN NOT NULL"),
            ("is_limit_down", "BOOLEAN NOT NULL"),
            ("is_buyable", "BOOLEAN NOT NULL"),
            ("is_sellable", "BOOLEAN NOT NULL"),
            ("in_universe", "BOOLEAN NOT NULL"),
        ),
        constraints=("PRIMARY KEY (ts_code, trade_date)",),
        description="每日可交易标记（供因子有效性过滤）",
    ),
    Table(
        name=c.FACT_FACTOR_QUALITY,
        columns=(
            ("factor_id", "INTEGER NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("n_total", "BIGINT NOT NULL"),
            ("n_valid", "BIGINT NOT NULL"),
            ("n_stale", "BIGINT NOT NULL"),
            ("n_outlier", "BIGINT NOT NULL"),
            ("coverage", "DOUBLE NOT NULL"),
            ("computed_at", "TIMESTAMPTZ NOT NULL DEFAULT now()"),
        ),
        constraints=("PRIMARY KEY (factor_id, trade_date)",),
        description="因子每日质量统计",
    ),
)

# 注意：is_buyable OR is_sellable 会保留“可卖不可买”的涨停股；
# 方向过滤必须由策略层用 fact_tradable_flag 的对应列完成，视图不做方向假设。
FACTOR_VALID_VIEW_SQL: Final[str] = """
SELECT
    f.ts_code,
    f.trade_date,
    f.factor_id,
    f.value,
    f.is_stale
FROM fact_factor_daily f
JOIN fact_tradable_flag t
  ON t.ts_code = f.ts_code
 AND t.trade_date = f.trade_date
WHERE t.is_buyable = TRUE
   OR t.is_sellable = TRUE
""".strip()

#: 静态视图；``v_factor_wide`` 依赖活跃因子列表，由 init_factor_db 动态创建。
FACTOR_STATIC_VIEWS: Final[dict[str, str]] = {
    "v_factor_valid": FACTOR_VALID_VIEW_SQL,
}

#: factor 组件初始化前必须存在的 warehouse 表。
FACTOR_REQUIRED_WAREHOUSE_TABLES: Final[tuple[str, ...]] = (
    c.META_INGEST_LOG,
    c.DIM_STOCK_BASIC,
    c.DIM_TRADE_CAL,
    c.FACT_DAILY,
    c.FACT_ADJ_FACTOR,
    c.FACT_DAILY_BASIC,
    c.FACT_STK_LIMIT,
)
