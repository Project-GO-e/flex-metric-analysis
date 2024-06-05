
from datetime import time

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.baselines_dao import BaselineDao
from db.flex_devices_dao import FlexDevicesDao
from experiment.experiment_description import DeviceType
from flex_metric_config import DEFAULT_PV_GROUP

engine = create_engine("sqlite:///test.db", echo=True)


with Session(engine) as session:
    # doa = FlexDevicesDao(session)
    # m = doa.get_flex_metrics(DeviceType.HP, time(7), 4, '2_1kap+1975-1991+family', 'January')
    # print(m)
    # m = doa.get_flex_metrics(DeviceType.EV, time(0,45), 16, '6651', 'workday')
    # print(m)
    dao = BaselineDao(session)
    group=DEFAULT_PV_GROUP
    months = dao.get_typical_days(device_type=DeviceType.PV, group=group)
    profiles = pd.DataFrame(index=pd.RangeIndex(start=0, stop=96))
    for m in months:
        p: pd.DataFrame = dao.get_baseline_mean(device_type=DeviceType.PV, typical_day=m, group=group)
        profiles[m] = p.reset_index(drop=True)

    profiles.to_csv("pvgis-interpolated-tz-shift-eff.csv", sep=';')
