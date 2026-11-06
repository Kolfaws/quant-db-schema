# quant-db-schema

Quant 项目的 **schema 契约包**：只有常量与 DDL，没有数据库连接、没有业务逻辑、没有第三方依赖。

- 项目/文件夹：`quant-db-schema`
- Python 包名：`quant_schema`
- 安装后的 distribution：`quant-db-schema`

四个项目通过 editable 依赖共享同一份表结构定义：

```text
quant-data-pipeline      → market_ddl.py      建 market.duckdb（warehouse + factor）
quant-backtest-engine    → backtest_ddl.py    建 backtest.duckdb（backtest）
quant-baseline           → constants.py       只引用表名/主键，不建表
factor_research          → constants.py       只引用表名/主键，不建表
```

## 1. 目录

```text
quant-db-schema/
├── pyproject.toml
├── README.md
├── src/quant_schema/
│   ├── __init__.py
│   ├── _ddl.py           # Table 元数据 + DDL 渲染（无 IO）
│   ├── constants.py      # 组件/版本/表名/字段名/幂等键
│   ├── market_ddl.py     # market.duckdb: warehouse + factor
│   └── backtest_ddl.py   # backtest.duckdb: backtest
└── tests/test_ddl.py     # 契约自洽性测试（表名唯一、主键、幂等键）
```

> 文件夹叫 `quant-db-schema`，包名保持 `quant_schema`；`pyproject.toml` 用
> `[tool.uv.build-backend] module-name = "quant_schema"` 显式声明。
> 因此代码始终 `from quant_schema... import ...`。

## 2. 版本契约

| 数据库 | 组件 `meta_schema_version.component` | 当前版本 |
| --- | --- | --- |
| `market.duckdb` | `warehouse` | `1.2.0` |
| `market.duckdb` | `factor` | `1.0.0` |
| `backtest.duckdb` | `backtest` | `1.0.0` |

版本常量集中在 `constants.py`，各项目的 `init_*_db.py` 只引用常量，不重复写版本号。

## 3. 使用方式

各项目根目录执行（路径按实际项目位置调整）：

```bash
# quant-data-pipeline
uv add --editable ../quant-db-schema

# quant-baseline
uv add --editable ../quant-db-schema
uv add --editable ../quant-data-pipeline

# quant-backtest-engine
uv add --editable ../quant-db-schema
uv add --editable ../quant-data-pipeline
uv add --editable ../quant-baseline

# factor_research / quant-factor
uv add --editable ../quant-db-schema
uv add --editable ../quant-data-pipeline
```

代码里：

```python
from quant_schema.constants import BT_BASELINES, BT_BASELINES_KEYS
from quant_schema.backtest_ddl import BACKTEST_TABLES, BACKTEST_VIEWS
from quant_schema.market_ddl import WAREHOUSE_TABLES, FACTOR_TABLES

for table in BACKTEST_TABLES:
    con.execute(table.ddl())        # 只有 init 脚本才执行
```

## 4. 硬性约定

1. **不在业务代码里手写 `CREATE TABLE`**：建表只允许出现在各项目的 `init_*_db.py`，且 DDL 来自本包。
2. **表名/主键从 `constants.py` 引用**：`CONFLICT_KEYS` 是写入层 upsert 的唯一来源。
3. **改结构必须升版本**：修改 `*_ddl.py` 后同步 `constants` 版本、项目文档与迁移；旧库用 `verify_schema()` 会在结构漂移时失败。
4. **不把连接逻辑放进本包**：连接器统一放在 `data_pipeline.db`，本包保持零依赖。

## 5. 测试

```bash
uv run --with pytest pytest tests -q
```

或使用任意已安装 pytest 的环境：

```bash
python -m pytest tests -q
```
