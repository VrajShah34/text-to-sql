from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.text_to_sql.config import PipelineConfig
from src.text_to_sql.pipeline import NL2SQLPipeline

app = FastAPI(title="Text-to-SQL Dashboard")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Instantiate pipeline once with quiet logging for the dashboard UI
web_config = PipelineConfig()
web_config.verbose = False
pipeline = NL2SQLPipeline(web_config)
SCHEMA_CHOICES: List[str] = [schema.name for schema in pipeline.schemas]


def _run_pipeline(question: str, schema_name: Optional[str]):
    output = pipeline.run(question=question, schema_name=schema_name or None)
    result_rows = output.result.rows if output.result else []
    result_columns = output.result.columns if output.result else []
    error = output.validation_error
    return output.sql, result_columns, result_rows, error


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
            "error": "",
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
        sql_text, columns, rows, err = _run_pipeline(question, schema_name)
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

