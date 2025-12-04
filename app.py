import argparse

from rich.console import Console

from src.text_to_sql.config import PipelineConfig
from src.text_to_sql.pipeline import NL2SQLPipeline

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NL → SQL inference.")
    parser.add_argument(
        "--question",
        required=True,
        help="Natural language question to translate.",
    )
    parser.add_argument(
        "--schema",
        default=None,
        help="Database schema name to target (defaults to first schema).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = NL2SQLPipeline(PipelineConfig())
    output = pipeline.run(question=args.question, schema_name=args.schema)
    pipeline.render(output)


if __name__ == "__main__":
    main()

