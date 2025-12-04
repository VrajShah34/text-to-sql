# Text-to-SQL Demo

End-to-end natural language -> SQL pipeline aligned to the requested methodology:

1. **Input & Preprocessing** – Tokenizes the NL question with a pretrained tokenizer, performs schema linking/augmentation (column sampling, FK graph), and emits a constrained prompt.
2. **Model Core & Constrained Decoding** – Uses a Spider-tuned T5 checkpoint (`gaussalgo/T5-LM-Large-text2sql-spider` by default) with beam search plus execution-guided filtering.
3. **Postprocessing & Execution** – Sanitizes/validates SQL (tables, clauses, read-only guard), formats it, and executes against SQLite with results rendered in Rich tables.

## Highlights

- Multi-table schema serialization with relation hints (foreign keys) and optional aggregation cues to help joins/subqueries.
- Execution-guided candidate reranking plus deterministic heuristics for common HR-style prompts.
- Demo SQLite database now covers `departments`, `employees`, `projects`, `employee_projects`, and `sales`, so you can test joins/many-to-many relationships locally.
- Spider dataset utility script to convert the official `tables.json` into this pipeline's schema format.
- CLI switches for swapping schema/model/device at runtime (`--schema-path`, `--model-name`, `--device`).

## Project Structure

```
.
├── app.py                      # CLI entry point
├── data/
│   ├── sample.db               # SQLite DB (generated)
│   └── sample_schema.json      # Schema metadata
├── requirements.txt
├── scripts/
│   ├── bootstrap_db.py         # Seeds the demo database (employees + departments)
│   └── import_spider_schema.py # Converts Spider tables.json to schema JSON
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

- **Spider** – ~10k questions spanning 200 DBs with heavy joins/aggregations/subqueries. The default model (`tscholak/lego-base`) is Spider-tuned, and the repo ships with `scripts/import_spider_schema.py` to ingest `tables.json`.
- **WikiSQL** – ~80k simpler single-table queries. Swap in a WikiSQL-tuned checkpoint via `--model-name` if your workload is simpler.

## Setup

```bash
python -m venv .venv
. .venv/Scripts/activate    # PS> .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
python scripts/bootstrap_db.py    # creates data/sample.db with demo rows
```

### Optional: ingest Spider databases

```bash
# Assuming Spider lives in ../spider with tables.json + database/* directories
python scripts/import_spider_schema.py ^
  --tables-json ..\spider\tables.json ^
  --database-dir ..\spider\database ^
  --output data\spider_schema.json

# Run against a Spider DB (e.g., academic.sqlite) with the bundled model
python app.py --question "How many authors have more than 3 papers?" ^
  --schema academic ^
  --schema-path data\spider_schema.json
```

## Usage

```bash
python app.py --question "List the names of employees who are older than 30 and work in the Sales department."
```

Example output:

```
╭─────────────────────────────────────╮
│            NL -> SQL Result         │
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
- Override the model at runtime with `--model-name Salesforce/codet5p-770m-py` (or any other HF checkpoint).
- Tune schema serialization knobs (table/column caps, relation hints, aggregation cues) via `src/text_to_sql/config.py`.
- Plug the `NL2SQLPipeline` class into an API or chat interface for interactive agents.

## Join Example

The enriched sample schema supports multi-table questions. For instance:

- **NL Query:** “Which client deals closed in 2024-Q3 and what division handled them?”
- **Generated SQL:**

```
SELECT s.client,
       d.name AS department,
       d.division,
       e.name AS employee
FROM sales AS s
JOIN employees AS e ON s.employee_id = e.id
JOIN departments AS d ON e.department_id = d.id
WHERE s.quarter = '2024-Q3';
```

Result (based on the seeded data):

```
| client | department | division    | employee     |
|--------|------------|-------------|--------------|
| Globex | Sales      | Enterprise  | Olivia Green |
```

Similar prompts can traverse `employee_projects -> projects -> departments` to reason over many-to-many relationships.