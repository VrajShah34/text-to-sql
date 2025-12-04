import os
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from google import genai

# --- Type Definitions ---

QueryResult = List[Tuple[Any, ...]]
DatabaseSchema = Dict[str, List[Dict[str, str]]]

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "Spider_db"


# --- Database Utilities ---

def extract_schema(db_path: str) -> DatabaseSchema:
    """
    Extracts the schema from a SQLite database.
    Returns a dictionary where keys are table names and values are lists of column details.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        schema: DatabaseSchema = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            # column structure from PRAGMA: (cid, name, type, notnull, dflt_value, pk)
            schema[table_name] = [
                {"name": col[1], "type": col[2]} for col in columns
            ]

        conn.close()
        return schema
    except sqlite3.Error as e:
        print(f"Error extracting schema from {db_path}: {e}")
        return {}


# --- Gemini Client ---

class GeminiClient:
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Client that uses google.genai to generate an SQL query.
        Reads GEMINI_API_KEY from the environment.
        """
        self.model = model
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            # You *can* hardcode for local dev, but env var is better.
            # api_key = "YOUR_DEV_KEY_HERE"
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=api_key)

    def get_sql_query(self, user_query: str, schema: DatabaseSchema) -> str:
        """
        Asks the Gemini model to produce a JSON object with a single key
        "sql_query" whose value is the SQL string. Returns that SQL string.
        """
        prompt = (
            "You are an assistant that translates a natural language request into a valid SQL query.\n"
            "Return only a JSON object with a single key \"sql_query\" whose value is the SQL string.\n"
            "Do not include markdown formatting or code fences.\n\n"
            f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
            f"User request: {user_query}\n"
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        # response.text is the typical attribute containing the model output
        text = getattr(response, "text", None)
        if text is None:
            text = str(response)

        # Clean up potential markdown code blocks
        text = re.sub(r"```", "", text)
        text = re.sub(r"json\s*", "", text)
        text = text.strip()

        try:
            data = json.loads(text)
        except ValueError as e:
            raise Exception(f"Invalid JSON response from Gemini API: {text}") from e

        return data.get("sql_query", "")


def discover_schema_choices() -> List[str]:
    """
    Look into Spider_db and list all *.sqlite files as schema choices.
    The stem (filename without .sqlite) becomes the schema name.
    """
    if not DB_DIR.exists():
        return []
    return [p.stem for p in DB_DIR.glob("*.sqlite")]


def get_db_path(schema_name: Optional[str]) -> str:
    """
    Map schema_name from the dropdown to an actual .sqlite file.
    Fallbacks:
      - If given schema exists, use it.
      - Else if we have any schemas, use the first one.
      - Else default to Spider_db/college.sqlite.
    """
    if schema_name:
        candidate = DB_DIR / f"{schema_name}.sqlite"
        if candidate.exists():
            return str(candidate)

    choices = discover_schema_choices()
    if choices:
        return str(DB_DIR / f"{choices[0]}.sqlite")

    # Last resort
    return str(DB_DIR / "college.sqlite")


# --- Initialize Gemini client once ---

try:
    gemini_client = GeminiClient()
    GEMINI_INIT_ERROR = ""
except Exception as e:
    gemini_client = None
    GEMINI_INIT_ERROR = f"Error initializing Gemini client: {e}"


# --- Main function used by frontend ---

def run_llm_sql_pipeline(
    question: str,
    schema_name: Optional[str],
) -> Tuple[str, List[str], List[List[Any]], str]:
    """
    Replacement for the old _run_pipeline:
    - choose DB based on schema_name
    - extract schema
    - ask Gemini for SQL
    - execute SQL
    - return (sql_text, columns, rows, error_message)
    """
    if GEMINI_INIT_ERROR:
        return "", [], [], GEMINI_INIT_ERROR

    if gemini_client is None:
        return "", [], [], "Gemini client is not initialized."

    db_path = get_db_path(schema_name)

    if not os.path.exists(db_path):
        return "", [], [], f"Database file not found for schema '{schema_name or ''}'."

    schema = extract_schema(db_path)
    if not schema:
        return "", [], [], "Could not extract database schema (database may be empty)."

    # Get the SQL query from the Gemini LLM
    try:
        sql_query = gemini_client.get_sql_query(question, schema)
    except Exception as e:
        return "", [], [], f"Error generating SQL from LLM: {e}"

    if not sql_query or not sql_query.strip():
        return "", [], [], "Model did not return a SQL query."

    # Execute the SQL query on the SQLite database
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = [list(r) for r in results]
    except sqlite3.Error as e:
        return sql_query, [], [], f"Error executing SQL: {e}"
    finally:
        if conn is not None:
            conn.close()

    return sql_query, columns, rows, ""


# Exported for frontend
SCHEMA_CHOICES: List[str] = discover_schema_choices()
