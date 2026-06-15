from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey
from datetime import datetime
from app.db.base import Base
from app.utils import utc_now

class ValidationError(Base):
    """
    ValidationError represents a single validation error that occurred during a validation run.
    
    Errors belong to runs and are deleted with them. If a referenced
    validation rule is deleted, rule_id is set to NULL so historical
    validation results are preserved.
    
    Errors are immutable once recorded, so no updated_at is tracked.

    """
    
    __tablename__ = "validation_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
   
    run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("validation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("validation_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    rule_type_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    column_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    run: Mapped["ValidationRun"] = relationship(
        "ValidationRun",
        back_populates="errors")
    
    rule: Mapped["ValidationRule | None"] = relationship(
        "ValidationRule",
        back_populates="errors"
    )

    def __repr__(self) -> str:
        return f"<ValidationError id={self.id} run_id={self.run_id} rule_id={self.rule_id} column_name={self.column_name!r}>"