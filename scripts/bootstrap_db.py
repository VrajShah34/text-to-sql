import argparse
import sqlite3
from pathlib import Path

EMPLOYEES = [
    (1, "Ava Thompson", 34, "Sales", "Sales Manager", 120000),
    (2, "Liam Carter", 29, "Engineering", "Backend Engineer", 135000),
    (3, "Sophia Nguyen", 41, "Sales", "Account Executive", 98000),
    (4, "Ethan Patel", 37, "Sales", "Sales Associate", 86000),
    (5, "Mia Rodriguez", 31, "HR", "HR Business Partner", 90000),
    (6, "Noah Brooks", 45, "Finance", "Senior Analyst", 110000),
    (7, "Olivia Green", 33, "Sales", "Sales Operations Lead", 102000),
]


def bootstrap(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                department TEXT NOT NULL,
                role TEXT NOT NULL,
                salary INTEGER NOT NULL
            )
            """
        )
        cur.execute("DELETE FROM employees")
        cur.executemany(
            "INSERT INTO employees (id, name, age, department, role, salary) VALUES (?, ?, ?, ?, ?, ?)",
            EMPLOYEES,
        )
        conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap demo SQLite database.")
    parser.add_argument(
        "--output",
        default="data/sample.db",
        type=Path,
        help="Path to SQLite database file to create.",
    )
    args = parser.parse_args()
    bootstrap(args.output)
    print(f"SQLite demo database ready at {args.output}")


if __name__ == "__main__":
    main()

