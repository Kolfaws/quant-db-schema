"""quant_schema — Quant 项目的 schema 契约包。

只包含：

* ``constants``：组件名、版本号、表名、字段名、幂等键；
* ``market_ddl``：``market.duckdb``（warehouse + factor）的 DDL；
* ``backtest_ddl``：``backtest.duckdb``（backtest）的 DDL。

不包含数据库连接、不执行 SQL、不依赖任何第三方库。
"""

from .constants import (
    BACKTEST_COMPONENT,
    BACKTEST_SCHEMA_VERSION,
    FACTOR_COMPONENT,
    FACTOR_SCHEMA_VERSION,
    WAREHOUSE_COMPONENT,
    WAREHOUSE_SCHEMA_VERSION,
)

__all__ = [
    "BACKTEST_COMPONENT",
    "BACKTEST_SCHEMA_VERSION",
    "FACTOR_COMPONENT",
    "FACTOR_SCHEMA_VERSION",
    "WAREHOUSE_COMPONENT",
    "WAREHOUSE_SCHEMA_VERSION",
]
