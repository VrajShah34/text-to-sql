# Text-to-SQL Demo

End-to-end natural language → SQL pipeline that follows the requested methodology:

1. **Input & Preprocessing** – Tokenizes the user question with a pretrained tokenizer, links schema terms, and builds a structured prompt.
2. **Model Core & Constrained Decoding** – Uses a T5-family model (`mrm8488/t5-base-finetuned-wikiSQL`) to autoregressively decode SQL with beam search.
3. **Postprocessing & Execution** – Validates, formats, and executes the generated SQL against SQLite, returning tabular results.

The demo ships with a `company` database containing an `employees` table populated via `scripts/bootstrap_db.py`. It can be swapped with richer databases (e.g., WikiSQL tables).

## Project Structure

```
.
├── app.py                      # CLI entry point
├── data/
│   ├── sample.db               # SQLite DB (generated)
│   └── sample_schema.json      # Schema metadata
├── requirements.txt
├── scripts/
│   └── bootstrap_db.py         # Seeds the demo database
└── src/text_to_sql/
    ├── __init__.py
    ├── config.py               # Config dataclasses
    ├── executor.py             # SQLite execution helper
    ├── model.py                # Hugging Face model wrapper
    ├── pipeline.py             # Orchestrates NL→SQL pipeline
    ├── postprocess.py          # SQL sanitization/validation
    └── preprocess.py           # Tokenization & schema linking
```

## Datasets

- **WikiSQL** – ~80k NL/SQL pairs across 700 tables; ideal for baseline models.
- **Spider** (page 6/17 excerpt) – ~10k questions spanning 200 DBs with complex SQL (joins, aggregations, subqueries). The provided pipeline can fine-tune on these datasets using Hugging Face `datasets` if desired.

## Setup

```bash
python -m venv .venv
. .venv/Scripts/activate    # PS> .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
python scripts/bootstrap_db.py    # creates data/sample.db with demo rows
```

## Usage

```bash
python app.py --question "List the names of employees who are older than 30 and work in the Sales department."
```

Example output:

```
╭─────────────────────────────────────╮
│            NL → SQL Result          │
╰─────────────────────────────────────╯
SQL
SELECT
  name
FROM employees
WHERE age > 30
  AND department = 'Sales'

Query Result
| name             |
|------------------|
| Ava Thompson     |
| Sophia Nguyen    |
| Ethan Patel      |
| Olivia Green     |
```

## Extending

- Swap `data/sample_schema.json` with schemas extracted from WikiSQL/Spider.
- Fine-tune or replace the model in `src/text_to_sql/config.py`.
- Plug the `NL2SQLPipeline` class into an API or chat interface for interactive agents.