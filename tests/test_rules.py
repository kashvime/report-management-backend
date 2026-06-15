"""Tests for the validation rule checkers in app.services.rules.

Each checker takes (rows, column, params) and returns a list of RuleFailure,
one per failed row. 
"""

from app.models.validation_rule import ValidationRule
from app.services.rules import (
    check_not_null,
    check_unique,
    check_value_range,
    check_allowed_values,
    check_not_future_date,
    check_column_gte,
    check_must_be_blank,
    check_date_lte_column,
    check_regex_match,
    matches_when,
)
from app.services.validation_engine import evaluate_rule


def test_not_null_flags_blank_values():
    rows = [{"claim_id": "A1"}, {"claim_id": ""}, {"claim_id": "  "}]
    failures = check_not_null(rows, "claim_id", None)
    assert [f.row_number for f in failures] == [3, 4]


def test_unique_flags_only_duplicates():
    rows = [{"claim_id": "A1"}, {"claim_id": "A2"}, {"claim_id": "A1"}]
    failures = check_unique(rows, "claim_id", None)
    assert [f.row_number for f in failures] == [4]


def test_value_range_flags_negatives_and_non_numbers():
    rows = [{"billed_amount": "304"}, {"billed_amount": "-1"}, {"billed_amount": "x"}]
    failures = check_value_range(rows, "billed_amount", {"min": 0})
    assert [f.row_number for f in failures] == [3, 4]


def test_allowed_values_flags_disallowed_options():
    rows = [{"follow_up_required": "Yes"}, {"follow_up_required": "No"}, {"follow_up_required": "Yeah"}]
    failures = check_allowed_values(rows, "follow_up_required", {"values": ["Yes", "No"]})
    assert [f.row_number for f in failures] == [4]


def test_not_future_date_flags_future_and_invalid_dates():
    rows = [{"date_of_service": "08/07/2024"}, {"date_of_service": "12/31/2099"}, {"date_of_service": "nope"}]
    failures = check_not_future_date(rows, "date_of_service", None)
    assert [f.row_number for f in failures] == [3, 4]


def test_column_gte_flags_when_value_is_below_other_column():
    rows = [
        {"billed_amount": "304", "allowed_amount": "218"},  # 304 >= 218, ok
        {"billed_amount": "100", "allowed_amount": "218"},  # 100 < 218, fail
    ]
    failures = check_column_gte(rows, "billed_amount", {"other": "allowed_amount"})
    assert [f.row_number for f in failures] == [3]


def test_must_be_blank_flags_non_blank_values():
    rows = [{"closed_date": ""}, {"closed_date": "2024-01-01"}, {"closed_date": "  "}]
    failures = check_must_be_blank(rows, "closed_date", None)
    assert [f.row_number for f in failures] == [3]


def test_date_lte_column_flags_when_left_is_after_right():
    rows = [
        {"open_date": "2023-01-01", "closed_date": "2023-06-01"},  # open before close, ok
        {"open_date": "2024-01-01", "closed_date": "2023-01-01"},  # open after close, fail
        {"open_date": "2023-01-01", "closed_date": ""},            # close blank, skipped
    ]
    failures = check_date_lte_column(rows, "open_date", {"other": "closed_date", "format": "%Y-%m-%d"})
    assert [f.row_number for f in failures] == [3]


def test_regex_match_flags_values_not_matching_pattern():
    email_pattern = r"[^@\s]+@[^@\s]+\.[^@\s]+"
    rows = [
        {"email": "emma.johnson@email.com"},  # valid
        {"email": "no-at-sign.com"},          # missing @ -> fail
        {"email": "bad@@email.com"},          # double @ -> fail
        {"email": ""},                        # blank -> skipped (not_null's job)
    ]
    failures = check_regex_match(rows, "email", {"pattern": email_pattern})
    assert [f.row_number for f in failures] == [3, 4]


def test_matches_when_supports_equals_and_in():
    assert matches_when({"status": "Closed"}, {"column": "status", "equals": "Closed"})
    assert not matches_when({"status": "Open"}, {"column": "status", "equals": "Closed"})
    assert matches_when({"account_type": "Checking"}, {"column": "account_type", "in": ["Checking", "Savings"]})
    assert not matches_when({"account_type": "Credit"}, {"column": "account_type", "in": ["Checking", "Savings"]})


def test_evaluate_rule_applies_when_condition():
    # "closed_date must be present, but only when status is Closed"
    rows = [
        {"status": "Closed", "closed_date": ""},  # closed but no date -> fail
        {"status": "Open", "closed_date": ""},     # open, no date -> excluded by `when`
    ]
    header = ["status", "closed_date"]
    rule = ValidationRule(
        name="closed_date present when closed",
        rule_type="not_null",
        column_name="closed_date",
        params={"when": {"column": "status", "equals": "Closed"}},
    )
    failures = evaluate_rule(rule, rows, header)
    assert [f.row_number for f in failures] == [2]
