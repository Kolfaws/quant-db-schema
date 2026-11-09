"""constants — 跨项目共享的 schema 常量。

所有项目（data_pipeline / quant-baseline / quant-backtest-engine / factor_research）
只允许从这里引用表名、组件名、版本号与幂等键，禁止在业务代码里硬编码字符串。

版本号约定（与 ``meta_schema_version.version`` 一致）：

============  =========================  ==================================
数据库          组件 (component)            当前版本
============  =========================  ==================================
market.duckdb   ``warehouse``              ``1.2.0``
market.duckdb   ``factor``                 ``1.1.0``
backtest.duckdb ``backtest``               ``1.0.0``
============  =========================  ==================================
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# 组件与版本
# ---------------------------------------------------------------------------
WAREHOUSE_COMPONENT: Final[str] = "warehouse"
FACTOR_COMPONENT: Final[str] = "factor"
BACKTEST_COMPONENT: Final[str] = "backtest"

WAREHOUSE_SCHEMA_VERSION: Final[str] = "1.2.0"
FACTOR_SCHEMA_VERSION: Final[str] = "1.1.0"
BACKTEST_SCHEMA_VERSION: Final[str] = "1.0.0"

# 运行环境：正式库 / 测试库
QUANT_ENVS: Final[tuple[str, ...]] = ("prod", "test")
FACTOR_ENVS: Final[tuple[str, ...]] = ("prod", "test")

# 因子域：量价、基本面、资金流、宏观
FACTOR_DOMAIN_PRICE_VOLUME: Final[str] = "price_volume"
FACTOR_DOMAIN_FUNDAMENTAL: Final[str] = "fundamental"
FACTOR_DOMAIN_CAPITAL_FLOW: Final[str] = "capital_flow"
FACTOR_DOMAIN_MACRO: Final[str] = "macro"
FACTOR_DOMAINS: Final[tuple[str, ...]] = (
    FACTOR_DOMAIN_PRICE_VOLUME,
    FACTOR_DOMAIN_FUNDAMENTAL,
    FACTOR_DOMAIN_CAPITAL_FLOW,
    FACTOR_DOMAIN_MACRO,
)

# 因子频率
FACTOR_FREQUENCIES: Final[tuple[str, ...]] = (
    "daily",
    "weekly",
    "monthly",
    "quarterly",
    "event",
)

# 上线前验证状态
FACTOR_VALIDATION_STATUSES: Final[tuple[str, ...]] = (
    "pending",
    "approved",
    "rejected",
)

# ---------------------------------------------------------------------------
# 公共表 / 字段
# ---------------------------------------------------------------------------
META_SCHEMA_VERSION: Final[str] = "meta_schema_version"
META_INGEST_LOG: Final[str] = "meta_ingest_log"

COMPONENT: Final[str] = "component"
VERSION: Final[str] = "version"
APPLIED_AT: Final[str] = "applied_at"

TRADE_DATE: Final[str] = "trade_date"
TS_CODE: Final[str] = "ts_code"
BENCHMARK_ID: Final[str] = "benchmark_id"
UNIVERSE_ID: Final[str] = "universe_id"
RUN_ID: Final[str] = "run_id"
SYMBOL: Final[str] = "symbol"
WEIGHT: Final[str] = "weight"

# ---------------------------------------------------------------------------
# market.duckdb — warehouse 组件（基础行情）
# ---------------------------------------------------------------------------
DIM_STOCK_BASIC: Final[str] = "dim_stock_basic"
DIM_TRADE_CAL: Final[str] = "dim_trade_cal"
FACT_DAILY: Final[str] = "fact_daily"
FACT_ADJ_FACTOR: Final[str] = "fact_adj_factor"
FACT_DAILY_BASIC: Final[str] = "fact_daily_basic"
FACT_STK_LIMIT: Final[str] = "fact_stk_limit"
FACT_INDEX_DAILY: Final[str] = "fact_index_daily"
FACT_INDEX_WEIGHT: Final[str] = "fact_index_weight"
FACT_FUND_DAILY: Final[str] = "fact_fund_daily"

MARKET_WAREHOUSE_TABLES: Final[tuple[str, ...]] = (
    META_SCHEMA_VERSION,
    META_INGEST_LOG,
    DIM_STOCK_BASIC,
    DIM_TRADE_CAL,
    FACT_DAILY,
    FACT_ADJ_FACTOR,
    FACT_DAILY_BASIC,
    FACT_STK_LIMIT,
    FACT_INDEX_DAILY,
    FACT_INDEX_WEIGHT,
    FACT_FUND_DAILY,
)

MARKET_WAREHOUSE_VIEWS: Final[tuple[str, ...]] = (
    "v_daily_qfq",
    "v_daily_hfq",
)

# ---------------------------------------------------------------------------
# market.duckdb — factor 组件（因子层）
# ---------------------------------------------------------------------------
META_FACTOR_REGISTRY: Final[str] = "meta_factor_registry"
FACT_FACTOR_DAILY: Final[str] = "fact_factor_daily"
FACT_TRADABLE_FLAG: Final[str] = "fact_tradable_flag"
FACT_FACTOR_QUALITY: Final[str] = "fact_factor_quality"
META_FACTOR_PROFILE: Final[str] = "meta_factor_profile"
META_FACTOR_VALIDATION: Final[str] = "meta_factor_validation"
META_FACTOR_PROMOTION_LOG: Final[str] = "meta_factor_promotion_log"

MARKET_FACTOR_TABLES: Final[tuple[str, ...]] = (
    META_FACTOR_REGISTRY,
    FACT_FACTOR_DAILY,
    FACT_TRADABLE_FLAG,
    FACT_FACTOR_QUALITY,
    META_FACTOR_PROFILE,
    META_FACTOR_VALIDATION,
    META_FACTOR_PROMOTION_LOG,
)

MARKET_FACTOR_VIEWS: Final[tuple[str, ...]] = (
    "v_factor_wide",
    "v_factor_valid",
)

# ---------------------------------------------------------------------------
# backtest.duckdb — backtest 组件（回测评估）
# ---------------------------------------------------------------------------
BT_BENCHMARKS: Final[str] = "bt_benchmarks"
BT_BASELINES: Final[str] = "bt_baselines"
BT_BASELINE_WEIGHTS: Final[str] = "bt_baseline_weights"
BT_RUNS: Final[str] = "bt_runs"
BT_NAV: Final[str] = "bt_nav"
BT_RUN_METRICS: Final[str] = "bt_run_metrics"
BT_COMPUTE_LOG: Final[str] = "bt_compute_log"

BACKTEST_TABLES: Final[tuple[str, ...]] = (
    META_SCHEMA_VERSION,
    BT_BENCHMARKS,
    BT_BASELINES,
    BT_BASELINE_WEIGHTS,
    BT_RUNS,
    BT_NAV,
    BT_RUN_METRICS,
    BT_COMPUTE_LOG,
)

BACKTEST_VIEWS: Final[tuple[str, ...]] = (
    "v_bt_baselines",
    "v_bt_nav_excess",
)

# ---------------------------------------------------------------------------
# 幂等键（ON CONFLICT 的冲突列）
# ---------------------------------------------------------------------------
BT_BENCHMARKS_KEYS: Final[tuple[str, ...]] = (BENCHMARK_ID,)
BT_BASELINES_KEYS: Final[tuple[str, ...]] = (BENCHMARK_ID, TRADE_DATE)
BT_BASELINE_WEIGHTS_KEYS: Final[tuple[str, ...]] = (
    BENCHMARK_ID,
    TRADE_DATE,
    SYMBOL,
)
BT_RUNS_KEYS: Final[tuple[str, ...]] = (RUN_ID,)
BT_NAV_KEYS: Final[tuple[str, ...]] = (RUN_ID, TRADE_DATE)
BT_RUN_METRICS_KEYS: Final[tuple[str, ...]] = (RUN_ID, "metric_name")
BT_COMPUTE_LOG_KEYS: Final[tuple[str, ...]] = (RUN_ID,)
META_SCHEMA_VERSION_KEYS: Final[tuple[str, ...]] = (COMPONENT,)
META_INGEST_LOG_KEYS: Final[tuple[str, ...]] = ("table_name", "scope_key")
META_FACTOR_PROFILE_KEYS: Final[tuple[str, ...]] = ("factor_id",)
META_FACTOR_VALIDATION_KEYS: Final[tuple[str, ...]] = (
    "factor_id",
    "env",
    "validated_at",
)
META_FACTOR_PROMOTION_KEYS: Final[tuple[str, ...]] = ("promotion_id",)

#: 表名 -> 幂等键。写入层可直接查表，避免每个调用点重复声明。
CONFLICT_KEYS: Final[dict[str, tuple[str, ...]]] = {
    META_SCHEMA_VERSION: META_SCHEMA_VERSION_KEYS,
    META_INGEST_LOG: META_INGEST_LOG_KEYS,
    META_FACTOR_PROFILE: META_FACTOR_PROFILE_KEYS,
    META_FACTOR_VALIDATION: META_FACTOR_VALIDATION_KEYS,
    META_FACTOR_PROMOTION_LOG: META_FACTOR_PROMOTION_KEYS,
    BT_BENCHMARKS: BT_BENCHMARKS_KEYS,
    BT_BASELINES: BT_BASELINES_KEYS,
    BT_BASELINE_WEIGHTS: BT_BASELINE_WEIGHTS_KEYS,
    BT_RUNS: BT_RUNS_KEYS,
    BT_NAV: BT_NAV_KEYS,
    BT_RUN_METRICS: BT_RUN_METRICS_KEYS,
    BT_COMPUTE_LOG: BT_COMPUTE_LOG_KEYS,
}

#: 写库前禁止交给 ``INSERT BY NAME`` 的额外列（写入层会剔除）。
BACKTEST_TABLE_COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    BT_BENCHMARKS: (
        BENCHMARK_ID,
        "name",
        "kind",
        "category",
        "symbol",
        "universe_id",
        "price_field",
        "adjust",
        "weight_method",
        "weight_field",
        "weight_lag",
        "rebalance_freq",
        "rebalance_align",
        "base_date",
        "base_value",
        "is_active",
        "updated_at",
    ),
    BT_BASELINES: (
        BENCHMARK_ID,
        TRADE_DATE,
        "close",
        "ret_1d",
        "nav",
        "base_date",
        "base_value",
        "kind",
        "category",
        "source",
        RUN_ID,
        "created_at",
        "updated_at",
    ),
    BT_BASELINE_WEIGHTS: (
        BENCHMARK_ID,
        TRADE_DATE,
        SYMBOL,
        WEIGHT,
        "target_weight",
        "price",
        "market_value",
        "is_rebalance_date",
        RUN_ID,
        "created_at",
    ),
    BT_RUNS: (
        RUN_ID,
        "strategy_id",
        "strategy_name",
        BENCHMARK_ID,
        "params_json",
        "start_date",
        "end_date",
        "initial_capital",
        "cost_model",
        "status",
        "engine_version",
        "config_hash",
        "created_at",
        "finished_at",
    ),
    BT_NAV: (
        RUN_ID,
        TRADE_DATE,
        "nav",
        "ret_1d",
        "cum_ret",
        "drawdown",
        BENCHMARK_ID,
        "created_at",
    ),
    BT_RUN_METRICS: (RUN_ID, "metric_name", "metric_value", "computed_at"),
    BT_COMPUTE_LOG: (
        RUN_ID,
        "job_name",
        "target_key",
        "status",
        "rows_written",
        "start_date",
        "end_date",
        "error_message",
        "started_at",
        "finished_at",
    ),
}
