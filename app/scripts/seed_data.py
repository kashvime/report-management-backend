"""Seed every sample dataset and its validation rules.

Run with:  uv run python -m app.scripts.seed_data

Each dataset lists its rules as (name, rule_type, column_name, params). Rules
are active by default. The `params` dict carries each rule type's config and,
optionally, a `when` clause that restricts the rule to matching rows.
"""

from app.db.session import SessionLocal
from app.models.dataset import Dataset
from app.models.validation_rule import ValidationRule

# Email format: non-empty local part, one @, a dotted domain.
EMAIL_PATTERN = r"[^@\s]+@[^@\s]+\.[^@\s]+"

DATASETS = [
    {
        "name": "Claims",
        "file_name": "claim_data.csv",
        "rules": [
            ("claim_id present", "not_null", "claim_id", None),
            ("provider_id present", "not_null", "provider_id", None),
            ("patient_id present", "not_null", "patient_id", None),
            ("service date not in future", "not_future_date", "date_of_service", None),
            ("billed amount non-negative", "value_range", "billed_amount", {"min": 0}),
            ("allowed amount non-negative", "value_range", "allowed_amount", {"min": 0}),
            ("paid amount non-negative", "value_range", "paid_amount", {"min": 0}),
            ("billed >= allowed", "column_gte", "billed_amount", {"other": "allowed_amount"}),
            ("allowed >= paid", "column_gte", "allowed_amount", {"other": "paid_amount"}),
            ("insurance type valid", "allowed_values", "insurance_type",
             {"values": ["Self-Pay", "Medicaid", "Commercial", "Medicare"]}),
            ("follow up valid", "allowed_values", "follow_up_required", {"values": ["Yes", "No"]}),
            ("claim status valid", "allowed_values", "claim_status",
             {"values": ["Paid", "Under Review", "Denied"]}),
        ],
    },
    {
        "name": "Financial Accounts",
        "file_name": "financial_accounts.csv",
        "rules": [
            ("account_id unique", "unique", "account_id", None),
            ("account_id present", "not_null", "account_id", None),
            ("customer_id present", "not_null", "customer_id", None),
            ("open_date present", "not_null", "open_date", None),
            ("account_type valid", "allowed_values", "account_type",
             {"values": ["Credit", "Checking", "Savings"]}),
            ("status valid", "allowed_values", "status", {"values": ["Open", "Closed"]}),
            ("registration_id valid", "allowed_values", "registration_id", {"values": [1, 2, 3]}),
            ("closed_date not in future", "not_future_date", "closed_date", {"format": "%Y-%m-%d"}),
            ("open_date on or before closed_date", "date_lte_column", "open_date",
             {"other": "closed_date", "format": "%Y-%m-%d"}),
            ("closed_date present when closed", "not_null", "closed_date",
             {"when": {"column": "status", "equals": "Closed"}}),
            ("closed_date blank when open", "must_be_blank", "closed_date",
             {"when": {"column": "status", "equals": "Open"}}),
            ("deposit balance non-negative", "value_range", "balance",
             {"min": 0, "when": {"column": "account_type", "in": ["Checking", "Savings"]}}),
        ],
    },
    {
        "name": "Travel Information",
        "file_name": "travel_information.csv",
        "rules": [
            ("email format valid", "regex_match", "email", {"pattern": EMAIL_PATTERN}),
            ("customer_id unique", "unique", "customer_id", None),
            ("email unique", "unique", "email", None),
            ("loyalty tier valid", "allowed_values", "loyalty_tier",
             {"values": ["Gold", "Silver", "Platinum", "Bronze"]}),
            ("travel style valid", "allowed_values", "preferred_travel_style",
             {"values": ["Cultural", "Food", "Luxury", "City", "Adventure"]}),
            ("average trip budget non-negative", "value_range", "average_trip_budget", {"min": 0}),
            ("customer_id present", "not_null", "customer_id", None),
            ("email present", "not_null", "email", None),
            ("first_name present", "not_null", "first_name", None),
            ("last_name present", "not_null", "last_name", None),
        ],
    },
]


def seed_dataset(db, name, file_name, rules):
    if db.query(Dataset).filter(Dataset.name == name).first():
        print(f"{name!r} already exists; skipping.")
        return

    dataset = Dataset(name=name, file_name=file_name)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    db.add_all(
        ValidationRule(
            dataset_id=dataset.id,
            name=rule_name,
            rule_type=rule_type,
            column_name=column_name,
            params=params,
        )
        for rule_name, rule_type, column_name, params in rules
    )
    db.commit()
    print(f"Seeded {name!r} (id={dataset.id}) with {len(rules)} rules.")


def seed_all(db):
    for dataset in DATASETS:
        seed_dataset(db, dataset["name"], dataset["file_name"], dataset["rules"])


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
