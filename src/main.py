from datetime import datetime
from pathlib import Path
from typing import Dict

from experiment_description import DeviceType
from experiment_filter import ExperimentFilter
from experiment_loader import FileLoader
from plotting import *

BASE_DIR='data/hp/'

BASELINES_DIR=BASE_DIR + 'baselines/'
SHIFTED_DIR=BASE_DIR + 'shifted/'


if __name__ == "__main__":

    DAY = datetime(2020,1,15)

    # load_filter = ExperimentFilter().with_grout('9722')
    all_experiments = FileLoader(baselines_dir=Path(BASELINES_DIR), shifted_dir=Path(SHIFTED_DIR)).load_experiments()
    
    plot: Plotting = Plotting()

    plot.plot_mean_baseline_and_shifted(all_experiments)

    plot.flex_metric_histogram_per_duration(all_experiments)
    
    plot.flex_metric_heat_map_for_cong_start(all_experiments, DAY.replace(hour=10))
    
    plot.flex_metric_heat_map_for_duration(all_experiments, 16)
    # plot.flex_metric_heat_map_for_duration(all_experiments.filter(ExperimentFilter().with_group('9722')), 16)


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

    
    plot.show()
    
    print("Done. Bye!")