
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.flex_metrics_dao import FlexMetricsDao
from experiment_description import DeviceType

engine = create_engine("sqlite:///test.db", echo=True)


with Session(engine) as session:
    doa = FlexMetricsDao(session)
    m = doa.get_flex_metrics(DeviceType.HP, datetime(2020,1,15,10), 8, 'tussen+2012+family', 'winterday')
    print(m)
    m = doa.get_flex_metrics(DeviceType.EV, datetime(2020,6,3,10), 8, '2515', 'workday')
    print(m)
