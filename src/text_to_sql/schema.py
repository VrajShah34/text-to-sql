import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Column:
    name: str
    type: str
    description: Optional[str] = None


@dataclass
class Table:
    name: str
    columns: List[Column]
    description: Optional[str] = None
    primary_key: Optional[str] = None
    sample_values: Optional[Dict[str, List[str]]] = None

    def column_names(self) -> List[str]:
        return [col.name for col in self.columns]


@dataclass
class ForeignKey:
    source_table: str
    source_column: str
    target_table: str
    target_column: str


@dataclass
class DatabaseSchema:
    name: str
    path: Path
    tables: List[Table]
    foreign_keys: List[ForeignKey]

    def __post_init__(self) -> None:
        self._table_index = {table.name.lower(): table for table in self.tables}

    def find_table(self, table_name: str) -> Optional[Table]:
        return self._table_index.get(table_name.lower())

    def relation_strings(self) -> List[str]:
        return [
            f"{fk.source_table}.{fk.source_column} -> {fk.target_table}.{fk.target_column}"
            for fk in self.foreign_keys
        ]


def load_schema(schema_path: Path) -> List[DatabaseSchema]:
    with schema_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    dbs: List[DatabaseSchema] = []
    for db in payload["databases"]:
        tables = []
        for tbl in db["tables"]:
            columns = [
                Column(name=col["name"], type=col["type"], description=col.get("description"))
                for col in tbl["columns"]
            ]
            tables.append(
                Table(
                    name=tbl["name"],
                    description=tbl.get("description"),
                    columns=columns,
                    primary_key=tbl.get("primary_key"),
                    sample_values=tbl.get("sample_values"),
                )
            )
        fks = [
            ForeignKey(
                source_table=fk["source_table"],
                source_column=fk["source_column"],
                target_table=fk["target_table"],
                target_column=fk["target_column"],
            )
            for fk in db.get("foreign_keys", [])
        ]
        dbs.append(DatabaseSchema(name=db["name"], path=Path(db["path"]), tables=tables, foreign_keys=fks))
    return dbs

