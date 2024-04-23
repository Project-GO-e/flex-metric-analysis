from datetime import datetime, timedelta

import pandas as pd

from .experiment_description import ExperimentDescription


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
        self.ptu_duration: timedelta = baseline.index[1] - baseline.index[0]
        congestion_end = self.exp_des.congestion_start + (self.exp_des.congestion_duration - 1) * self.ptu_duration
        self.__baseline = baseline

        self.__shifted = shifted[self.exp_des.congestion_start: congestion_end]
        mean_baseline = self.__baseline[self.exp_des.congestion_start : congestion_end].mean(axis=1)
        self.__mean_weighted_flex_metric: pd.Series = (mean_baseline - self.__shifted.mean(axis=1)) / mean_baseline


    def get_congestion_start(self) -> datetime:
        return self.exp_des.congestion_start


    def get_congestion_duration(self) -> int:
        return self.exp_des.congestion_duration
    

    def get_flexwindow_duration(self) -> int:
        return self.exp_des.flexwindow_duration


    def get_group(self) -> str:
        return self.exp_des.group
    
    
    def get_weighted_mean_flex_metrics(self) -> pd.Series:
        return self.__mean_weighted_flex_metric
    

    def get_weighted_mean_flex_metric(self, ptu: int) -> float :
        return self.__mean_weighted_flex_metric[self.exp_des.congestion_start + self.ptu_duration * ptu]


    def get_baseline_profiles(self) -> pd.DataFrame:
        """Return the baseline power for all PTU of all devices"""
        return self.__baseline

    def get_baseline(self, ptu: int) -> pd.Series:
        """Return the baseline power of all devices"""
        return self.__baseline.iloc[ptu]

    
    def get_shifted(self, ptu: int) -> pd.Series:
        """Return the power after flex optimalization of all devices"""
        return self.__shifted.iloc[ptu]
    

    def get_shifted_profiles(self) -> pd.DataFrame:
        """Return the baseline power for all PTU of all devices"""
        return self.__shifted


    def get_num_active_baseline_devices(self, ptu: int) -> int:
        mask = self.__baseline.iloc[ptu] != 0.0
        return self.__baseline.iloc[ptu][mask.values].count()
