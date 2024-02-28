

import pickle
from datetime import date, datetime, time, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import NonFlexDevices


class NonFlexDevicesDao():

    def __init__(self, session: Session) -> None:
        self.session = session

    
    def save(self, asset_type: str, typical_day: str, mean_power) -> None:
        power = pickle.dumps(mean_power)
        exp_id = f"{asset_type}+{typical_day}"
        exp_db = self.session.get(NonFlexDevices, exp_id)
        if exp_db:
            self.session.merge(NonFlexDevices(id=exp_id, asset_type=asset_type, typical_day=typical_day, mean_power=power))
        else:
            self.session.add(NonFlexDevices(id=exp_id, asset_type=asset_type, typical_day=typical_day, mean_power=power))
        self.session.commit()


    def get_baseline(self, asset_type: str, cong_start: time, cong_dur: int, typical_day: str) -> List[float]:
        stmt = select(NonFlexDevices.mean_power)\
                    .filter(NonFlexDevices.asset_type.is_(asset_type))\
                    .filter(NonFlexDevices.typical_day.is_(typical_day))
        cong_start = datetime.combine(date(2020,1,1), time(10,0))
        cong_start_idx = int((cong_start - datetime(2020,1,1)) / timedelta(minutes=15))
        baseline = self.session.scalar(stmt)
        return pickle.loads(baseline)[cong_start_idx : cong_start_idx + cong_dur]
        