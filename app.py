import argparse
from pathlib import Path

from rich.console import Console

from src.text_to_sql.config import PipelineConfig
from src.text_to_sql.pipeline import NL2SQLPipeline

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NL -> SQL inference.")
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
    parser.add_argument(
        "--schema-path",
        default=None,
        help="Override schema JSON path (useful for Spider).",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Override Hugging Face model checkpoint.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Force device placement (cpu/cuda).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = PipelineConfig()
    if args.schema_path:
        config.schema.schema_path = Path(args.schema_path)
    if args.model_name:
        config.model.model_name = args.model_name
    if args.device:
        config.device = args.device
    pipeline = NL2SQLPipeline(config)
    output = pipeline.run(question=args.question, schema_name=args.schema)
    pipeline.render(output)


if __name__ == "__main__":
    main()

