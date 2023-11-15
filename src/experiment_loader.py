from pathlib import Path, PurePath
from time import time

import pandas as pd

from experiment import Experiment
from experiment_container import ExperimentContainer
from experiment_description import DeviceType, ExperimentDescription
from experiment_filter import ExperimentFilter


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
        all_experiments = {}
        missing_shifted_file = False
        device_type = DeviceType.from_string(PurePath(self.baselines_dir).parts[-2])
        print(f"Loading experiments from files...")
        t = time()
        
        experiments = filter(lambda e: ExperimentDescription.validate_name(e.stem), self.baselines_dir.iterdir())
        for exp_path in experiments:
            description = ExperimentDescription(exp_path.stem, device_type)
            
            if experiment_filter.passFilter(description):                    
                shifted_path = self.shifted_dir / exp_path.name
                try:
                    df_baseline = FileLoader.__load_file(exp_path)
                    df_shifted = FileLoader.__load_file(shifted_path)
                    all_experiments[description.name] = Experiment(df_baseline, df_shifted, description)
                except FileNotFoundError as e:
                    missing_shifted_file = True
                    print("ERROR: Experiment '" + e.filename + "' doesn't have a shifted input data file")
        # Fast fail approach:
        if missing_shifted_file : exit(1)
        print(f"Experiments loaded successfully. Loaded {len(all_experiments)} experiments in {round(time() - t)} seconds.")
        return ExperimentContainer(all_experiments)
    

    def __load_file(path: Path) -> pd.DataFrame:
        if path.suffix == '.csv':
            return FileLoader.__load_csv_file(path)
        if path.suffix == '.parquet':
            return FileLoader.__load_parquet_file(path)
        else:
            print(f"Warning: cannot load file: {path}")
            
    
    def __load_csv_file(path: Path) -> pd.DataFrame:
        # Consider using skiprows and nrows to only create dataframe for the congestion period.
        return pd.read_csv(path, sep=';', decimal=',', index_col=0, parse_dates=True)
    
    def __load_parquet_file(path: Path) -> pd.DataFrame:
        return pd.read_parquet(path)