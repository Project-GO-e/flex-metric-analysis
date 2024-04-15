
from datetime import time

from sqlalchemy import BLOB, Column, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from db.type_decorators import MappedEnum
from experiment.experiment_description import DeviceType

'''
Python models of the SQL database tables.
'''

class Base(DeclarativeBase):
    pass


class FlexMetric(Base):
    '''
    Python model of the database table that contians flex metrics.
    '''
    __tablename__ = "flexible_devices"

    id: Mapped[str] = mapped_column(primary_key=True)
    cong_start: Mapped[time] = Column(Time)
    cong_duration: Mapped[int]
    device_type: Mapped[DeviceType] = Column(MappedEnum(DeviceType))
    typical_day: Mapped[str]
    group: Mapped[str]
    flex_metric: Mapped[BLOB] = Column(BLOB)

    def __repr__(self) -> str:
        return f"{self.asset_type}: cong_start: {self.cong_start}, cong_dur: {self.cong_duration})"


class Baseline(Base):
    '''
    Python model of the database table that contians baselines.
    '''
    __tablename__ = "baseline"

    id: Mapped[str] = mapped_column(primary_key=True)
    device_type: Mapped[DeviceType] = Column(MappedEnum(DeviceType))
    typical_day: Mapped[str]
    group: Mapped[str]
    mean_power: Mapped[BLOB] = Column(BLOB)
    p95: Mapped[BLOB] = Column(BLOB)
