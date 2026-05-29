# Data Quality & Report Management Backend

A FastAPI + PostgreSQL backend for managing datasets and tracking data quality
through validation rules, runs, and errors.

**Stack:** FastAPI · PostgreSQL (SQLAlchemy ORM) · Alembic · Pydantic v2

---

## Getting Started

**Prerequisites:** Python 3.12+ · PostgreSQL running locally

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

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` in the project root:

```
DATABASE_URL=postgresql://report_management_user:yourpassword@localhost:5432/report_management_db
```

### 6. Run migrations

```bash
alembic upgrade head
```

### 7. Start the server

```bash
uvicorn main:app --reload
```

Once running:
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## Data Model

```
Dataset
├── ValidationRule   (many per dataset)
└── ValidationRun    (many per dataset)
        └── ValidationError  (many per run)
```

`Dataset` is the root entity. Rules and runs belong to a dataset; errors belong
to a run and reference the rule that failed.

| Model             | Description                               | Relationships                                        |
| ----------------- | ----------------------------------------- | ---------------------------------------------------- |
| `Dataset`         | Root data source being checked            | Owns rules and runs; delete cascades to both         |
| `ValidationRule`  | A reusable quality rule for a dataset     | Belongs to one dataset; referenced by errors         |
| `ValidationRun`   | One execution of validation on a dataset  | Belongs to one dataset; owns errors (cascade delete) |
| `ValidationError` | A single failure recorded during a run    | Belongs to one run; nullable link to the failed rule |

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

| Method   | Path                                   | Action       |
| -------- | -------------------------------------- | ------------ |
| `POST`   | `/datasets/{dataset_id}/runs`          | Create a run |
| `GET`    | `/datasets/{dataset_id}/runs`          | List runs    |
| `GET`    | `/datasets/{dataset_id}/runs/{run_id}` | Get a run    |
| `PATCH`  | `/datasets/{dataset_id}/runs/{run_id}` | Update a run |
| `DELETE` | `/datasets/{dataset_id}/runs/{run_id}` | Delete a run |

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

## Architecture

The app is structured in three layers:

**Models** (`app/models/`) define the database schema using SQLAlchemy ORM.

**Schemas** (`app/schemas/`) define what the API accepts and returns using Pydantic.

**Endpoints** (`app/api/v1/endpoints/`) wire HTTP requests to database operations.

```
app/
├── api/v1/
│   ├── endpoints/       # route handlers
│   ├── dependencies.py  # shared dependencies (get_db)
│   └── router.py        # combines all routers
├── core/
│   └── config.py        # environment config
├── db/
│   ├── base.py          # SQLAlchemy Base
│   └── session.py       # engine and get_db
├── models/              # ORM models
└── schemas/             # Pydantic schemas
alembic/                 # migrations
main.py                  # app entry point
```

---
