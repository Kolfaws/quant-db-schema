"""tests.test_ddl — schema 契约包的自洽性检查。"""

from __future__ import annotations

from quant_schema import constants as c
from quant_schema._ddl import Table, normalise_type
from quant_schema.backtest_ddl import BACKTEST_TABLES, BACKTEST_VIEWS
from quant_schema.market_ddl import (
    FACTOR_STATIC_VIEWS,
    FACTOR_TABLES,
    WAREHOUSE_MACROS,
    WAREHOUSE_TABLES,
    WAREHOUSE_VIEWS,
)


def _by_name(tables: tuple[Table, ...]) -> dict[str, Table]:
    return {table.name: table for table in tables}


def test_table_names_are_unique_per_database() -> None:
    market = [table.name for table in WAREHOUSE_TABLES + FACTOR_TABLES]
    backtest = [table.name for table in BACKTEST_TABLES]
    assert len(market) == len(set(market))
    assert len(backtest) == len(set(backtest))
    # 两个库各自拥有独立的 meta_schema_version
    assert c.META_SCHEMA_VERSION in market
    assert c.META_SCHEMA_VERSION in backtest


def test_every_table_has_primary_key() -> None:
    for table in WAREHOUSE_TABLES + FACTOR_TABLES + BACKTEST_TABLES:
        assert table.primary_key, f"{table.name} 没有主键"
        assert set(table.primary_key) <= set(table.column_names)


def test_ddl_contains_pk_and_types() -> None:
    table = _by_name(BACKTEST_TABLES)["bt_nav"]
    ddl = table.ddl()
    assert ddl.startswith('CREATE TABLE IF NOT EXISTS "bt_nav"')
    assert "PRIMARY KEY (run_id, trade_date)" in ddl
    assert table.expected_types["trade_date"] == "DATE"
    assert normalise_type("TIMESTAMPTZ") == "TIMESTAMP WITH TIME ZONE"


def test_conflict_keys_match_columns() -> None:
    all_tables = {
        table.name: table
        for table in WAREHOUSE_TABLES + FACTOR_TABLES + BACKTEST_TABLES
    }
    for name, keys in c.CONFLICT_KEYS.items():
        assert name in all_tables, f"{name} 不在任何 DDL 中"
        assert set(keys) <= set(all_tables[name].column_names)


def test_views_declared() -> None:
    assert set(WAREHOUSE_VIEWS) == set(c.MARKET_WAREHOUSE_VIEWS)
    assert set(WAREHOUSE_MACROS) == set(c.MARKET_WAREHOUSE_MACROS)
    assert set(BACKTEST_VIEWS) == set(c.BACKTEST_VIEWS)


def test_v_factor_valid_filters_stale() -> None:
    sql = FACTOR_STATIC_VIEWS["v_factor_valid"].lower()
    assert "is_stale = false" in sql


def test_qfq_macro_is_point_in_time() -> None:
    sql = WAREHOUSE_MACROS["qfq_daily"].lower()
    assert "qfq_daily(as_of date)" in sql
    assert "trade_date <= as_of" in sql


def test_component_versions_are_semver() -> None:
    for version in (
        c.WAREHOUSE_SCHEMA_VERSION,
        c.FACTOR_SCHEMA_VERSION,
        c.BACKTEST_SCHEMA_VERSION,
    ):
        parts = version.split(".")
        assert len(parts) == 3 and all(part.isdigit() for part in parts)
