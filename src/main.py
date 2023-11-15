from datetime import datetime
from pathlib import Path
from typing import Dict

from experiment_description import DeviceType
from experiment_filter import ExperimentFilter
from experiment_loader import FileLoader
from plotting import *

BASE_DIR='data/data_all_pc4_broken/'

BASELINES_DIR=BASE_DIR + 'ev/baselines/'
SHIFTED_DIR=BASE_DIR + 'ev/shifted/'


if __name__ == "__main__":

    load_filter = ExperimentFilter().with_area('1077')
    all_experiments = FileLoader(baselines_dir=Path(BASELINES_DIR), shifted_dir=Path(SHIFTED_DIR)).load_experiments(load_filter)
    
    plot: Plotting = Plotting()
    
    data = all_experiments.get_mean_flex_for_time_of_day(DeviceType.EV, ['1077'], 96)
    
    
    # plot.plot_multipe_percentile_and_mean(all_experiments.filter(ExperimentFilter().with_cong_starts([datetime(2020,6,3,13,45), datetime(2020,6,3,14,45),  datetime(2020,6,3,15,45)])), 95)
    
    plot.plot_multipe_percentile_and_mean(all_experiments.filter(ExperimentFilter().with_cong_start(datetime(2020,6,3,18,00))), 95)
    
        
    data, metadata = all_experiments.get_mean_flex_for_congestion_start(DeviceType.EV, ['1077'], 96, 24)
    plot.plot_mean_flex_metric(data, metadata)

    plot.show()
    # data, metadata = all_experiments.get_mean_flex_for_duration(DeviceType.EV, ['6651'], 48, datetime(2020,6,3,13,45))
    # plot.plot_mean_flex_metric(data, metadata)
    
    # plot.show()
    
    print("Done. Bye!")