"""PostgreSQL contract for immutable, versioned backtest NAV snapshots."""

from quant_schema.postgres_ddl import PUBLICATION

POSTGRES_NAV_VERSION = "1.0.0"
NAV_COMPONENT = "backtest_nav"
BACKTEST_RUN = "backtest.nav_run"
BACKTEST_NAV = "backtest.nav_daily"

POSTGRES_BACKTEST_DDL = (
    "CREATE SCHEMA IF NOT EXISTS backtest",
    f"""CREATE TABLE {BACKTEST_RUN} (
        run_id text NOT NULL,
        revision integer NOT NULL CHECK (revision > 0),
        input_version bigint NOT NULL REFERENCES {PUBLICATION}(version_id),
        strategy_id text NOT NULL,
        strategy_name text,
        benchmark_id text,
        engine_version text,
        config_hash text,
        start_date date NOT NULL,
        end_date date NOT NULL CHECK (end_date >= start_date),
        rows integer NOT NULL CHECK (rows > 0),
        content_sha256 char(64) NOT NULL,
        published_at timestamptz NOT NULL DEFAULT current_timestamp,
        PRIMARY KEY (run_id, revision),
        UNIQUE (run_id, input_version, content_sha256)
    )""",
    f"""CREATE TABLE {BACKTEST_NAV} (
        run_id text NOT NULL,
        revision integer NOT NULL,
        trade_date date NOT NULL,
        nav double precision NOT NULL CHECK (nav > 0 AND nav < 'Infinity'::float8),
        ret_1d double precision NOT NULL CHECK (ret_1d > -1 AND ret_1d < 'Infinity'::float8),
        cum_ret double precision NOT NULL CHECK (cum_ret > -1 AND cum_ret < 'Infinity'::float8),
        drawdown double precision NOT NULL CHECK (drawdown > -1 AND drawdown <= 0),
        PRIMARY KEY (run_id, revision, trade_date),
        FOREIGN KEY (run_id, revision) REFERENCES {BACKTEST_RUN}(run_id, revision)
    )""",
)
