from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Text
from datetime import datetime
from app.db.base import Base
from app.utils import utc_now

class Dataset(Base): 
    """
    Dataset is the root entity of the system that is being checked for quality. 

    A dataset owns its validation rules and validation runs. Deleting
    a dataset cascades deletion to its dependent entities.
    
    """
    __tablename__ = "datasets" 

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
  
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # One dataset can have many rules
    rules: Mapped[list["ValidationRule"]] = relationship(
        "ValidationRule", 
        back_populates="dataset", 
        cascade="all, delete-orphan") 
    
    # One dataset can have many runs
    runs: Mapped[list["ValidationRun"]] = relationship(
        "ValidationRun", 
        back_populates="dataset", 
        cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Dataset id={self.id} name={self.name!r}>"

