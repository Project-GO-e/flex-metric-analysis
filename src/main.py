from datetime import datetime
from pathlib import Path
from typing import Dict

from csv_loader import CsvLoader
from experiment_description import DeviceType
from experiment_filter import ExperimentFilter
from plotting import *

BASELINE_DIR='data/ev/baseline/'
SHIFTED_DIR='data/ev/shifted/'


if __name__ == "__main__":


    load_filter = ExperimentFilter().with_area('46651').with_flex_window_duration(48).with_cong_durations([16, 20, 24])

    all_experiments = CsvLoader(baselines_dir=Path(BASELINE_DIR), shifted_dir=Path(SHIFTED_DIR)).load_experiments()
    
    
    plot = Plotting()
    
    data = all_experiments.get_mean_flex_for_time_of_day(DeviceType.EV, ['46651'], 48)
    
    plot.flex_metric_histogram(data)
    
    
    
    # data, metadata = all_experiments.get_mean_flex_for_congestion_start(DeviceType.EV, ['46651'], 48, 24)
    

    # plot.plot_mean_flex_metric(data, metadata)

    # data, metadata = all_experiments.get_mean_flex_for_duration(DeviceType.EV, ['46651'], 48, datetime(2020,6,3,13,45))
    # # plot.plot_mean_flex_metric(data, metadata)
    
    # plot.plot_multipe_percentile_and_mean(all_experiments.filter(ExperimentFilter().with_cong_starts([datetime(2020,6,3,13,45), datetime(2020,6,3,14,45),  datetime(2020,6,3,15,45)])), 95)
    
    # plot.plot_multipe_percentile_and_mean(all_experiments.filter(ExperimentFilter().with_cong_start(datetime(2020,6,3,17,45))), 95)
    
    plot.show()
    
    print("Done. Bye!")