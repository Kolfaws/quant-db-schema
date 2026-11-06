"""backtest_ddl — ``backtest.duckdb`` 的结构契约。

回测库只服务于“策略配置 → 净值 → 基准/超额”的评价闭环：

* ``bt_runs``           一次策略回测的配置与状态；
* ``bt_nav``            策略日频净值（由 quant-backtest-engine 写入）；
* ``bt_benchmarks``     基准定义（由 quant-baseline 从配置同步）；
* ``bt_baselines``      基准日频点位（由 quant-baseline 写入）；
* ``bt_baseline_weights`` 合成基准的每日成分权重；
* ``bt_run_metrics``    绩效指标（由 quant-backtest-engine 计算）；
* ``bt_compute_log``    基准/回测计算批次日志；
* ``meta_schema_version`` 独立版本表，``component='backtest'``。

本模块只定义 ``Table`` 对象与视图 SQL，不执行 DDL。
"""

from __future__ import annotations

from typing import Final

from . import constants as c
from ._ddl import Table

BACKTEST_TABLES: Final[tuple[Table, ...]] = (
    Table(
        name=c.META_SCHEMA_VERSION,
        columns=(
            ("component", "VARCHAR NOT NULL"),
            ("version", "VARCHAR NOT NULL"),
            ("applied_at", "TIMESTAMPTZ NOT NULL DEFAULT current_timestamp"),
        ),
        constraints=("PRIMARY KEY (component)",),
        description="backtest 组件独立版本行（component='backtest'）",
    ),
    Table(
        name=c.BT_BENCHMARKS,
        columns=(
            ("benchmark_id", "VARCHAR NOT NULL"),
            ("name", "VARCHAR NOT NULL"),
            ("kind", "VARCHAR NOT NULL"),
            ("category", "VARCHAR"),
            ("symbol", "VARCHAR"),
            ("universe_id", "VARCHAR"),
            ("price_field", "VARCHAR"),
            ("adjust", "VARCHAR"),
            ("weight_method", "VARCHAR"),
            ("weight_field", "VARCHAR"),
            ("weight_lag", "INTEGER"),
            ("rebalance_freq", "VARCHAR"),
            ("rebalance_align", "VARCHAR"),
            ("base_date", "DATE"),
            ("base_value", "DOUBLE"),
            ("is_active", "BOOLEAN NOT NULL DEFAULT TRUE"),
            ("updated_at", "TIMESTAMPTZ NOT NULL DEFAULT current_timestamp"),
        ),
        constraints=("PRIMARY KEY (benchmark_id)",),
        description="基准定义（configs/baseline.yaml 的物化副本）",
    ),
    Table(
        name=c.BT_BASELINES,
        columns=(
            ("benchmark_id", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("close", "DOUBLE NOT NULL"),
            ("ret_1d", "DOUBLE"),
            ("nav", "DOUBLE NOT NULL"),
            ("base_date", "DATE"),
            ("base_value", "DOUBLE"),
            ("kind", "VARCHAR NOT NULL"),
            ("category", "VARCHAR"),
            ("source", "VARCHAR"),
            ("run_id", "VARCHAR NOT NULL"),
            ("created_at", "TIMESTAMPTZ NOT NULL DEFAULT current_timestamp"),
            ("updated_at", "TIMESTAMPTZ NOT NULL DEFAULT current_timestamp"),
        ),
        constraints=("PRIMARY KEY (benchmark_id, trade_date)",),
        description="基准日频点位；nav 在 base_date 归一为 1.0",
    ),
    Table(
        name=c.BT_BASELINE_WEIGHTS,
        columns=(
            ("benchmark_id", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("symbol", "VARCHAR NOT NULL"),
            ("weight", "DOUBLE NOT NULL"),
            ("target_weight", "DOUBLE"),
            ("price", "DOUBLE"),
            ("market_value", "DOUBLE"),
            ("is_rebalance_date", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("run_id", "VARCHAR NOT NULL"),
            ("created_at", "TIMESTAMPTZ NOT NULL DEFAULT current_timestamp"),
        ),
        constraints=("PRIMARY KEY (benchmark_id, trade_date, symbol)",),
        description="合成基准的每日实际权重与再平衡目标权重",
    ),
    Table(
        name=c.BT_RUNS,
        columns=(
            ("run_id", "VARCHAR NOT NULL"),
            ("strategy_id", "VARCHAR NOT NULL"),
            ("strategy_name", "VARCHAR"),
            ("benchmark_id", "VARCHAR"),
            ("params_json", "VARCHAR"),
            ("start_date", "DATE"),
            ("end_date", "DATE"),
            ("initial_capital", "DECIMAL(20,4) NOT NULL DEFAULT 1000000"),
            ("cost_model", "VARCHAR"),
            ("status", "VARCHAR NOT NULL DEFAULT 'pending'"),
            ("engine_version", "VARCHAR"),
            ("config_hash", "VARCHAR"),
            ("created_at", "TIMESTAMPTZ NOT NULL DEFAULT current_timestamp"),
            ("finished_at", "TIMESTAMPTZ"),
        ),
        constraints=("PRIMARY KEY (run_id)",),
        description="策略回测批次与配置快照",
    ),
    Table(
        name=c.BT_NAV,
        columns=(
            ("run_id", "VARCHAR NOT NULL"),
            ("trade_date", "DATE NOT NULL"),
            ("nav", "DOUBLE NOT NULL"),
            ("ret_1d", "DOUBLE"),
            ("cum_ret", "DOUBLE"),
            ("drawdown", "DOUBLE"),
            ("benchmark_id", "VARCHAR"),
            ("created_at", "TIMESTAMPTZ NOT NULL DEFAULT current_timestamp"),
        ),
        constraints=("PRIMARY KEY (run_id, trade_date)",),
        description="策略日频净值；nav 在首个交易日归一为 1.0",
    ),
    Table(
        name=c.BT_RUN_METRICS,
        columns=(
            ("run_id", "VARCHAR NOT NULL"),
            ("metric_name", "VARCHAR NOT NULL"),
            ("metric_value", "DOUBLE"),
            ("computed_at", "TIMESTAMPTZ NOT NULL DEFAULT current_timestamp"),
        ),
        constraints=("PRIMARY KEY (run_id, metric_name)",),
        description="回测绩效指标（年化、夏普、回撤、超额等）",
    ),
    Table(
        name=c.BT_COMPUTE_LOG,
        columns=(
            ("run_id", "VARCHAR NOT NULL"),
            ("job_name", "VARCHAR NOT NULL"),
            ("target_key", "VARCHAR NOT NULL"),
            ("status", "VARCHAR NOT NULL"),
            ("rows_written", "BIGINT NOT NULL DEFAULT 0"),
            ("start_date", "DATE"),
            ("end_date", "DATE"),
            ("error_message", "VARCHAR"),
            ("started_at", "TIMESTAMPTZ NOT NULL"),
            ("finished_at", "TIMESTAMPTZ"),
        ),
        constraints=("PRIMARY KEY (run_id)",),
        description="基准计算 / 回测批次日志（幂等覆盖同一 run_id）",
    ),
)

BACKTEST_VIEWS: Final[dict[str, str]] = {
    "v_bt_baselines": """
        SELECT
            b.benchmark_id,
            m.name,
            b.kind,
            b.category,
            b.trade_date,
            b.close,
            b.ret_1d,
            b.nav,
            b.run_id
        FROM bt_baselines b
        LEFT JOIN bt_benchmarks m USING (benchmark_id)
    """.strip(),
    "v_bt_nav_excess": """
        WITH joined AS (
            SELECT
                n.run_id,
                n.trade_date,
                n.nav,
                n.ret_1d,
                n.benchmark_id,
                b.nav AS benchmark_nav,
                b.ret_1d AS benchmark_ret_1d,
                first_value(b.nav IGNORE NULLS) OVER (
                    PARTITION BY n.run_id ORDER BY n.trade_date
                ) AS benchmark_start_nav
            FROM bt_nav n
            LEFT JOIN bt_baselines b
              ON b.benchmark_id = n.benchmark_id
             AND b.trade_date = n.trade_date
        )
        SELECT
            run_id,
            trade_date,
            benchmark_id,
            nav,
            ret_1d,
            benchmark_nav,
            benchmark_ret_1d,
            CASE
                WHEN benchmark_start_nav IS NULL OR benchmark_start_nav = 0 THEN NULL
                ELSE benchmark_nav / benchmark_start_nav
            END AS benchmark_nav_rel,
            CASE
                WHEN benchmark_start_nav IS NULL OR benchmark_start_nav = 0
                  OR benchmark_nav IS NULL THEN NULL
                ELSE nav / (benchmark_nav / benchmark_start_nav)
            END AS excess_nav,
            CASE
                WHEN benchmark_ret_1d IS NULL THEN NULL
                ELSE ret_1d - benchmark_ret_1d
            END AS excess_ret_1d
        FROM joined
    """.strip(),
}
