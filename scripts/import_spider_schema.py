import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple


def _columns_by_table(entry: Dict) -> Dict[int, List[Tuple[str, str]]]:
    mapping: Dict[int, List[Tuple[str, str]]] = {}
    column_names = entry["column_names_original"]
    column_types = entry["column_types"]
    for idx, (table_id, column_name) in enumerate(column_names):
        if table_id == -1 or column_name == "*":
            continue
        mapping.setdefault(table_id, []).append((column_name, column_types[idx]))
    return mapping


def convert_spider(tables_json: Path, database_dir: Path, output: Path) -> None:
    with tables_json.open("r", encoding="utf-8") as handle:
        entries = json.load(handle)

    result = {"databases": []}
    for entry in entries:
        table_names: List[str] = entry["table_names_original"]
        columns_map = _columns_by_table(entry)
        pk_indexes = set(entry.get("primary_keys", []))
        column_names = entry["column_names_original"]

        tables = []
        for table_idx, table_name in enumerate(table_names):
            cols = []
            for column_name, column_type in columns_map.get(table_idx, []):
                cols.append(
                    {
                        "name": column_name,
                        "type": column_type.upper(),
                    }
                )
            pk_name = None
            for pk_idx in pk_indexes:
                pk_table, pk_column = column_names[pk_idx]
                if pk_table == table_idx:
                    pk_name = pk_column
                    break
            tables.append(
                {
                    "name": table_name,
                    "columns": cols,
                    "primary_key": pk_name,
                }
            )

        foreign_keys = []
        for source_idx, target_idx in entry.get("foreign_keys", []):
            source_table_id, source_column = column_names[source_idx]
            target_table_id, target_column = column_names[target_idx]
            if source_table_id == -1 or target_table_id == -1:
                continue
            foreign_keys.append(
                {
                    "source_table": table_names[source_table_id],
                    "source_column": source_column,
                    "target_table": table_names[target_table_id],
                    "target_column": target_column,
                }
            )

        sqlite_path = database_dir / entry["db_id"] / f"{entry['db_id']}.sqlite"
        result["databases"].append(
            {
                "name": entry["db_id"],
                "path": str(sqlite_path),
                "tables": tables,
                "foreign_keys": foreign_keys,
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(f"Spider schema exported to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Spider tables.json to pipeline schema format.")
    parser.add_argument("--tables-json", required=True, type=Path, help="Path to Spider tables.json file.")
    parser.add_argument("--database-dir", required=True, type=Path, help="Path to Spider database directory.")
    parser.add_argument(
        "--output",
        default=Path("data/spider_schema.json"),
        type=Path,
        help="Destination schema JSON path.",
    )
    args = parser.parse_args()
    convert_spider(args.tables_json, args.database_dir, args.output)


if __name__ == "__main__":
    main()

