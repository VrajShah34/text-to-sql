from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from rich import box
from rich.console import Console
from rich.table import Table

from .config import PipelineConfig
from .executor import ExecutionResult, SQLiteExecutor
from .fallbacks import HeuristicTranslator
from .model import SQLCandidate, TextToSQLModel
from .postprocess import pretty_format, sanitize_sql, validate_sql
from .schema import DatabaseSchema, load_schema

console = Console()


@dataclass
class PipelineOutput:
    sql: str
    result: Optional[ExecutionResult]
    validation_error: Optional[str] = None


class NL2SQLPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.schemas = load_schema(config.schema.schema_path)
        self.model = TextToSQLModel(config)
        self.heuristic = HeuristicTranslator()

    def _find_schema(self, name: Optional[str] = None) -> DatabaseSchema:
        if name:
            for schema in self.schemas:
                if schema.name.lower() == name.lower():
                    return schema
            raise ValueError(f"Schema {name} not found.")
        return self.schemas[0]

    def run(self, question: str, schema_name: Optional[str] = None) -> PipelineOutput:
        schema = self._find_schema(schema_name)
        candidates = self.model.generate(question, schema)
        for candidate in candidates:
            cleaned = sanitize_sql(candidate.sql)
            validation_error = validate_sql(cleaned, schema)
            if validation_error:
                continue
            executor = SQLiteExecutor(schema.path)
            try:
                result = executor.execute(cleaned)
                return PipelineOutput(sql=pretty_format(cleaned), result=result)
            except Exception as exc:
                if self.config.verbose:
                    console.print(f"[yellow]Execution failure for candidate SQL:[/yellow] {exc}")
                continue
        # if none succeeded, surface first error
        fallback_sql = self.heuristic.translate(question, schema)
        if fallback_sql:
            executor = SQLiteExecutor(schema.path)
            try:
                result = executor.execute(fallback_sql)
                return PipelineOutput(sql=pretty_format(fallback_sql), result=result)
            except Exception:
                pass

        first = candidates[0] if candidates else None
        return PipelineOutput(
            sql=first.sql if first else "",
            result=None,
            validation_error="All candidate SQLs failed validation or execution.",
        )

    def render(self, output: PipelineOutput) -> None:
        console.rule("[bold green]NL -> SQL Result")
        console.print("[bold cyan]SQL[/bold cyan]")
        console.print(output.sql or "[red]No SQL generated[/red]")
        if output.validation_error:
            console.print(f"[red]Validation error:[/red] {output.validation_error}")
        if output.result:
            table = Table(title="Query Result", box=box.SIMPLE_HEAD)
            for column in output.result.columns:
                table.add_column(column)
            for row in output.result.rows:
                table.add_row(*[str(value) for value in row])
            console.print(table)

