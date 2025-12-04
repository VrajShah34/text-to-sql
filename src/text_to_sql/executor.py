from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Sequence

import pandas as pd
from tabulate import tabulate


@dataclass
class ExecutionResult:
    columns: Sequence[str]
    rows: List[Sequence[Any]]

    def as_table(self) -> str:
        return tabulate(self.rows, headers=self.columns, tablefmt="github")


class SQLiteExecutor:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def execute(self, sql: str) -> ExecutionResult:
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(sql, conn)
        return ExecutionResult(columns=df.columns.tolist(), rows=df.values.tolist())

