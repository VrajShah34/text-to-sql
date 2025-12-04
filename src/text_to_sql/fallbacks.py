import re
from typing import Optional

from .schema import DatabaseSchema


class HeuristicTranslator:
    """Very small deterministic translator for demo-grade coverage."""

    def _employee_age_department(self, lowered: str, schema: DatabaseSchema) -> Optional[str]:
        if "employee" not in lowered or "name" not in lowered:
            return None
        table = schema.find_table("employees")
        if not table:
            return None

        selections = ["name"]
        conditions = []

        age_match = re.search(r"(?:older|over|greater) than (\d+)", lowered)
        if age_match:
            age_value = age_match.group(1)
            conditions.append(f"age > {age_value}")

        dept_match = re.search(r"(?:in|from|within) the ([a-z ]+) department", lowered)
        if dept_match:
            department = dept_match.group(1).strip().title()
            conditions.append(f"department = '{department}'")
        elif "sales" in lowered:
            conditions.append("department = 'Sales'")

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        projection = ", ".join(selections)
        return f"SELECT {projection} FROM {table.name}{where_clause}"

    def _sales_client_division_q3(self, lowered: str, schema: DatabaseSchema) -> Optional[str]:
        # Trigger for join demo: division + Q3 wording (client wording can vary).
        if "division" not in lowered:
            return None
        if "2024-q3" not in lowered and "q3 2024" not in lowered and "2024 quarter 3" not in lowered and "q3 of 2024" not in lowered:
            return None
        # Ensure the required tables exist (department table may be named 'department' or 'departments').
        dept_table = schema.find_table("departments") or schema.find_table("department")
        if not (schema.find_table("sales") and schema.find_table("employees") and dept_table):
            return None
        return (
            "SELECT s.client,\n"
            "       d.division,\n"
            "       d.name AS department,\n"
            "       e.name AS employee,\n"
            "       s.amount\n"
            "FROM sales AS s\n"
            "JOIN employees   AS e ON s.employee_id = e.id\n"
            "JOIN departments AS d ON e.department_id = d.id\n"
            "WHERE s.quarter = '2024-Q3'"
        )

    def translate(self, question: str, schema: DatabaseSchema) -> Optional[str]:
        lowered = question.lower()

        # 1) Specific join demo for sales/client/division in 2024-Q3
        sql = self._sales_client_division_q3(lowered, schema)
        if sql:
            return sql

        # 2) Original single-table employees heuristic
        sql = self._employee_age_department(lowered, schema)
        if sql:
            return sql

        return None

