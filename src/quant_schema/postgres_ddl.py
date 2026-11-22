"""PostgreSQL contracts for published A-share daily data and approved factors."""

from dataclasses import dataclass

POSTGRES_VERSION = "1.0.0"
PUBLICATION = "control.publication"
INSTRUMENT = "reference.instrument"
FACTOR_DEFINITION = "features.factor_definition"
FACTOR_VALUE = "features.factor_value_daily"


@dataclass(frozen=True)
class Dataset:
    table: str
    columns: tuple[tuple[str, str], ...]
    key: tuple[str, ...]

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self.columns)


CALENDAR = Dataset(
    "reference.trade_calendar",
    (
        ("exchange", "text NOT NULL"),
        ("cal_date", "date NOT NULL"),
        ("is_open", "boolean NOT NULL"),
        ("pretrade_date", "date"),
    ),
    ("exchange", "cal_date"),
)
STOCK = Dataset(
    "reference.stock_snapshot",
    (
        ("ts_code", "text NOT NULL"),
        ("symbol", "text"),
        ("name", "text"),
        ("area", "text"),
        ("industry", "text"),
        ("market", "text"),
        ("exchange", "text NOT NULL"),
        ("list_status", "text NOT NULL"),
        ("list_date", "date"),
        ("delist_date", "date"),
        ("is_hs", "text"),
    ),
    ("ts_code",),
)
DAILY = Dataset(
    "market.stock_daily",
    (
        ("ts_code", "text NOT NULL"),
        ("trade_date", "date NOT NULL"),
        *(
            (name, "double precision NOT NULL")
            for name in ("open", "high", "low", "close")
        ),
        *((name, "double precision") for name in ("pre_close", "chg", "pct_chg")),
        ("vol", "double precision NOT NULL"),
        ("amount", "numeric(20,4) NOT NULL"),
    ),
    ("ts_code", "trade_date"),
)
ADJUSTMENT = Dataset(
    "market.stock_adjustment",
    (
        ("ts_code", "text NOT NULL"),
        ("trade_date", "date NOT NULL"),
        ("adj_factor", "double precision NOT NULL"),
    ),
    ("ts_code", "trade_date"),
)
DATASETS = (STOCK, CALENDAR, DAILY, ADJUSTMENT)


def _table(dataset: Dataset, *constraints: str) -> str:
    parts = [f"{name} {kind}" for name, kind in dataset.columns]
    parts.append(f"version_id bigint NOT NULL REFERENCES {PUBLICATION}(version_id)")
    parts.extend(constraints)
    return f"CREATE TABLE IF NOT EXISTS {dataset.table} ({', '.join(parts)})"


POSTGRES_DDL = (
    *(
        f"CREATE SCHEMA IF NOT EXISTS {schema}"
        for schema in ("control", "reference", "market", "features")
    ),
    """CREATE TABLE IF NOT EXISTS control.schema_version (
        component text PRIMARY KEY, version text NOT NULL
    )""",
    f"""CREATE TABLE IF NOT EXISTS {PUBLICATION} (
        version_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        source text NOT NULL,
        observed_at timestamptz NOT NULL,
        start_date date NOT NULL,
        end_date date NOT NULL CHECK (end_date >= start_date),
        content_sha256 char(64) NOT NULL,
        counts jsonb NOT NULL
    )""",
    f"""CREATE TABLE IF NOT EXISTS {INSTRUMENT} (
        instrument_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        ts_code text NOT NULL UNIQUE
    )""",
    _table(
        STOCK,
        "PRIMARY KEY (ts_code, version_id)",
        f"FOREIGN KEY (ts_code) REFERENCES {INSTRUMENT}(ts_code)",
        "CHECK (list_status IN ('L', 'D', 'P'))",
        "CHECK (list_status <> 'D' OR delist_date IS NOT NULL)",
        "CHECK (list_date IS NULL OR delist_date IS NULL OR list_date <= delist_date)",
    ),
    _table(
        CALENDAR,
        "PRIMARY KEY (exchange, cal_date)",
        "CHECK (pretrade_date IS NULL OR pretrade_date < cal_date)",
    ),
    _table(
        DAILY,
        "PRIMARY KEY (ts_code, trade_date)",
        f"FOREIGN KEY (ts_code) REFERENCES {INSTRUMENT}(ts_code)",
        "CHECK (low > 0 AND low <= least(open, close) AND high >= greatest(open, close))",
        "CHECK (vol >= 0 AND amount >= 0)",
    ),
    _table(
        ADJUSTMENT,
        "PRIMARY KEY (ts_code, trade_date)",
        f"FOREIGN KEY (ts_code, trade_date) REFERENCES {DAILY.table}(ts_code, trade_date)",
        "CHECK (adj_factor > 0)",
    ),
    f"CREATE INDEX IF NOT EXISTS stock_daily_trade_date ON {DAILY.table} (trade_date, ts_code)",
    f"CREATE INDEX IF NOT EXISTS stock_adjustment_trade_date ON {ADJUSTMENT.table} (trade_date, ts_code)",
    f"""CREATE TABLE IF NOT EXISTS {FACTOR_DEFINITION} (
        factor_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        factor_key text NOT NULL,
        factor_version text NOT NULL,
        input_version bigint NOT NULL REFERENCES {PUBLICATION}(version_id),
        definition jsonb NOT NULL,
        approved_at timestamptz NOT NULL,
        UNIQUE (factor_key, factor_version)
    )""",
    f"""CREATE TABLE IF NOT EXISTS {FACTOR_VALUE} (
        factor_id bigint NOT NULL REFERENCES {FACTOR_DEFINITION}(factor_id),
        instrument_id bigint NOT NULL REFERENCES {INSTRUMENT}(instrument_id),
        trade_date date NOT NULL,
        factor_value double precision NOT NULL,
        available_at timestamptz NOT NULL,
        version_id bigint NOT NULL REFERENCES {PUBLICATION}(version_id),
        PRIMARY KEY (factor_id, trade_date, instrument_id),
        CHECK (factor_value NOT IN ('NaN'::float8, 'Infinity'::float8, '-Infinity'::float8))
    )""",
)
