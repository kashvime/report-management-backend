"""Tests for file upload and the validation run lifecycle.

Covers uploading CSVs, rejecting non-CSV uploads, running validation
against an uploaded file, the recorded errors, the run summary report,
and failed runs.
"""

import io

import pytest

from app.core.config import settings


CSV_CONTENT = (
    "coffee_shop,status\n"
    "Blue Bottle,active\n"
    ",active\n"
    "Blank Street,archived\n"
    "Tatte Bakery,unknown\n"
)

@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    """Point uploads at a temp dir so tests never touch uploads/."""
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def dataset_id(client):
    response = client.post("/api/v1/datasets", json={"name": "Coffee Shop Reports"})
    assert response.status_code == 201
    return response.json()["id"]


def upload_csv(client, dataset_id, content=CSV_CONTENT, filename="coffee_shops.csv"):
    return client.post(
        f"/api/v1/datasets/{dataset_id}/files",
        files={"file": (filename, io.BytesIO(content.encode()), "text/csv")},
    )


def create_rule(client, dataset_id, **overrides):
    payload = {"name": "coffee shop name required", "rule_type": "not_null", "column_name": "coffee_shop"}
    payload.update(overrides)
    response = client.post(f"/api/v1/datasets/{dataset_id}/rules", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


def test_upload_csv_file(client, dataset_id, upload_dir):
    response = upload_csv(client, dataset_id)

    assert response.status_code == 201
    body = response.json()
    assert body["dataset_id"] == dataset_id
    assert body["original_filename"] == "coffee_shops.csv"
    assert body["content_type"] == "text/csv"
    assert body["file_size"] == len(CSV_CONTENT.encode())
    assert body["is_active"] is True

    # The file is stored on disk under uploads/datasets/{dataset_id}/
    stored = list((upload_dir / "datasets" / str(dataset_id)).iterdir())
    assert len(stored) == 1
    assert stored[0].read_text() == CSV_CONTENT


def test_upload_rejects_non_csv_extension(client, dataset_id):
    response = upload_csv(client, dataset_id, filename="coffee_shops.txt")
    assert response.status_code == 400
    assert "Only CSV files are accepted" in response.json()["detail"]


def test_upload_rejects_non_csv_content_type(client, dataset_id):
    response = client.post(
        f"/api/v1/datasets/{dataset_id}/files",
        files={"file": ("coffee_shops.csv", io.BytesIO(b"<html></html>"), "text/html")},
    )
    assert response.status_code == 400


def test_upload_to_missing_dataset_returns_404(client):
    response = upload_csv(client, 999999)
    assert response.status_code == 404


def test_list_and_get_uploaded_files(client, dataset_id):
    file_id = upload_csv(client, dataset_id).json()["id"]

    listed = client.get(f"/api/v1/datasets/{dataset_id}/files")
    assert listed.status_code == 200
    assert [f["id"] for f in listed.json()] == [file_id]

    fetched = client.get(f"/api/v1/datasets/{dataset_id}/files/{file_id}")
    assert fetched.status_code == 200
    assert fetched.json()["original_filename"] == "coffee_shops.csv"

    # A file can't be fetched through a dataset it doesn't belong to
    other = client.post("/api/v1/datasets", json={"name": "Other"}).json()["id"]
    assert client.get(f"/api/v1/datasets/{other}/files/{file_id}").status_code == 404


def test_run_validation_against_uploaded_file(client, dataset_id):
    create_rule(client, dataset_id)
    create_rule(
        client, dataset_id,
        name="status allowed", rule_type="allowed_values", column_name="status",
        params={"values": ["active", "archived"]},
    )
    file_id = upload_csv(client, dataset_id).json()["id"]

    response = client.post(f"/api/v1/datasets/{dataset_id}/files/{file_id}/run-validation")

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == dataset_id
    assert body["file_id"] == file_id
    assert body["status"] == "completed"
    assert body["total_records_checked"] == 4
    assert body["total_errors_found"] == 2  # 1 blank coffee_shop + 1 bad status
    assert body["errors_by_rule"] == {"not_null": 1, "allowed_values": 1}

    # The run record reflects the lifecycle
    run = client.get(f"/api/v1/datasets/{dataset_id}/runs/{body['run_id']}").json()
    assert run["status"] == "completed"
    assert run["file_id"] == file_id
    assert run["started_at"] is not None
    assert run["completed_at"] is not None
    assert run["failure_reason"] is None


def test_run_validation_creates_error_records(client, dataset_id):
    rule_id = create_rule(client, dataset_id)
    file_id = upload_csv(client, dataset_id).json()["id"]

    run_id = client.post(
        f"/api/v1/datasets/{dataset_id}/files/{file_id}/run-validation"
    ).json()["run_id"]

    errors = client.get(f"/api/v1/runs/{run_id}/errors").json()
    assert len(errors) == 1
    error = errors[0]
    assert error["rule_id"] == rule_id
    assert error["rule_type_snapshot"] == "not_null"
    assert error["column_name"] == "coffee_shop"
    assert error["row_number"] == 3  # blank coffee_shop is on CSV line 3
    assert "must not be empty" in error["message"]


def test_run_validation_with_unknown_file_returns_404(client, dataset_id):
    response = client.post(f"/api/v1/datasets/{dataset_id}/files/999999/run-validation")
    assert response.status_code == 404


def test_run_summary(client, dataset_id):
    create_rule(client, dataset_id)
    create_rule(
        client, dataset_id,
        name="status allowed", rule_type="allowed_values", column_name="status",
        params={"values": ["active", "archived"]},
    )
    file_id = upload_csv(client, dataset_id).json()["id"]
    run_id = client.post(
        f"/api/v1/datasets/{dataset_id}/files/{file_id}/run-validation"
    ).json()["run_id"]

    response = client.get(f"/api/v1/validation-runs/{run_id}/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    assert body["dataset_name"] == "Coffee Shop Reports"
    assert body["file_name"] == "coffee_shops.csv"
    assert body["status"] == "completed"
    assert body["total_records_checked"] == 4
    assert body["total_errors_found"] == 2
    assert body["errors_by_rule_type"] == {"not_null": 1, "allowed_values": 1}
    assert body["errors_by_field"] == {"coffee_shop": 1, "status": 1}


def test_run_summary_for_missing_run_returns_404(client):
    assert client.get("/api/v1/validation-runs/999999/summary").status_code == 404


def test_failed_run_is_recorded_cleanly(client, dataset_id):
    # A rule against a column the CSV doesn't have makes the run fail
    create_rule(client, dataset_id, name="bad rule", column_name="no_such_column")
    file_id = upload_csv(client, dataset_id).json()["id"]

    response = client.post(f"/api/v1/datasets/{dataset_id}/files/{file_id}/run-validation")
    assert response.status_code == 422

    # The failed run is kept with its failure_reason and timestamps
    runs = client.get(f"/api/v1/datasets/{dataset_id}/runs").json()
    assert len(runs) == 1
    run = runs[0]
    assert run["status"] == "failed"
    assert "no_such_column" in run["failure_reason"]
    assert run["started_at"] is not None
    assert run["completed_at"] is not None

    # No error records survive from the failed run
    assert client.get(f"/api/v1/runs/{run['id']}/errors").json() == []

    # And the summary endpoint reports the failure
    summary = client.get(f"/api/v1/validation-runs/{run['id']}/summary").json()
    assert summary["status"] == "failed"
    assert summary["errors_by_rule_type"] == {}
    assert summary["errors_by_field"] == {}
