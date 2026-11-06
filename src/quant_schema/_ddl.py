"""_ddl — 极小的 DDL 元数据构造器。

本模块刻意只做三件事：

1. 描述一张表（列、约束、注释）；
2. 渲染 ``CREATE TABLE IF NOT EXISTS`` 语句；
3. 给出校验函数需要的期望列类型。

它**不**连接数据库、不执行 SQL、不含任何业务逻辑。
建表事务、结构校验、版本写入由各项目自己的 ``init_*_db.py`` 负责。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# DuckDB 的 duckdb_columns() 会把 TIMESTAMPTZ 归一成
# "TIMESTAMP WITH TIME ZONE"，校验前必须做同样的别名映射。
_TYPE_ALIASES: dict[str, str] = {"TIMESTAMPTZ": "TIMESTAMP WITH TIME ZONE"}

_PRIMARY_KEY_RE = re.compile(r"^PRIMARY\s+KEY\s*\(([^)]*)\)$", re.IGNORECASE)


def normalise_type(raw: str) -> str:
    """把 SQL 类型声明归一成 duckdb_columns() 的展示形式。"""
    upper = raw.strip().upper()
    return _TYPE_ALIASES.get(upper, upper)


@dataclass(frozen=True, slots=True)
class Table:
    """一张表的完整结构契约。

    Attributes:
        name: 表名（小写 snake_case）。
        columns: ``(列名, SQL 类型声明)`` 有序元组；顺序即建表顺序。
        constraints: 追加在列定义后的约束，如 ``PRIMARY KEY (a, b)``。
        description: 供文档与 CLI 展示的一句话说明。
    """

    name: str
    columns: tuple[tuple[str, str], ...]
    constraints: tuple[str, ...] = ()
    description: str = ""

    def ddl(self) -> str:
        """渲染 ``CREATE TABLE IF NOT EXISTS`` 语句。"""
        body = ",\n        ".join(f'"{column}" {decl}' for column, decl in self.columns)
        tail = "".join(f",\n        {constraint}" for constraint in self.constraints)
        return (
            f'CREATE TABLE IF NOT EXISTS "{self.name}" (\n        {body}{tail}\n    )'
        )

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(column for column, _ in self.columns)

    @property
    def expected_types(self) -> dict[str, str]:
        """校验用的 ``{列名: 归一化类型}``。"""
        return {
            column: normalise_type(decl.split(" ", 1)[0])
            for column, decl in self.columns
        }

    @property
    def primary_key(self) -> tuple[str, ...] | None:
        """从 constraints 中解析主键列；没有主键返回 ``None``。"""
        for constraint in self.constraints:
            match = _PRIMARY_KEY_RE.match(constraint.strip())
            if match is None:
                continue
            columns = tuple(
                part.strip().strip('"')
                for part in match.group(1).split(",")
                if part.strip()
            )
            if columns:
                return columns
        return None
