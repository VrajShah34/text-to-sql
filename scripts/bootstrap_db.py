import argparse
import sqlite3
from pathlib import Path
from typing import Callable, Dict

DATA_DIR = Path("data")


def ensure_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def bootstrap_company(db_path: Path) -> None:
    departments = [
        (1, "Sales", "Enterprise"),
        (2, "Engineering", "Product"),
        (3, "HR", "Corporate"),
        (4, "Finance", "Corporate"),
    ]
    projects = [
        (1, "Atlas CRM", 1, 300000),
        (2, "Nova Backend", 2, 520000),
        (3, "People Analytics", 3, 180000),
        (4, "Margin Guard", 4, 210000),
    ]
    employees = [
        (1, "Ava Thompson", 34, "Sales", 1, "Sales Manager", 120000),
        (2, "Liam Carter", 29, "Engineering", 2, "Backend Engineer", 135000),
        (3, "Sophia Nguyen", 41, "Sales", 1, "Account Executive", 98000),
        (4, "Ethan Patel", 37, "Sales", 1, "Sales Associate", 86000),
        (5, "Mia Rodriguez", 31, "HR", 3, "HR Business Partner", 90000),
        (6, "Noah Brooks", 45, "Finance", 4, "Senior Analyst", 110000),
        (7, "Olivia Green", 33, "Sales", 1, "Sales Operations Lead", 102000),
    ]
    employee_projects = [
        (1, 1),
        (1, 3),
        (2, 2),
        (2, 7),
        (3, 5),
        (3, 1),
        (4, 6),
        (4, 4),
    ]
    sales = [
        (1, 1, "Acme Retail", 450000, "2024-Q1"),
        (2, 3, "OmniShop", 380000, "2024-Q2"),
        (3, 4, "Northwind", 215000, "2024-Q2"),
        (4, 7, "Globex", 510000, "2024-Q3"),
        (5, 1, "Globex", 125000, "2024-Q4"),
    ]

    with ensure_db(db_path) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            DROP TABLE IF EXISTS sales;
            DROP TABLE IF EXISTS employee_projects;
            DROP TABLE IF EXISTS employees;
            DROP TABLE IF EXISTS projects;
            DROP TABLE IF EXISTS departments;
            CREATE TABLE departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                division TEXT NOT NULL
            );
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department_id INTEGER NOT NULL,
                budget INTEGER NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            );
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                department TEXT NOT NULL,
                department_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                salary INTEGER NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            );
            CREATE TABLE employee_projects (
                project_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                PRIMARY KEY (project_id, employee_id),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );
            CREATE TABLE sales (
                id INTEGER PRIMARY KEY,
                employee_id INTEGER NOT NULL,
                client TEXT NOT NULL,
                amount INTEGER NOT NULL,
                quarter TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );
            """
        )
        cur.executemany(
            "INSERT INTO departments (id, name, division) VALUES (?, ?, ?)", departments
        )
        cur.executemany(
            "INSERT INTO projects (id, name, department_id, budget) VALUES (?, ?, ?, ?)",
            projects,
        )
        cur.executemany(
            """
            INSERT INTO employees (id, name, age, department, department_id, role, salary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            employees,
        )
        cur.executemany(
            "INSERT INTO employee_projects (project_id, employee_id) VALUES (?, ?)",
            employee_projects,
        )
        cur.executemany(
            "INSERT INTO sales (id, employee_id, client, amount, quarter) VALUES (?, ?, ?, ?, ?)",
            sales,
        )
        conn.commit()


def bootstrap_university(db_path: Path) -> None:
    students = [
        (1, "Alice Kim", "Computer Science", "Junior"),
        (2, "Brandon Lee", "Mathematics", "Senior"),
        (3, "Cora Patel", "Economics", "Sophomore"),
        (4, "Diego Torres", "History", "Senior"),
    ]
    courses = [
        (1, "Database Systems", "CS", 3),
        (2, "Linear Algebra", "MATH", 4),
        (3, "Microeconomics", "ECON", 3),
        (4, "Modern Europe", "HIST", 3),
    ]
    enrollments = [
        (1, 1, "A"),
        (1, 2, "B+"),
        (2, 2, "A-"),
        (2, 3, "B"),
        (3, 3, "A"),
        (3, 1, "B"),
        (4, 4, "A-"),
        (4, 2, "B"),
    ]

    with ensure_db(db_path) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            DROP TABLE IF EXISTS enrollments;
            DROP TABLE IF EXISTS students;
            DROP TABLE IF EXISTS courses;
            CREATE TABLE students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                major TEXT NOT NULL,
                year TEXT NOT NULL
            );
            CREATE TABLE courses (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                department TEXT NOT NULL,
                credits INTEGER NOT NULL
            );
            CREATE TABLE enrollments (
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                grade TEXT NOT NULL,
                PRIMARY KEY (student_id, course_id),
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (course_id) REFERENCES courses(id)
            );
            """
        )
        cur.executemany(
            "INSERT INTO students (id, name, major, year) VALUES (?, ?, ?, ?)", students
        )
        cur.executemany(
            "INSERT INTO courses (id, title, department, credits) VALUES (?, ?, ?, ?)",
            courses,
        )
        cur.executemany(
            "INSERT INTO enrollments (student_id, course_id, grade) VALUES (?, ?, ?)",
            enrollments,
        )
        conn.commit()


def bootstrap_retail(db_path: Path) -> None:
    products = [
        (1, "Aurora Laptop", "Electronics", 1299),
        (2, "Nimbus Headphones", "Accessories", 199),
        (3, "Summit Backpack", "Outdoors", 149),
        (4, "Glide Running Shoes", "Footwear", 179),
    ]
    orders = [
        (1, "Harper Steel", "2024-09-12", "Shipped"),
        (2, "Milo Reeves", "2024-10-05", "Processing"),
        (3, "Zara Lane", "2024-10-18", "Delivered"),
    ]
    order_items = [
        (1, 1, 1, 1299),
        (1, 2, 2, 199),
        (2, 3, 1, 149),
        (2, 4, 1, 179),
        (3, 2, 1, 199),
        (3, 4, 2, 179),
    ]

    with ensure_db(db_path) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            DROP TABLE IF EXISTS order_items;
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS products;
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL
            );
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                customer TEXT NOT NULL,
                order_date TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE order_items (
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            """
        )
        cur.executemany(
            "INSERT INTO products (id, name, category, price) VALUES (?, ?, ?, ?)",
            products,
        )
        cur.executemany(
            "INSERT INTO orders (id, customer, order_date, status) VALUES (?, ?, ?, ?)",
            orders,
        )
        cur.executemany(
            """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (?, ?, ?, ?)
            """,
            order_items,
        )
        conn.commit()


DATASETS: Dict[str, Callable[[Path], None]] = {
    "company": lambda path=DATA_DIR / "company.db": bootstrap_company(path),
    "university": lambda path=DATA_DIR / "university.db": bootstrap_university(path),
    "retail": lambda path=DATA_DIR / "retail.db": bootstrap_retail(path),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo SQLite databases.")
    parser.add_argument(
        "--dataset",
        choices=["company", "university", "retail", "all"],
        default="all",
        help="Which dataset(s) to create.",
    )
    args = parser.parse_args()
    targets = DATASETS.keys() if args.dataset == "all" else [args.dataset]

    for dataset in targets:
        DATASETS[dataset]()
        print(f"SQLite demo database ready: {dataset}")


if __name__ == "__main__":
    main()

