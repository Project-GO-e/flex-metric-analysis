
import pickle
from datetime import time
from typing import List

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from db.data_not_found_exception import DataNotFoundException
from db.models import FlexDevices
from experiment.experiment import Experiment
from experiment.experiment_container import ExperimentContainer
from experiment.experiment_description import DeviceType


class FlexDevicesDao():

    @classmethod
    def to_db_object(cls, exp: Experiment) -> FlexDevices:
        baseline = pickle.dumps(exp.get_baseline_profiles().mean(axis=1).to_list())
        flex_metric = pickle.dumps(exp.get_weighted_mean_flex_metrics().to_list())
        return FlexDevices(id=exp.exp_des.name, 
                            cong_start=exp.exp_des.congestion_start.time(),
                            cong_duration=exp.exp_des.congestion_duration,
                            asset_type=exp.exp_des.device_type,
                            group=exp.exp_des.group,
                            typical_day=exp.exp_des.typical_day,
                            baseline=baseline,
                            flex_metric=flex_metric)

    
    def __init__(self, session: Session) -> None:
        self.session = session


    def save_container(self, container: ExperimentContainer):
        for e in container.exp.values():
            exp = self.session.get(FlexDevices, e.exp_des.name)
            if exp:
                self.session.merge(FlexDevicesDao.to_db_object(e))
            else: 
                self.session.add(FlexDevicesDao.to_db_object(e))
        self.session.commit()
    

    def save(self, exp: Experiment):
        exp_db = self.session.get(FlexDevices, exp.exp_des.name)
        if exp_db:
            self.session.merge(FlexDevicesDao.to_db_object(exp))
        else: 
            self.session.add(FlexDevicesDao.to_db_object(exp))
        self.session.commit()


    def get_typical_days(self, device_type: DeviceType) -> List[str]:
        stmt = select(FlexDevices.typical_day).where(FlexDevices.asset_type.is_(device_type)).distinct()
        return self.session.scalars(stmt).all()
    
    
    def get_congestion_start(self) -> List[time]:
        stmt = select(FlexDevices.cong_start).distinct()
        return self.session.scalars(stmt).all()
    

    def get_congestion_duration(self, cong_start: time) -> List[int]:
        stmt = select(FlexDevices.cong_duration).where(FlexDevices.cong_start.is_(cong_start)).distinct()
        return self.session.scalars(stmt).all()
    
    
    def get_groups_for_device_type(self: time, device_type: DeviceType) -> List[int]:
        stmt = select(FlexDevices.group).where(FlexDevices.asset_type.is_(device_type)).distinct()
        return self.session.scalars(stmt).all()
    

    def get_flex_metrics(self, asset_type: DeviceType, cong_start: time, cong_dur: int, group: str, typical_day: str) -> List[float]:
        stmt = select(FlexDevices.flex_metric)\
                    .filter(FlexDevices.asset_type.is_(asset_type))\
                    .filter(FlexDevices.cong_start.is_(cong_start))\
                    .filter(FlexDevices.cong_duration.is_(cong_dur))\
                    .filter(FlexDevices.group.is_(group))\
                    .filter(FlexDevices.typical_day.is_(typical_day))
        res = self.session.scalar(stmt)
        if res:
            return pickle.loads(res)
        else:
            raise DataNotFoundException(f"No flex metrics found for {str(asset_type)}, congestion start '{cong_start}', congestion duration '{cong_dur}', group '{group}', typical day '{typical_day}'.")


    def get_baseline(self, asset_type: DeviceType, cong_start: time, cong_dur: int, group: str, typical_day: str) -> List[float]:
        stmt = select(FlexDevices.baseline)\
                    .filter(FlexDevices.asset_type.is_(asset_type))\
                    .filter(FlexDevices.cong_start.is_(cong_start))\
                    .filter(FlexDevices.cong_duration.is_(cong_dur))\
                    .filter(FlexDevices.group.is_(group))\
                    .filter(FlexDevices.typical_day.is_(typical_day))
        res = self.session.scalar(stmt)
        if res:
            return pickle.loads(res)
        else:
            raise DataNotFoundException(f"No baseline found for {asset_type}, congestion start '{cong_start}', congestion duration '{cong_dur}', group '{group}', typical day '{typical_day}'..")
        
    
    def delete_device_type(self, asset_type: DeviceType):
        stmt = delete(FlexDevices).where(FlexDevices.asset_type.is_(asset_type))
        self.session.execute(stmt)
        self.session.commit()