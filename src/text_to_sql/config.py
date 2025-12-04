from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ModelConfig:
    model_name: str = "tscholak/lego-base"
    max_input_tokens: int = 512
    max_output_tokens: int = 196
    num_beams: int = 6
    temperature: float = 0.0


@dataclass
class SchemaConfig:
    schema_path: Path = Path("data/sample_schema.json")
    default_db_path: Path = Path("data/sample.db")
    max_tables: int = 6
    max_columns_per_table: int = 16
    include_sample_values: bool = True


@dataclass
class PipelineConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    schema: SchemaConfig = field(default_factory=SchemaConfig)
    device: Optional[str] = None
    enable_execution_guidance: bool = True
    top_k: int = 3
    stop_tokens: List[str] = field(default_factory=lambda: ["<pad>", "</s>"])
    include_relations_in_prompt: bool = True
    max_relation_paths: int = 3

