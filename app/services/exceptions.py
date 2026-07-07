"""Validation engine exceptions."""


class ValidationEngineError(Exception):
    """Base error for validation engine failures."""


class DatasetNotFoundError(ValidationEngineError):
    """Raised when the requested dataset does not exist."""


class DatasetNotRunnableError(ValidationEngineError):
    """Raised when a dataset has no readable CSV to validate."""


class RuleConfigError(ValidationEngineError):
    """Raised when an active rule is misconfigured."""


class InvalidUploadError(Exception):
    """Raised when an uploaded file is not an acceptable CSV."""