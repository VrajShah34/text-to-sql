from __future__ import annotations

import re
from typing import Optional

import sqlparse

from .schema import DatabaseSchema

SQL_KEYWORDS = {"select", "from", "where", "group", "order", "limit", "having", "join"}


def sanitize_sql(sql: str) -> str:
    cleaned = sql.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned.lower().startswith("select"):
        return cleaned
    return cleaned


def validate_sql(sql: str, schema: DatabaseSchema) -> Optional[str]:
    parsed = sqlparse.parse(sql)
    if not parsed:
        return "Failed to parse SQL."
    statement = parsed[0]
    tokens = [token.value.lower() for token in statement.tokens if token.ttype is None]
    if not any("from" in token for token in tokens):
        return "Missing FROM clause."
    tables = {tbl.name.lower() for tbl in schema.tables}
    if not any(tbl in sql.lower() for tbl in tables):
        return "No known table referenced."
    lowered = sql.lower()
    dangerous = ["drop ", "delete ", "update ", "insert "]
    if any(keyword in lowered for keyword in dangerous):
        return "Only SELECT statements are allowed."
    return None


def pretty_format(sql: str) -> str:
    return sqlparse.format(sql, reindent=True, keyword_case="upper")

