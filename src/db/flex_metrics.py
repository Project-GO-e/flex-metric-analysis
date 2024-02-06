
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class FlexMetrics(Base):
    __tablename__ = "flex_metrics"

    id: Mapped[str] = mapped_column(primary_key=True)
    cong_start: Mapped[datetime] = Column(DateTime)
    cong_duration: Mapped[int]
    asset_type: Mapped[str]
    group: Mapped[str]
    typical_day: Mapped[Optional[str]]
    baseline: Mapped[Optional[str]]
    flex_metric: Mapped[Optional[str]]

    def __repr__(self) -> str:
        return f"{self.asset_type}: cong_start: {self.cong_start}, cong_dur: {self.cong_duration})"
