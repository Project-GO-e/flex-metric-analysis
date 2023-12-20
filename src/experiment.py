from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd

from db.flex_metrics import FlexMetrics
from experiment_description import ExperimentDescription


class Experiment:
    """
    Experiment class that contains data of baseline and shifted power profiles and calculates the flex metric.
    The expirement class only concerns data in the congestion period.
    """


    def __init__(self, baseline: pd.DataFrame, shifted: pd.DataFrame, experiment_description: ExperimentDescription) -> None:
        """
        Args:
            baseline: pandas dataframe with the baseline profiles of a experiment.
            shifted: pandas dataframe of a experiment's shifted profiles.
        """

        self.exp_des = experiment_description
        ptu_duration = baseline.index[1] - baseline.index[0]
        congestion_end = self.get_congestion_start() + (self.get_congestion_duration() - 1) * ptu_duration
        self.__baseline = baseline[self.get_congestion_start() : congestion_end]
        self.__shifted = shifted[self.get_congestion_start(): congestion_end]

        self.__baseline_wo_zeros: Dict[int, pd.Series] = {}
        self.__shifted_wo_zeros: Dict[int, pd.Series] = {}
        self.__flex_metrics: Dict[int, pd.Series] = {}
        self.__mean_weighted_flex_metric: Dict[int, np.float64] = {}


    def calc(self) -> None:
        for ptu_idx in range(self.get_congestion_duration()):
            mask = self.__baseline.iloc[ptu_idx] != 0.0
            baselines_wo_zeros = self.__baseline.iloc[ptu_idx][mask.values]
            shifted_wo_zeros = self.__shifted.iloc[ptu_idx][mask.values]
            self.__flex_metrics[ptu_idx] = (baselines_wo_zeros - shifted_wo_zeros) / baselines_wo_zeros
            self.__mean_weighted_flex_metric[ptu_idx] = (self.__flex_metrics[ptu_idx] * baselines_wo_zeros).mean()/baselines_wo_zeros.mean()                
            self.__baseline_wo_zeros[ptu_idx] = baselines_wo_zeros
            self.__shifted_wo_zeros[ptu_idx] = shifted_wo_zeros
            # flexpower = flex_metric * baseline_wo_zeros
            # weighted_flex_metric = (baseline_wo_zeros - shifted_wo_zeros) / baseline_wo_zeros.mean()
            # metric_variances_weighted = np.square(flex_metric - mean_weighted_flex_metric) * baseline_wo_zeros / baseline_wo_zeros.mean()
            # sd_weighted_flex_metric = np.sqrt(metric_variances_weighted.mean())


    def get_congestion_start(self) -> datetime:
        return self.exp_des.get_congestion_start()


    def get_congestion_duration(self) -> int:
        return self.exp_des.get_congestion_duration()
    

    def get_flexwindow_duration(self) -> int:
        return self.exp_des.get_flexwindow_duration()


    def get_congestion_zipcode(self) -> str:
        return self.exp_des.get_area()


    def get_flex_metric(self, ptu: int) -> pd.Series:
        if len(self.__flex_metrics) == 0: self.calc()
        return self.__flex_metrics[ptu]
    
    
    def get_weighted_mean_flex_metrics(self) -> List[float] :
        if len(self.__flex_metrics) == 0: self.calc()
        return list(self.__mean_weighted_flex_metric.values())
    

    def get_weighted_mean_flex_metric(self, ptu: int) -> float :
        if len(self.__flex_metrics) == 0: self.calc()
        return self.__mean_weighted_flex_metric[ptu]


    def get_baseline(self, ptu: int) -> pd.Series:
        """Return the baseline power for a PTU of all devices that are non-zero in the baseline"""
        if len(self.__baseline_wo_zeros) == 0: self.calc()
        return self.__baseline_wo_zeros[ptu]


    def get_baseline_profiles(self) -> pd.DataFrame:
        """Return the baseline power for all PTU of all devices"""
        if len(self.__baseline_wo_zeros) == 0: self.calc()
        return self.__baseline


    def get_shifted(self, ptu: int) -> pd.Series:
        """Return the power after flex optimalization of all devices that are non-zero in the baseline"""
        if len(self.__baseline_wo_zeros) == 0: self.calc()
        return self.__shifted_wo_zeros[ptu]
    

    def get_shifted_profiles(self) -> pd.DataFrame:
        """Return the baseline power for all PTU of all devices"""
        if len(self.__baseline_wo_zeros) == 0: self.calc()
        return self.__shifted


    def get_num_active_baseline_devices(self, ptu: int) -> int:
        if len(self.__baseline_wo_zeros) == 0: self.calc()
        return self.__baseline_wo_zeros[ptu].count()


    def to_db_object(self) -> FlexMetrics:
        baseline = ','.join(map(lambda x: str(x), self.__baseline.mean(axis=1)))
        flex_metric = ','.join(map(lambda x: str(x), self.get_weighted_mean_flex_metrics()))
        baseline_wo_zero_list = []
        for ptu in self.__baseline_wo_zeros:
            baseline_wo_zero_list.append(self.__baseline_wo_zeros[ptu].mean())
        
        baseline_wo_zero = ','.join(map(lambda x: str(x), baseline_wo_zero_list))
        return FlexMetrics(id=self.exp_des.name, 
                            cong_start=self.exp_des.congestion_start,
                            cong_duration=self.exp_des.congestion_duration,
                            asset_type=str(self.exp_des.device_type), 
                            area=self.exp_des.area, 
                            baseline=baseline,
                            flex_metric=flex_metric,
                            baseline_non_zero=baseline_wo_zero)