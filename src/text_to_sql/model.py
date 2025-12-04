from __future__ import annotations

from dataclasses import dataclass
from typing import List

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from .config import PipelineConfig
from .preprocess import Preprocessor, PreprocessorOutput
from .schema import DatabaseSchema


@dataclass
class SQLCandidate:
    sql: str
    score: float
    metadata: PreprocessorOutput


class TextToSQLModel:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config.model.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(config.model.model_name)
        self.device = torch.device(config.device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model.to(self.device)
        self.preprocessor = Preprocessor(
            tokenizer=self.tokenizer,
            schema_config=config.schema,
            include_relations=config.include_relations_in_prompt,
            max_length=config.model.max_input_tokens,
        )

    def _prepare_inputs(self, pre_out: PreprocessorOutput) -> dict:
        encoded = {k: v.to(self.device) for k, v in pre_out.encoded_inputs.items()}
        return encoded

    def generate(self, question: str, schema: DatabaseSchema) -> List[SQLCandidate]:
        pre_out = self.preprocessor.build_model_input(question, schema)
        inputs = self._prepare_inputs(pre_out)
        generation = self.model.generate(
            **inputs,
            max_new_tokens=self.config.model.max_output_tokens,
            num_beams=self.config.model.num_beams,
            early_stopping=True,
            num_return_sequences=self.config.top_k,
            return_dict_in_generate=True,
            output_scores=True,
            temperature=self.config.model.temperature,
        )
        sequences = generation.sequences
        scores = generation.sequences_scores
        candidates: List[SQLCandidate] = []
        for seq, score in zip(sequences, scores):
            decoded = self.tokenizer.decode(seq, skip_special_tokens=True)
            candidates.append(SQLCandidate(sql=decoded.strip(), score=score.item(), metadata=pre_out))
        return candidates

