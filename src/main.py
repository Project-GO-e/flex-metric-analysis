from pathlib import Path
from typing import Dict, List
from time import time
from datetime import datetime
from experiment import Experiment
from experiment_description import ExperimentDescription
from plotting import *

BASELINE_DIR='data/ev/baseline/'
SHIFTED_DIR='data/ev/shifted/'


def load_experiments(zipcode: List[str] = None, window: List[int] = None, cong_start: List[datetime] = None, cong_duration: List[int] = None) -> Dict[str, Experiment]:
    all_experiments = {}
    baselines_path = Path(BASELINE_DIR)
    missing_shifted_file = False
    all_files_it = baselines_path.glob('*.csv')
    print(f"Loading experiments from {len(list(all_files_it))} CSV files...")
    t = time()
    for experiment_path in baselines_path.glob('*.csv'):
        description = ExperimentDescription(experiment_path.stem)
        skip_experiment = False
        if zipcode is not None and len(zipcode) != 0 and description.get_congestion_zipcode() not in zipcode:
            skip_experiment = True
        if window is not None and len(window) != 0 and description.get_flexwindow_duration() not in window:
            skip_experiment = True
        if cong_start is not None and len(cong_start) != 0 and description.get_congestion_start() not in cong_start:
            skip_experiment = True
        if cong_duration is not None and len(cong_duration) != 0 and description.get_congestion_duration() not in cong_duration:
            skip_experiment = True

        if not skip_experiment:    
            shifted_path = Path(SHIFTED_DIR) / experiment_path.name
            try:
                e = Experiment(experiment_path, shifted_path)
                all_experiments[e.exp_des.name] = e
            except FileNotFoundError as e:
                missing_shifted_file = True
                print("ERROR: Experiment '" + e.filename + "' doesn't have a shifted input data file")
    #Fast fail approach:
    if missing_shifted_file : exit(1)
    print(f"All experiments loaded successfully. Loading time: {round(time() - t)} seconds.")
    return all_experiments



if __name__ == "__main__":

    zipcodes = ['46651']
    flex_window_durations = [48]
    cong_starts = [datetime(2020,6,3,17,45)]
    cong_durations = [16]

    all_experiments: Dict[str, Experiment] = load_experiments(zipcodes, flex_window_durations, cong_starts, cong_durations)
    
    plot_multipe_percentile_and_mean(all_experiments, 95)

    for e in all_experiments:
        plot_percentile_baseline_and_shifted(all_experiments[e], 95)

    
    print("Done. Bye!")

        
