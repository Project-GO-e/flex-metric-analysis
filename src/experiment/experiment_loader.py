
from abc import ABC, abstractmethod
from datetime import datetime, time
from pathlib import Path, PurePath
from time import time as time_s
from typing import List

import pandas as pd

from experiment.device_type import DeviceType

from .experiment import Experiment
from .experiment_container import ExperimentContainer
from .experiment_description import DataSource, ExperimentDescription
from .experiment_filter import ExperimentFilter


class ExperimentLoader():
    '''
    Load experiments from files with different formats according to the data source.
    NOTE: this experiment loader assumes that a directory with input files contains profiles for only one device type.
    '''

    def __init__(self, baselines_dir: Path, shifted_dir: Path, data_source: DataSource) -> None:
        if not baselines_dir.exists():
            raise AssertionError(f"Baselines directory '{baselines_dir}' does not exist")
        if not any(baselines_dir.iterdir()):
            raise AssertionError(f"Baselines directory '{baselines_dir}' is empty")
        if not shifted_dir.exists():
            raise AssertionError(f"Shifted directory '{shifted_dir}' does not exist")
        if not any(shifted_dir.iterdir()):
            raise AssertionError(f"Shifted directory '{shifted_dir}' is empty")
        if data_source == DataSource.GO_E:
            self.file_loader = _Go_eLoader(baselines_dir, shifted_dir)
        elif data_source == DataSource.ELAAD_AGG:
            self.file_loader = _ElaadAggLoader(baselines_dir, shifted_dir)
        else:
            raise AssertionError(f"No support for loading files of source {data_source}")

    def load_experiments(self, experiment_filter: ExperimentFilter = ExperimentFilter()) -> ExperimentContainer:
        loaded_experiments = {}
        missing_baseline = False
        device_type = self.file_loader.get_device_type()
        print("Loading experiments from files...")
        t = time_s()
        all_experiments: List[Path] = list(filter(lambda e: ExperimentDescription.validate_name(e.stem), self.file_loader.shifted_dir.iterdir()))

        for cnt_checked, exp_path in enumerate(all_experiments):
            description = ExperimentDescription(exp_path.stem, device_type)
            if cnt_checked > 0 and cnt_checked % int(max(len(all_experiments),10) / 10) == 0:
                print(f"Loaded {len(loaded_experiments)} / {cnt_checked} experiments.")
            if experiment_filter.pass_filter(description):
                try:
                    loaded_experiments[description.name] = self.file_loader.load_experiment(description, exp_path)
                except FileNotFoundError as e:
                    missing_baseline = True
                    print("ERROR: Experiment '" + e.filename + "' doesn't have a baseline input data file")

        # Fast fail approach:
        if missing_baseline : exit(1)
        print(f"Experiments loaded successfully. Loaded {len(loaded_experiments)} / {cnt_checked + 1} experiments in {round(time_s() - t)} seconds.")
        return ExperimentContainer(loaded_experiments)


class _DataSourceLoader(ABC):

    def __init__(self, baselines_dir: Path, shifted_dir: Path ) -> None:
        self.baselines_dir = baselines_dir
        self.shifted_dir = shifted_dir

    @abstractmethod
    def load_experiment(self, description: ExperimentDescription, exp_path: Path) -> Experiment:
        pass

    @abstractmethod
    def get_device_type(self) -> DeviceType:
        pass


class _Go_eLoader(_DataSourceLoader):
  
    def load_experiment(self, description: ExperimentDescription, exp_path: Path) -> Experiment:
        baseline = (self.baselines_dir / description.get_baseline_file_name()).with_suffix('.csv')
        if not baseline.exists():
            baseline = (self.baselines_dir / description.get_baseline_file_name()).with_suffix('.parquet')
        df_shifted = self.__load_file(exp_path)
        df_baseline: pd.DataFrame = self.__load_file(baseline)
        day = description.congestion_start.date()
        idx = df_baseline.index.get_loc(datetime.combine(day, time()))
        return Experiment(df_baseline.iloc[idx:idx+96], df_shifted, description)
    
    def get_device_type(self) -> DeviceType:
        return DeviceType.from_string(PurePath(self.shifted_dir).parts[-2])

    def __load_file(self, path: Path) -> pd.DataFrame:
        if path.suffix == '.csv':
            # Consider using skiprows and nrows to only create dataframe for the congestion period.
            return pd.read_csv(path, sep=';', decimal=',', index_col=0, parse_dates=True)
        if path.suffix == '.parquet':
            return pd.read_parquet(path)
        else:
            print(f"Warning: cannot load file: {path}")


class _ElaadAggLoader(_DataSourceLoader):

    def load_experiment(self, description: ExperimentDescription, exp_path: Path) -> Experiment:
        baseline_path = (self.baselines_dir / description.get_baseline_file_name()).with_suffix('.csv')
        baseline = self.__read_file(baseline_path)
        df_shifted = self.__read_file(exp_path)
        return Experiment(baseline, df_shifted, description)

    def get_device_type(self) -> DeviceType:
        return DeviceType.EV
    
    def __read_file(self, path: Path) -> pd.DataFrame:
        amout_charging_points = int(path.stem.split('-')[2])
        assert(amout_charging_points > 0 and amout_charging_points < 10000)
        return pd.read_csv(path, sep=',', header=0, index_col=0, parse_dates=True, date_format='%H:%M')[['Average']] / amout_charging_points * 1000
