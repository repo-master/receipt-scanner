from ..db import Base

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Identity, Integer, String, Enum, select
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import func


class ScannerBase(Base):
    __abstract__ = True
    # __table_args__ = {"schema": "receipt_scanner"}


class Receipt(ScannerBase):
    __tablename__ = "receipt_history"
    receipt_id: Mapped[int] = Column(
        "receipt_id", Integer, Identity(start=1), primary_key=True
    )
    time_created: Mapped[datetime] = Column(
        "time_created", DateTime(timezone=True), server_default=func.now()
    )
    time_updated: Mapped[datetime] = Column(
        "time_updated", DateTime(timezone=True), onupdate=func.now()
    )
    summary: Mapped[dict] = Column("summary", JSON, default={})
    item_listing: Mapped[list] = Column("item_listing", JSON, default=[])


__all__ = ["Receipt"]