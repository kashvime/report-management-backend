"""Shared schema building blocks reused across every resource. """

from datetime import datetime 
from enum import StrEnum
from pydantic import BaseModel, ConfigDict


class RuleType(StrEnum):
    NOT_NULL = "not_null"
    UNIQUE = "unique"
    VALUE_RANGE = "value_range"
    ALLOWED_VALUES = "allowed_values"
    NOT_FUTURE_DATE = "not_future_date"
    COLUMN_GREATER_THAN_OR_EQUAL = "column_gte"
    DATE_LESS_THAN_OR_EQUAL = "date_lte_column"
    MUST_BE_BLANK = "must_be_blank"
    REGEX_MATCH = "regex_match"


class RunStatus(StrEnum):
    """
    Lifecycle states of a validation run.

    ``pending``   -- created, not yet started.
    ``running``   -- engine is executing rules.
    ``completed`` -- finished; totals are populated (errors may be > 0).
    ``failed``    -- aborted before completion (missing file, bad rule config).
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed" 
    FAILED = "failed" 

class ORMModel(BaseModel):
    """Base for any schema read out of a SQLAlchemy model. """ 
    model_config = ConfigDict(from_attributes=True)


class TimeStampRead(ORMModel):
    created_at: datetime
    updated_at: datetime