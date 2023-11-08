

from pathlib import Path, PurePath
from time import time

import pandas as pd

from experiment import Experiment
from experiment_container import ExperimentContainer
from experiment_description import DeviceType, ExperimentDescription
from experiment_filter import ExperimentFilter


class CsvLoader():

    def __init__(self, baselines_dir: Path, shifted_dir: Path) -> None:
        self.baselines_dir = baselines_dir
        self.shifted_dir = shifted_dir


    def load_experiments(self, filter : ExperimentFilter = ExperimentFilter()) -> ExperimentContainer:
        all_experiments = {}
        missing_shifted_file = False
        device_type = DeviceType.from_string(PurePath(self.baselines_dir).parts[-2])
        all_files_it = self.baselines_dir.glob('*.csv')
        print(f"Loading experiments from {len(list(all_files_it))} CSV files...")
        t = time()
        for experiment_path in self.baselines_dir.glob('*.csv'):
            description = ExperimentDescription(experiment_path.stem, device_type)
            
            if filter.passFilter(description):
                shifted_path = self.shifted_dir / experiment_path.name
                try:
                    # Consider using skiprows and nrows to only create dataframe for the congestion period.
                    df_baseline = pd.read_csv(experiment_path, sep=';', decimal=',', index_col=0, parse_dates=True)
                    df_shifted = pd.read_csv(shifted_path, sep=';', decimal=',', index_col=0, parse_dates=True)
        
                    e = Experiment(df_baseline, df_shifted, description)
                    all_experiments[e.exp_des.name] = e
                except FileNotFoundError as e:
                    missing_shifted_file = True
                    print("ERROR: Experiment '" + e.filename + "' doesn't have a shifted input data file")
        # Fast fail approach:
        if missing_shifted_file : exit(1)
        print(f"All experiments loaded successfully. Loading time: {round(time() - t)} seconds.")
        return ExperimentContainer(all_experiments)