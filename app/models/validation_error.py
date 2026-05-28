from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey
from datetime import datetime, timezone
from app.db.base import Base


class ValidationError(Base):
    __tablename__ = "validation_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("validation_runs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("validation_rules.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    column_name: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    run: Mapped["ValidationRun"] = relationship("ValidationRun", back_populates="errors")
    rule: Mapped["ValidationRule"] = relationship("ValidationRule", back_populates="errors")

    def __repr__(self) -> str:
        return f"<ValidationError id={self.id} run_id={self.run_id} rule_id={self.rule_id} column_name={self.column_name!r}>"