
from datetime import time

from sqlalchemy import BLOB, Column, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FlexMetrics(Base):
    __tablename__ = "flex_metrics"

    id: Mapped[str] = mapped_column(primary_key=True)
    cong_start: Mapped[time] = Column(Time)
    cong_duration: Mapped[int]
    asset_type: Mapped[str]
    group: Mapped[str]
    typical_day: Mapped[str]
    baseline: Mapped[BLOB] = Column(BLOB)
    flex_metric: Mapped[BLOB] = Column(BLOB)

    def __repr__(self) -> str:
        return f"{self.asset_type}: cong_start: {self.cong_start}, cong_dur: {self.cong_duration})"


class NonFlexDevices(Base):
    __tablename__ = "non_flex_devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_type: Mapped[str]
    typical_day: Mapped[str]
    mean_power: Mapped[BLOB] = Column(BLOB)
