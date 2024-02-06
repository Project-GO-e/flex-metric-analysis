
import pickle
from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.flex_metrics import FlexMetrics
from experiment import Experiment
from experiment_container import ExperimentContainer
from experiment_description import DeviceType


class FlexMetricsDao():

    @classmethod
    def to_db_object(cls, exp: Experiment) -> FlexMetrics:
        baseline = pickle.dumps(exp.get_baseline_profiles().mean(axis=1).to_list())
        flex_metric = pickle.dumps(exp.get_weighted_mean_flex_metrics().to_list())
        return FlexMetrics(id=exp.exp_des.name, 
                            cong_start=exp.exp_des.congestion_start,
                            cong_duration=exp.exp_des.congestion_duration,
                            asset_type=str(exp.exp_des.device_type),
                            group=exp.exp_des.group,
                            typical_day=exp.exp_des.typical_day,
                            baseline=baseline,
                            flex_metric=flex_metric)

    
    def __init__(self, session: Session) -> None:
        self.session = session


    def save_container(self, container: ExperimentContainer):
        for e in container.exp.values():
            self.session.add(FlexMetricsDao.to_db_object(e))
        self.session.commit()
    

    def save(self, exp: Experiment):
        self.session.add(FlexMetricsDao.to_db_object(exp))
        self.session.commit()


    def get_ev_typical_days(self) -> List[str]:
        stmt = select(FlexMetrics.typical_day).where(FlexMetrics.asset_type.is_('DeviceType.EV')).distinct()
        return self.session.scalars(stmt).all()
    
    
    def get_hp_typical_days(self) -> List[str]:
        stmt = select(FlexMetrics.typical_day).where(FlexMetrics.asset_type.is_('DeviceType.HP')).distinct()
        return self.session.scalars(stmt).all()


    def get_flex_metrics(self, asset_type: DeviceType, cong_start: datetime, cong_dur: int, group: str, typical_day: str) -> List[float]:
        stmt = select(FlexMetrics.flex_metric)\
                    .filter(FlexMetrics.asset_type.is_(str(asset_type)))\
                    .filter(FlexMetrics.cong_start.is_(cong_start))\
                    .filter(FlexMetrics.cong_duration.is_(cong_dur))\
                    .filter(FlexMetrics.group.is_(group))\
                    .filter(FlexMetrics.typical_day.is_(typical_day))
        return pickle.loads(self.session.scalar(stmt))
        