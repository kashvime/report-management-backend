"""Pure validation rules."""

import re
from dataclasses import dataclass
from datetime import date, datetime

from app.schemas.common import RuleType
from app.services.exceptions import RuleConfigError

@dataclass
class RuleFailure:
    """One validation failure. row_number matches the CSV line number."""
    row_number: int
    message: str

def matches_when(row, when) -> bool:
    """Whether a row satisfies an optional 'when' condition.

    Lets any rule apply only to some rows, e.g.:
        {"column": "status", "equals": "Closed"}
        {"column": "account_type", "in": ["Checking", "Savings"]}
    """
    value = row.get(when["column"])
    if "equals" in when:
        return value == when["equals"]
    if "in" in when:
        return value in when["in"]
    raise RuleConfigError("'when' condition needs 'equals' or 'in'")



def is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def check_not_null(rows, column, params):
    return [
        RuleFailure(row_number, f"Column '{column}' must not be empty")
        for row_number, row in enumerate(rows, start=2)
        if is_blank(row.get(column))
    ]
    
def check_must_be_blank(rows, column, params):
    return [
        RuleFailure(row_number, f"Column '{column}' must be blank")
        for row_number, row in enumerate(rows, start=2)
        if not is_blank(row.get(column))
    ]

def check_unique(rows, column, params):
    seen = {}
    failures = []

    for row_number, row in enumerate(rows, start=2):
        value = row.get(column)

        if is_blank(value):
            continue # Let check_not_null handle null values

        if value in seen:
            failures.append(
                RuleFailure(
                    row_number,
                    (
                        f"Column '{column}' must be unique; "
                        f"value {value!r} already appears on row {seen[value]}"
                    ),
                )
            )
        else:
            seen[value] = row_number

    return failures

def check_value_range(rows, column, params):
    minimum = params.get("min") if params else None
    maximum = params.get("max") if params else None
    if minimum is None and maximum is None:
        raise RuleConfigError("value_range rule needs 'min' or 'max' in params")
    
    failures = []
    for row_number, row in enumerate(rows, start=2):
        value = row.get(column)
        if is_blank(value):
            continue # Let check_not_null handle null values
        try:
            number = float(value)
        except ValueError:
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' value {value!r} is not a valid number"
                )
            )
            continue
        
        if minimum is not None and number < minimum:
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' value {number} is less than minimum {minimum}"
                )
            )
        elif maximum is not None and number > maximum:
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' value {number} is greater than maximum {maximum}"
                )
            )
    return failures

def check_allowed_values(rows, column, params):
    values = params.get("values") if params else None
    if not values:
        raise RuleConfigError("allowed_values rule needs 'values' list in params")
    allowed = {str(v) for v in values}
    
    failures =[]
    for row_number, row in enumerate(rows, start=2):
        value = row.get(column)
        if is_blank(value):
            continue
        if value not in allowed:
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' value {value!r} is not a valid option; allowed values are {allowed}"
                )
            )
    return failures


def check_not_future_date(rows, column, params):
    date_format = params.get("format") if params else None
    date_format = date_format or "%m/%d/%Y"
    today = date.today()

    failures = []
    for row_number, row in enumerate(rows, start=2):
        value = row.get(column)
        if is_blank(value):
            continue  # Let check_not_null handle null values
        try:
            parsed = datetime.strptime(value, date_format).date()
        except ValueError:
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' value {value!r} is not a valid date (expected format {date_format})"
                )
            )
            continue
        if parsed > today:
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' date {value} is in the future"
                )
            )
    return failures

def check_column_gte(rows, column, params):
    other = params.get("other") if params else None
    if not other:
        raise RuleConfigError("column_gte rule needs an 'other' column name in params")
    if rows and other not in rows[0]:
        raise RuleConfigError(f"column_gte rule references unknown column {other!r}")

    failures = []
    for row_number, row in enumerate(rows, start=2):
        value = row.get(column)
        other_value = row.get(other)
        if is_blank(value) or is_blank(other_value):
            continue  # Let check_not_null handle null values
        try:
            number = float(value)
            other_number = float(other_value)
        except ValueError:
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' or '{other}' is not a valid number"
                )
            )
            continue
        if number < other_number:
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' value {number} must be >= column '{other}' value {other_number}"
                )
            )
    return failures


def check_date_lte_column(rows, column, params):
    other = params.get("other") if params else None
    if not other:
        raise RuleConfigError("date_lte_column rule needs an 'other' column name in params")
    date_format = (params.get("format") if params else None) or "%m/%d/%Y"
    if rows and other not in rows[0]:
        raise RuleConfigError(f"date_lte_column rule references unknown column {other!r}")

    failures = []
    for row_number, row in enumerate(rows, start=2):
        value = row.get(column)
        other_value = row.get(other)
        if is_blank(value) or is_blank(other_value):
            continue  # Only compare when both dates are present
        try:
            left = datetime.strptime(value, date_format).date()
            right = datetime.strptime(other_value, date_format).date()
        except ValueError:
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' or '{other}' is not a valid date (expected format {date_format})"
                )
            )
            continue
        if left > right:
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' date {value} must be on or before column '{other}' date {other_value}"
                )
            )
    return failures

def check_regex_match(rows, column, params):
    pattern = params.get("pattern") if params else None
    if not pattern:
        raise RuleConfigError("regex_match rule needs a 'pattern' in params")
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise RuleConfigError(f"regex_match rule has an invalid pattern: {exc}")

    failures = []
    for row_number, row in enumerate(rows, start=2):
        value = row.get(column)
        if is_blank(value):
            continue  # Let check_not_null handle null values
        if not compiled.fullmatch(value):
            failures.append(
                RuleFailure(
                    row_number,
                    f"Column '{column}' value {value!r} does not match the required format"
                )
            )
    return failures

# Maps a rule type to its checker. Add a rule type by adding an enum member
# (schemas/common.py), a checker above, and one entry here.
CHECKERS = {
    RuleType.NOT_NULL: check_not_null,
    RuleType.UNIQUE: check_unique,
    RuleType.VALUE_RANGE: check_value_range,
    RuleType.ALLOWED_VALUES: check_allowed_values,
    RuleType.NOT_FUTURE_DATE: check_not_future_date,
    RuleType.COLUMN_GREATER_THAN_OR_EQUAL: check_column_gte,
    RuleType.DATE_LESS_THAN_OR_EQUAL: check_date_lte_column,
    RuleType.MUST_BE_BLANK: check_must_be_blank,
    RuleType.REGEX_MATCH: check_regex_match,
}
