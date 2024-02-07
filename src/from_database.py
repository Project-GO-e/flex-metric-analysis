
from datetime import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.flex_metrics_dao import FlexMetricsDao
from experiment_description import DeviceType

engine = create_engine("sqlite:///test.db", echo=True)


with Session(engine) as session:
    doa = FlexMetricsDao(session)
    m = doa.get_flex_metrics(DeviceType.HP, time(10), 8, 'tussen+2012+family', 'winterday')
    print(m)
    m = doa.get_flex_metrics(DeviceType.EV, time(10), 8, '9561', 'workday')
    print(m)
