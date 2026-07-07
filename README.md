<div align="center">

# Data Quality & Report Management Backend

A FastAPI + PostgreSQL backend for managing datasets and tracking data quality
through validation rules, runs, and errors.

<br>

![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-6BA81E?style=for-the-badge)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge)

</div>

---

## Getting Started

> **Prerequisites:** Python 3.14+ · PostgreSQL running locally

### 1. Clone the repo

```bash
git clone https://github.com/kashvime/report-management-backend.git
cd report-management-backend
```

### 2. Create the database

Open `psql` and run:

```sql
CREATE DATABASE report_management_db;
CREATE USER report_management_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE report_management_db TO report_management_user;
\c report_management_db
GRANT ALL ON SCHEMA public TO report_management_user;
\q
```

### 3. Create and activate a virtual environment

This project uses uv for dependency management. It creates the virtual environment and installs all dependencies from the project configuration in a single step. 

Install uv using either:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
or

```bash
pip install uv
```

### 4. Install dependencies

```bash
uv sync
```

### 5. Configure environment variables

Create a `.env` in the project root:

```
DATABASE_URL=postgresql://report_management_user:yourpassword@localhost:5432/report_management_db
```

### 6. Run migrations

```bash
uv run alembic upgrade head
```

### 7. Seed sample data (optional)

Loads the sample datasets in `sample_data/` along with their validation rules,
so you have something to run validations against right away:

```bash
uv run python -m app.scripts.seed_data
```

### 8. Start the server

```bash
uv run uvicorn main:app --reload
```

> API docs → http://localhost:8000/docs &nbsp;&nbsp;|&nbsp;&nbsp; Health check → http://localhost:8000/health

---

## Data Model

```
Dataset
├── ValidationRule   (many per dataset)
├── DatasetFile      (many per dataset)
└── ValidationRun    (many per dataset, optionally linked to a file)
        └── ValidationError  (many per run)
```

`Dataset` is the root entity. Rules, uploaded files, and runs belong to a
dataset; errors belong to a run and reference the rule that failed.

| Model             | Description                               | Relationships                                          |
| ----------------- | ----------------------------------------- | ------------------------------------------------------ |
| `Dataset`         | Root data source being checked            | Owns rules, files, and runs; delete cascades to all    |
| `ValidationRule`  | A reusable quality rule for a dataset     | Belongs to one dataset; referenced by errors           |
| `DatasetFile`     | An uploaded CSV stored on local disk      | Belongs to one dataset; referenced by runs             |
| `ValidationRun`   | One execution of validation on a dataset  | Belongs to one dataset; owns errors (cascade delete); nullable link to the file it validated |
| `ValidationError` | A single failure recorded during a run    | Belongs to one run; nullable link to the failed rule   |

---

## API Routes

All routes are prefixed with `/api/v1`. Routes are nested to reflect ownership —
rules and runs live under a dataset, errors live under a run.

<details>
<summary>Datasets — <code>/datasets</code></summary>
<br>

| Method   | Path             | Action           |
| -------- | ---------------- | ---------------- |
| `POST`   | `/datasets`      | Create a dataset |
| `GET`    | `/datasets`      | List datasets    |
| `GET`    | `/datasets/{id}` | Get a dataset    |
| `PATCH`  | `/datasets/{id}` | Update a dataset |
| `DELETE` | `/datasets/{id}` | Delete a dataset |

</details>

<details>
<summary>Dataset Files — <code>/datasets/{dataset_id}/files</code></summary>
<br>

| Method | Path                                                      | Action                                        |
| ------ | --------------------------------------------------------- | --------------------------------------------- |
| `POST` | `/datasets/{dataset_id}/files`                             | Upload a CSV (multipart form, `file` field)   |
| `GET`  | `/datasets/{dataset_id}/files`                             | List uploaded files                           |
| `GET`  | `/datasets/{dataset_id}/files/{file_id}`                   | Get an uploaded file's metadata               |
| `POST` | `/datasets/{dataset_id}/files/{file_id}/run-validation`    | **Run all active rules against the file**     |

Only CSV uploads are accepted (extension + content type checked; anything else
is rejected with `400`). Files are stored locally under
`uploads/datasets/{dataset_id}/` with a generated filename so uploads never
collide; the original filename is kept for display.

</details>

<details>
<summary>Validation Rules — <code>/datasets/{dataset_id}/rules</code></summary>
<br>

| Method   | Path                                     | Action        |
| -------- | ---------------------------------------- | ------------- |
| `POST`   | `/datasets/{dataset_id}/rules`           | Create a rule |
| `GET`    | `/datasets/{dataset_id}/rules`           | List rules    |
| `GET`    | `/datasets/{dataset_id}/rules/{rule_id}` | Get a rule    |
| `PATCH`  | `/datasets/{dataset_id}/rules/{rule_id}` | Update a rule |
| `DELETE` | `/datasets/{dataset_id}/rules/{rule_id}` | Delete a rule |

</details>

<details>
<summary>Validation Runs — <code>/datasets/{dataset_id}/runs</code></summary>
<br>

| Method   | Path                                            | Action                                          |
| -------- | ----------------------------------------------- | ----------------------------------------------- |
| `POST`   | `/datasets/{dataset_id}/run-validation`         | **Run all active rules against the sample CSV** |
| `GET`    | `/validation-runs/{run_id}/summary`             | **Aggregated run summary** (see below)          |
| `POST`   | `/datasets/{dataset_id}/runs`                   | Create a run                                    |
| `GET`    | `/datasets/{dataset_id}/runs`                   | List runs                                       |
| `GET`    | `/datasets/{dataset_id}/runs/{run_id}`          | Get a run                                       |
| `PATCH`  | `/datasets/{dataset_id}/runs/{run_id}`          | Update a run                                    |
| `DELETE` | `/datasets/{dataset_id}/runs/{run_id}`          | Delete a run                                    |

The `run-validation` endpoints (here and under files) execute the dataset's
active rules and return a summary — records checked, total errors, and a
per-rule-type error breakdown.

`GET /validation-runs/{run_id}/summary` returns a richer report for any run:
dataset name, file name, status, totals, and error counts grouped both by rule
type (`errors_by_rule_type`) and by column (`errors_by_field`).

**Run lifecycle.** Every run moves through `pending → running → completed`
(or `failed`), with `started_at` / `completed_at` timestamps. A failed run is
kept with its `failure_reason` (e.g. a missing file or a rule referencing a
column the CSV doesn't have), and any partially recorded errors are discarded.

</details>

<details>
<summary>Validation Errors — <code>/runs/{run_id}/errors</code> (immutable, no update)</summary>
<br>

| Method   | Path                               | Action          |
| -------- | ---------------------------------- | --------------- |
| `POST`   | `/runs/{run_id}/errors`            | Create an error |
| `GET`    | `/runs/{run_id}/errors`            | List errors     |
| `GET`    | `/runs/{run_id}/errors/{error_id}` | Get an error    |
| `DELETE` | `/runs/{run_id}/errors/{error_id}` | Delete an error |

</details>

---

## Validation Engine

Validation can run against two sources:

- **An uploaded file** — `POST /datasets/{dataset_id}/files/{file_id}/run-validation`
  reads the uploaded CSV from `uploads/`.
- **The seeded sample CSV** — `POST /datasets/{dataset_id}/run-validation` loads
  the dataset's CSV from `sample_data/`.

Either way, the engine creates a run (`pending → running`), applies every
**active** rule, persists one `ValidationError` per failing row, marks the run
`completed` (or `failed` with a `failure_reason`), and returns a run summary
including `errors_by_rule` (counts grouped by rule type).

Each rule has a `rule_type`, a target `column_name`, and an optional `params`
object. `params` may include a `when` clause that restricts the rule to matching
rows (e.g. only check `closed_date` is present `when status == "Closed"`).

<details>
<summary>Sample datasets (seeded by <code>seed_data.py</code>)</summary>
<br>

| Dataset                | File                       | Rows | What it is                                                                         |
| ---------------------- | -------------------------- | ---- | ---------------------------------------------------------------------------------- |
| **Claims**             | `claim_data.csv`           | 597  | Healthcare insurance claims — billed/allowed/paid amounts, service dates, status   |
| **Financial Accounts** | `financial_accounts.csv`   | 193  | Bank accounts — type, open/closed dates, balance, status                           |
| **Travel Information** | `travel_information.csv`   | 99   | Customer travel profiles — contact info, loyalty tier, trip budget, destination    |

</details>

| Rule type        | Checks that…                                          |
| ---------------- | ----------------------------------------------------- |
| `not_null`       | the column is non-empty                               |
| `unique`         | values in the column are unique                       |
| `value_range`    | a numeric value is within `min`/`max`                 |
| `allowed_values` | the value is one of an allowed set                    |
| `not_future_date`| a date is not in the future                           |
| `column_gte`     | the column is ≥ another column                        |
| `date_lte_column`| a date is on or before another column's date          |
| `must_be_blank`  | the column is blank                                   |
| `regex_match`    | the value matches a regex `pattern`                   |

The engine lives in `app/services/` — `rules.py` (pure per-rule checkers),
`validation_engine.py` (orchestration and run lifecycle), and
`file_storage.py` (CSV upload validation and local storage). See
`app/scripts/seed_data.py` for worked examples of every rule type.

---

## Running Tests

Tests run against the configured Postgres database, each wrapped in a
transaction that is rolled back, so nothing is persisted:

```bash
uv run pytest
```

---

## Architecture

The app is structured in layers:

**Models** (`app/models/`) define the database schema using SQLAlchemy ORM.

**Schemas** (`app/schemas/`) define what the API accepts and returns using Pydantic.

**Endpoints** (`app/api/v1/endpoints/`) wire HTTP requests to database operations.

**Services** (`app/services/`) hold the validation engine and business logic,
kept independent of the HTTP layer.

```
app/
├── api/v1/
│   ├── endpoints/       # route handlers
│   ├── dependencies.py  # shared dependencies (get_db, 404 helpers)
│   └── router.py        # combines all routers
├── core/
│   └── config.py        # environment config
├── db/
│   ├── base.py          # SQLAlchemy Base
│   └── session.py       # engine and get_db
├── models/              # ORM models
├── schemas/             # Pydantic schemas
├── services/            # validation engine + business logic
├── scripts/             # seed_data and other CLI scripts
└── utils.py             # shared helpers
sample_data/             # sample CSVs for seeded datasets
uploads/                 # uploaded dataset files (created at runtime, gitignored)
tests/                   # pytest suite
alembic/                 # migrations
main.py                  # app entry point
```
