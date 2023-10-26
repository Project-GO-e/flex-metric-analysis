

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd

from experiment import Experiment
from experiment_description import DeviceType
from experiment_filter import ExperimentFilter


@dataclass
class Metadata():
    rows: str
    colums: str
    flex_window: int
    area_ids: List[str]
    device_type: DeviceType
    

class ExperimentContainer():

    def __init__(self, experiments : Dict[str, Experiment]) -> None:
        self.exp = experiments


    def get_mean_flex_for_duration(self, device_type: DeviceType, area_ids: List[str], flex_window: int, cong_start: datetime) -> (pd.DataFrame, Metadata):
        exp_filter = ExperimentFilter().with_areas(area_ids).with_flex_window_duration(flex_window).with_cong_start(cong_start)
        data :Dict[datetime, List[float] ] = {}
        max_length = 0
        for exp in self.exp.values():
            if exp_filter.passFilter(exp.exp_des):
                data[exp.get_congestion_duration()] = exp.get_weighted_mean_flex_metrics()
                max_length = exp.get_congestion_duration() if exp.get_congestion_duration() > max_length else max_length
        for exp in data:
            data[exp] += (max_length - len(data[exp])) * [np.NaN]
        data = dict(sorted(data.items()))
        return pd.DataFrame(data), Metadata("PTU", "Duration (#PTU)", area_ids, flex_window, device_type)


    def get_mean_flex_for_congestion_start(self, device_type: DeviceType, area_ids: List[str], flex_window: int, cong_duration: int) -> (pd.DataFrame, Metadata):
        exp_filter = ExperimentFilter().with_areas(area_ids).with_flex_window_duration(flex_window).with_cong_duration(cong_duration)
        data :Dict[datetime, List[float] ] = {}
        for exp in self.exp.values():
            if exp_filter.passFilter(exp.exp_des):
                data[exp.get_congestion_start()] =  exp.get_weighted_mean_flex_metrics()
        data = dict(sorted(data.items()))
        return pd.DataFrame(data), Metadata("PTU", "Congestion start times", area_ids, flex_window, device_type)
    

    def get_mean_flex(self, device_tpe: DeviceType, area_id: List[str], flex_window: int) -> (pd.DataFrame, Metadata):
        pass