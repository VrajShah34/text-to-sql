from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 🔹 New: import from the LLM+SQLite backend instead of old pipeline
from backend_llm import run_llm_sql_pipeline, SCHEMA_CHOICES, GEMINI_INIT_ERROR

app = FastAPI(title="Text-to-SQL Dashboard")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "schemas": SCHEMA_CHOICES,
            "selected_schema": "",
            "question_value": "",
            "sql_text": "",
            "columns": [],
            "rows": [],
            "error": GEMINI_INIT_ERROR,  # show init error (e.g., missing API key)
        },
    )


@app.post("/query", response_class=HTMLResponse)
async def query(
    request: Request,
    question: str = Form(...),
    schema_name: Optional[str] = Form(None),
):
    question = question.strip()
    sql_text = ""
    columns: List[str] = []
    rows: List[List[str]] = []
    error = ""

    if not question:
        error = "Please enter a natural-language question."
    else:
        # 🔹 New: call our LLM+SQLite backend instead of the old pipeline
        sql_text, columns, rows, err = run_llm_sql_pipeline(question, schema_name)
        if err:
            error = err

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "schemas": SCHEMA_CHOICES,
            "selected_schema": schema_name or "",
            "question_value": question,
            "sql_text": sql_text,
            "columns": columns,
            "rows": rows,
            "error": error,
        },
    )
