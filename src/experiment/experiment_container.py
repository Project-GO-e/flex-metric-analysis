from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .experiment import Experiment
from .experiment_filter import ExperimentFilter


class ExperimentContainer():

    def __init__(self, experiments : Dict[str, Experiment]) -> None:
        self.exp = experiments


    def filter(self, filter: ExperimentFilter) -> ExperimentContainer:
        filtered_experiments = {k: v for k, v in self.exp.items() if filter.pass_filter(v.exp_des)}
        return ExperimentContainer(filtered_experiments)           


    def get_mean_flex_per_duration(self) -> Dict[int, List[float]]:
        data: Dict[int, List[float] ] = {}
        for exp in self.exp.values():
            flex_metrics = data.setdefault(exp.get_congestion_duration(), [])
            flex_metrics.extend(exp.get_weighted_mean_flex_metrics().to_numpy())
        return dict(sorted(data.items()))
    

    def get_mean_flex_per_duration_per_ptu(self) -> Dict[int, Dict[int, List[float]]]:
        data: Dict[int, Dict[int, float] ] = {}
        for exp in self.exp.values():
            flex_metrics_per_duration = data.setdefault(exp.get_congestion_duration(), {})
            for ptu in range(exp.get_congestion_duration()):
                flex_metrics = flex_metrics_per_duration.setdefault(ptu, [])
                flex_metrics.append(exp.get_weighted_mean_flex_metric(ptu))
        return dict(sorted(data.items()))


    def get_mean_flex_per_congestion_start(self) -> Dict[datetime, List[float]]:
        data: Dict[datetime, List[float] ] = {}
        for exp in self.exp.values():
            flex_metrics = data.setdefault(exp.get_congestion_start(), [])
            flex_metrics.extend(exp.get_weighted_mean_flex_metrics().to_numpy())
        return dict(sorted(data.items()))
    

    def get_mean_flex_per_congestion_start_per_ptu(self) -> Dict[datetime, Dict[int, List[float]]]:
        data: Dict[datetime, Dict[int, List[float]]] = {}
        for exp in self.exp.values():
            flex_metrics_per_cong_start = data.setdefault(exp.get_congestion_start(), {})
            for ptu in range(exp.get_congestion_duration()):
                flex_metrics = flex_metrics_per_cong_start.setdefault(ptu, [])
                flex_metrics.append(exp.get_weighted_mean_flex_metric(ptu))
        return dict(sorted(data.items()))
    
    
    def get_mean_flex_per_group(self) -> Dict[str, List[float]]:
        data: Dict[str, List[float] ] = {}
        for exp in self.exp.values():
            flex_metrics = data.setdefault(exp.exp_des.group, [])
            flex_metrics.extend(exp.get_weighted_mean_flex_metrics().to_numpy())
        return data
    

    def get_mean_flex(self) -> List[float]:
        data: List[float] = []
        for exp in self.exp.values():
            data.extend(exp.get_weighted_mean_flex_metrics().to_numpy())
        return data
    

    def get_mean_flex_for_time_of_day(self) -> Dict[datetime, List[float]]:
        data : Dict[datetime, List[float]] = {}
        for exp in self.exp.values():
            metric_per_ptu = exp.get_weighted_mean_flex_metrics().to_numpy()
            for i in range(exp.get_congestion_duration()):
                l = data.setdefault(exp.get_congestion_start() + exp.ptu_duration * i, [])
                l.append(metric_per_ptu[i])
        return data
    
    
    def get_groups(self) -> List[str]:
        return list((set(map(lambda e: e.exp_des.group, self.exp.values()))))