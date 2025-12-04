from dataclasses import dataclass
from typing import Dict, List, Tuple, TYPE_CHECKING, Set

if TYPE_CHECKING:
    import torch

from transformers import PreTrainedTokenizerBase

from .config import SchemaConfig
from .schema import DatabaseSchema, Table


@dataclass
class PreprocessorOutput:
    prompt: str
    linked_columns: List[Tuple[str, str]]
    encoded_inputs: Dict[str, "torch.Tensor"]  # type: ignore[name-defined]
    schema_prompt: str
    aggregations: List[str]


class SchemaLinker:
    def __init__(self, fuzzy_threshold: float = 0.7):
        self.fuzzy_threshold = fuzzy_threshold

    @staticmethod
    def normalize(text: str) -> str:
        return text.lower().replace("_", " ")

    def link(self, question: str, tables: List[Table]) -> List[Tuple[str, str]]:
        matches: List[Tuple[str, str]] = []
        normalized_question = self.normalize(question)
        for table in tables:
            for column in table.columns:
                alias = self.normalize(column.name)
                if alias in normalized_question:
                    matches.append((table.name, column.name))
        return matches


class SchemaSerializer:
    def __init__(self, config: SchemaConfig, include_relations: bool = True):
        self.config = config
        self.include_relations = include_relations

    def _serialize_table(self, table: Table) -> str:
        columns = table.columns[: self.config.max_columns_per_table]
        column_fragments = [f"{col.name} {col.type}" for col in columns]
        snippet = ", ".join(column_fragments)
        if self.config.include_sample_values and table.sample_values:
            samples = []
            for col_name, values in table.sample_values.items():
                joined = "/".join(values[:2])
                samples.append(f"{col_name}≈{joined}")
            if samples:
                snippet += f" [samples: {', '.join(samples)}]"
        return f"{table.name}({snippet})"

    def serialize(self, schema: DatabaseSchema, linked_tables: Set[str]) -> str:
        prioritized = []
        seen = set()
        for tbl_name in linked_tables:
            table = schema.find_table(tbl_name)
            if table and table.name not in seen:
                prioritized.append(table)
                seen.add(table.name)
        for table in schema.tables:
            if table.name not in seen:
                prioritized.append(table)
                seen.add(table.name)
        tables = prioritized[: self.config.max_tables]
        table_section = " | ".join(self._serialize_table(table) for table in tables)
        relation_section = ""
        if self.include_relations and schema.foreign_keys:
            relations = schema.relation_strings()[: self.config.max_tables]
            relation_section = " || relations: " + "; ".join(relations)
        return table_section + relation_section


class Preprocessor:
    AGG_KEYWORDS = {
        "count": "COUNT",
        "total": "SUM",
        "sum": "SUM",
        "average": "AVG",
        "avg": "AVG",
        "maximum": "MAX",
        "highest": "MAX",
        "minimum": "MIN",
        "lowest": "MIN",
    }

    def __init__(
        self,
        tokenizer: PreTrainedTokenizerBase,
        schema_config: SchemaConfig,
        include_relations: bool = True,
        max_length: int = 512,
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.linker = SchemaLinker()
        self.serializer = SchemaSerializer(schema_config, include_relations=include_relations)

    def _aggregation_hints(self, question: str) -> List[str]:
        lowered = question.lower()
        hints: List[str] = []
        for keyword, sql_op in self.AGG_KEYWORDS.items():
            if keyword in lowered and sql_op not in hints:
                hints.append(sql_op)
        return hints

    def build_model_input(self, question: str, schema: DatabaseSchema) -> PreprocessorOutput:
        linked = self.linker.link(question, schema.tables)
        linked_table_names = {table for table, _ in linked}
        schema_prompt = self.serializer.serialize(schema, linked_table_names)
        agg_hints = self._aggregation_hints(question)
        agg_fragment = f" || agg_hints: {', '.join(agg_hints)}" if agg_hints else ""
        prompt = f"translate to SQL: {question} || schema: {schema_prompt}{agg_fragment}"
        encoded = self.tokenizer(
            prompt,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        return PreprocessorOutput(
            prompt=prompt,
            linked_columns=linked,
            encoded_inputs=encoded,
            schema_prompt=schema_prompt,
            aggregations=agg_hints,
        )

