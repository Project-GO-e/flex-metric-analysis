
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class FlexMetrics(Base):
    __tablename__ = "flex_metrics"

    id: Mapped[str] = mapped_column(primary_key=True)
    cong_start: Mapped[datetime] = Column(DateTime)
    cong_duration: Mapped[int]
    asset_type: Mapped[str]
    area: Mapped[str]
    baseline: Mapped[Optional[str]]
    flex_metric: Mapped[Optional[str]]
    baseline_non_zero: Mapped[Optional[str]]

