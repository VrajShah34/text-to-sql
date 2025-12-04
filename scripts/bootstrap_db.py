import argparse
import sqlite3
from pathlib import Path

DEPARTMENTS = [
    (1, "Sales", "Enterprise"),
    (2, "Engineering", "Product"),
    (3, "HR", "Corporate"),
    (4, "Finance", "Corporate"),
]

EMPLOYEES = [
    (1, "Ava Thompson", 34, "Sales", 1, "Sales Manager", 120000),
    (2, "Liam Carter", 29, "Engineering", 2, "Backend Engineer", 135000),
    (3, "Sophia Nguyen", 41, "Sales", 1, "Account Executive", 98000),
    (4, "Ethan Patel", 37, "Sales", 1, "Sales Associate", 86000),
    (5, "Mia Rodriguez", 31, "HR", 3, "HR Business Partner", 90000),
    (6, "Noah Brooks", 45, "Finance", 4, "Senior Analyst", 110000),
    (7, "Olivia Green", 33, "Sales", 1, "Sales Operations Lead", 102000),
]


def bootstrap(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS employees")
        cur.execute("DROP TABLE IF EXISTS departments")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                division TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                department TEXT NOT NULL,
                department_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                salary INTEGER NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
            """
        )
        cur.executemany(
            "INSERT INTO departments (id, name, division) VALUES (?, ?, ?)",
            DEPARTMENTS,
        )
        cur.executemany(
            """
            INSERT INTO employees (id, name, age, department, department_id, role, salary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
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

