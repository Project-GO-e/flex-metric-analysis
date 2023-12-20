from datetime import datetime
from pathlib import Path
from typing import Dict

from experiment_description import DeviceType
from experiment_filter import ExperimentFilter
from experiment_loader import FileLoader
from plotting import *

BASE_DIR='data/all_pc4/'

BASELINES_DIR=BASE_DIR + 'ev/baselines/'
SHIFTED_DIR=BASE_DIR + 'ev/shifted/'


if __name__ == "__main__":

    DAY = datetime(2020,6,3)

    load_filter = ExperimentFilter().with_area('9722')
    all_experiments = FileLoader(baselines_dir=Path(BASELINES_DIR), shifted_dir=Path(SHIFTED_DIR)).load_experiments(load_filter)
    
    plot: Plotting = Plotting()
    
    plot.flex_metric_heat_map_for_cong_start(all_experiments, DAY.replace(hour=10))
    
    plot.flex_metric_heat_map_for_duration(all_experiments, 16)
    # plot.flex_metric_heat_map_for_duration(all_experiments.filter(ExperimentFilter().with_area('9722')), 16)

    plot.flex_metric_histogram_per_duration(all_experiments)

    # plot.flex_metric_histogram_per_time_of_day(all_experiments)

    # plot.flex_metric_histogram_per_duration(all_experiments.filter(ExperimentFilter()))
    plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=7))))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=8))))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=9))))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=10))))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=16))))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=17))))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=18))))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=19))))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=20))))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=21))))
    
    #plot.flex_metric_histogram_per_time_of_day(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=10))))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_duration(20)))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_duration(24)))
    # plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_duration(32)))
    # plot.flex_metric_histogram(all_experiments)

    # plot.plot_multipe_percentile_and_mean(all_experiments.filter(ExperimentFilter().with_cong_starts([datetime(2020,6,3,13,45), datetime(2020,6,3,14,45),  datetime(2020,6,3,15,45)])), 95)
    # plot.plot_multipe_percentile_and_mean(all_experiments.filter(ExperimentFilter().with_cong_start(datetime(2020,6,3,17,45))), 95)
    
    plot.show()
    
    print("Done. Bye!")