import re
from typing import Optional

from .schema import DatabaseSchema


class HeuristicTranslator:
    """Very small deterministic translator for demo-grade coverage."""

    def translate(self, question: str, schema: DatabaseSchema) -> Optional[str]:
        lowered = question.lower()
        if "employee" not in lowered:
            return None
        if "name" not in lowered:
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

