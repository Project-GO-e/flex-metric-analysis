

import pickle
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from db.models import Baseline
from experiment.device_type import DeviceType
from experiment.experiment import Experiment


class BaselineDao():

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_experiment(self, experiment: Experiment) -> None:
        desc = experiment.exp_des
        self.save(desc.device_type, desc.typical_day, desc.group, experiment.get_baseline_profiles().mean(axis=1))
    
    def save(self, device_type: DeviceType, typical_day: str, group: str, mean_power) -> None:
        assert len(mean_power) == 96, "Mean power array should contain 96 elements"
        power = pickle.dumps(mean_power)
        exp_id = f"{device_type}+{group}+{typical_day}"
        if self.session.get(Baseline, exp_id):
            self.session.merge(Baseline(id=exp_id, device_type=device_type, typical_day=typical_day, group=group, mean_power=power))
        else:
            self.session.add(Baseline(id=exp_id, device_type=device_type, typical_day=typical_day, group=group, mean_power=power))
        self.session.commit()

    def get_device_types(self) -> List[DeviceType]:
        stmt = select(Baseline.device_type).distinct()
        return self.session.scalars(stmt).all()

    def get_typical_days(self, device_type: DeviceType = None, group: str = None) -> List[str]:
        stmt = select(Baseline.typical_day)
        if device_type:
            stmt = stmt.where(Baseline.device_type.is_(device_type))
        if group:
            stmt = stmt.where(Baseline.group == group)
        stmt = stmt.distinct()
        return self.session.scalars(stmt).all()

    def get_groups(self, device_type: DeviceType = None, typical_day: str = None) -> List[int]:
        stmt = select(Baseline.group)
        if device_type:
            stmt = stmt.where(Baseline.device_type.is_(device_type))
        if typical_day:
            stmt = stmt.where(Baseline.typical_day == typical_day)
        stmt = stmt.distinct()
        return self.session.scalars(stmt).all()

    def get_baseline_mean(self, device_type: DeviceType, typical_day: str, group: str) -> List[float]:
        stmt = select(Baseline.mean_power)\
                    .filter(Baseline.device_type.is_(device_type))\
                    .filter(Baseline.typical_day.is_(typical_day))\
                    .filter(Baseline.group.is_(group))
        baseline = self.session.scalar(stmt)
        return pickle.loads(baseline)

    def get_baseline_p95(self, device_type: DeviceType, typical_day: str, group: str) -> List[float]:
        stmt = select(Baseline.p95)\
                    .filter(Baseline.device_type.is_(device_type))\
                    .filter(Baseline.typical_day.is_(typical_day))\
                    .filter(Baseline.group.is_(group))
        baseline = self.session.scalar(stmt)
        return pickle.loads(baseline)
        
    def delete_device_type(self, device_type: DeviceType):
        stmt = delete(Baseline).where(Baseline.device_type.is_(device_type))
        self.session.execute(stmt)
        self.session.commit()