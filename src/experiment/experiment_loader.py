from datetime import datetime, time
from pathlib import Path, PurePath
from time import time as time_s

import pandas as pd

from .experiment import Experiment
from .experiment_container import ExperimentContainer
from .experiment_description import DeviceType, ExperimentDescription
from .experiment_filter import ExperimentFilter


class FileLoader():

    def __init__(self, baselines_dir: Path, shifted_dir: Path) -> None:
        if not baselines_dir.exists():
            raise AssertionError(f"Baselines directory '{baselines_dir}' does not exist")
        if not any(baselines_dir.iterdir()):
            raise AssertionError(f"Baselines directory '{baselines_dir}' is empty")
        if not shifted_dir.exists():
            raise AssertionError(f"Shifted directory '{shifted_dir}' does not exist")
        if not any(shifted_dir.iterdir()):
            raise AssertionError(f"Shifted directory '{shifted_dir}' is empty")
        self.baselines_dir = baselines_dir
        self.shifted_dir = shifted_dir   
    
    def load_experiments(self, experiment_filter: ExperimentFilter = ExperimentFilter()) -> ExperimentContainer:
        loaded_experiments = {}
        missing_baseline = False
        device_type = DeviceType.from_string(PurePath(self.shifted_dir).parts[-2])
        print("Loading experiments from files...")
        t = time_s()
        all_experiments = list(filter(lambda e: ExperimentDescription.validate_name(e.stem), self.shifted_dir.iterdir()))

        for cnt_checked, exp_path in enumerate(all_experiments):
            description = ExperimentDescription(exp_path.stem, device_type)
            if cnt_checked > 0 and cnt_checked % int(max(len(all_experiments),10) / 10) == 0:
                print(f"Loaded {len(loaded_experiments)} / {cnt_checked} experiments.")
            if experiment_filter.pass_filter(description):                    
                baseline = (self.baselines_dir / description.get_baseline_file_name()).with_suffix('.csv')
                if not baseline.exists():
                    baseline = (self.baselines_dir / description.get_baseline_file_name()).with_suffix('.parquet')
                df_shifted = self.__load_file(exp_path)
                try:
                    df_baseline: pd.DataFrame = self.__load_file(baseline)
                    day = description.get_congestion_start().date()
                    idx = df_baseline.index.get_loc(datetime.combine(day, time()))
                    loaded_experiments[description.name] = Experiment(df_baseline.iloc[idx:idx+96], df_shifted, description)
                except FileNotFoundError as e:
                    missing_baseline = True
                    print("ERROR: Experiment '" + e.filename + "' doesn't have a baseline input data file")
        
        # Fast fail approach:
        if missing_baseline : exit(1)
        print(f"Experiments loaded successfully. Loaded {len(loaded_experiments)} / {cnt_checked} experiments in {round(time_s() - t)} seconds.")
        return ExperimentContainer(loaded_experiments)

    def __load_file(self, path: Path) -> pd.DataFrame:
        if path.suffix == '.csv':
            # Consider using skiprows and nrows to only create dataframe for the congestion period.
            return pd.read_csv(path, sep=';', decimal=',', index_col=0, parse_dates=True)
        if path.suffix == '.parquet':
            return pd.read_parquet(path)
        else:
            print(f"Warning: cannot load file: {path}")
