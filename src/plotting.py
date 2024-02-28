from datetime import datetime
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import matplotlib.table as tbl
import matplotlib.ticker as tkr
import numpy as np
import pandas as pd

from experiment.experiment import Experiment
from experiment.experiment_container import ExperimentContainer
from experiment.experiment_filter import ExperimentFilter
from experiment.experiment_loader import FileLoader

BASE_DIR='data/hp/'

BASELINES_DIR=BASE_DIR + 'baseline/'
SHIFTED_DIR=BASE_DIR + 'shifted/'

class Plotting():

    def __init__(self, block_on_plot: bool = False) -> None:
        self.block_on_plot = block_on_plot
        self.figure_cnt: int = 1
        

    def show(self):
        plt.show(block=True)


    def __create_figure(self, *args, **kwargs):
        self.figure_cnt += 1
        return plt.figure(self.figure_cnt - 1, **kwargs)


    def plot_experiment_mean_baseline_and_shifted(self, exp: Experiment):
        self.__create_figure()
        ptus = range(exp.get_congestion_duration())
        plt.plot(ptus, exp.get_baseline_profiles().mean(axis=1))
        plt.plot(ptus, exp.get_shifted_profiles().mean(axis=1))
        plt.xlabel('PTU')
        plt.ylabel('Power (W)')
        plt.title(f"Mean\n{Plotting.__format_exp_name(exp.exp_des)} ")
        plt.show(block=self.block_on_plot)


    def plot_experiement_sum_baseline_and_shifted(self, exp: Experiment):
        self.__create_figure()
        ptus = range(exp.get_congestion_duration())
        plt.plot(ptus, exp.get_baseline_profiles().sum(axis=1))
        plt.plot(ptus, exp.get_shifted_profiles().sum(axis=1))
        plt.xlabel('PTU')
        plt.ylabel('Power (W)')
        plt.title(f"Summed Power \n{Plotting.__format_exp_name(exp.exp_des)} ")
        plt.show(block=self.block_on_plot)


    def plot_percentile_baseline_and_shifted(self, exp: Experiment, percentile):
        self.__create_figure()
        ptus = range(exp.get_congestion_duration())
        baseline_percentile = []
        shifted_percentile = []

        for i in ptus:
            mask = exp.get_baseline_profiles().iloc[i] != 0.0
            baseline_percentile.append(np.percentile(exp.get_baseline_profiles().iloc[i][mask.values], percentile, axis=0))
            shifted_percentile.append(np.percentile(exp.get_shifted_profiles().iloc[i][mask.values], percentile, axis=0))
        
        plt.plot(ptus, baseline_percentile)
        plt.plot(ptus, shifted_percentile)
        plt.xlabel('PTU')
        plt.ylabel('Power (W)')
        plt.title(f"P{percentile} Power, {Plotting.__format_exp_name(exp.exp_des)}")
        plt.show(block=self.block_on_plot)


    def plot_mean_baseline_and_shifted(self, experiments: ExperimentContainer):
        if len(experiments.exp) == 0:
            raise AssertionError("No experiment data to plot")
        exp_per_cong_start :Dict[str, Experiment] = {}

        for e in experiments.exp.values():
            exp_per_cong_start.setdefault(e.get_congestion_start(), [])
            exp_per_cong_start[e.get_congestion_start()].append(e)
        
        fig = self.__create_figure(figsize=[15,12])
        subplot_idx = 0
        nrows = len(exp_per_cong_start)
        subfigs = fig.subfigures(nrows=nrows, ncols=1)

        # UGLY! Apperently the return type of subfigures depends on the dimension of subfigures.
        if not type(subfigs) is np.ndarray: subfigs = [subfigs]
        
        for cong_start in exp_per_cong_start:
            ax = None
            cols = len(exp_per_cong_start[cong_start])
            subfigs[int(subplot_idx / cols)].suptitle(f"Congestion start: {cong_start}")
            subfigs[int(subplot_idx / cols)].subplots_adjust(top=0.8)
            axs = subfigs[int(subplot_idx / cols)].subplots(nrows=1, ncols=cols)
            
            # UGLY! Apperently the return type of subplots depends on the dimension of subfigures.
            if not type(axs) is np.ndarray: axs = [axs]

            for exp in sorted(exp_per_cong_start[cong_start], key=lambda x: x.get_congestion_duration()):
                ax = axs[subplot_idx % cols]
                ptus = range(exp.get_congestion_duration())
                baseline_mean = []
                shifted_mean = []
                count_len = []

                for i in ptus:
                    baseline_mean.append(exp.get_baseline(i).sum() / exp.get_num_active_baseline_devices(i))
                    shifted_mean.append(exp.get_shifted(i).sum() / exp.get_num_active_baseline_devices(i))
                    count_len.append(exp.get_num_active_baseline_devices(i))
                ax.plot(ptus, baseline_mean, label = 'Baseline mean')
                ax.plot(ptus, shifted_mean, label = 'Shifted mean')
                ax.xaxis.set_major_formatter(tkr.FormatStrFormatter('%d'))
                ax.set_title(f"Duration: {exp.get_congestion_duration()}", y=1.05)
                table = tbl.table(ax=ax, cellText=[count_len], loc='top')
            
                if subplot_idx % cols == 0 : ax.set_ylabel('Power (W)')
                
                subplot_idx += 1

            Line, Label = ax.get_legend_handles_labels()
            fig.legend(Line, Label) 
        plt.show(block=self.block_on_plot)


    def flex_metric_heat_map_for_cong_start(self, container: ExperimentContainer, cong_start: datetime):
        data = container.filter(ExperimentFilter().with_cong_start(cong_start)).get_mean_flex_per_duration_per_ptu()
        df = pd.DataFrame(data).map(np.mean).transpose()
        
        if len(df.columns) == 0:
            raise AssertionError("No data. Cannot make plot.")
        self.__create_figure()

        # Displaying dataframe as an heatmap with diverging colourmap as RdYlBu 
        # The imshow command puts the rows to the y-axis, we want that on x-axis.
        plt.imshow(df, cmap ="RdYlBu", vmin=0, vmax=1)

        # Displaying a color bar to understand which color represents which range of data 
        plt.colorbar() 
        plt.title(f"{' ,'.join(container.get_groups())} - {cong_start}")
        plt.xticks(range(len(df.columns.values)), df.columns)
        plt.xlabel("PTU")
        plt.yticks(range(len(df)), df.index) 
        plt.ylabel("duration")
        plt.show(block=self.block_on_plot)


    def flex_metric_heat_map_for_duration(self, container: ExperimentContainer, duration: int):
        data = container.filter(ExperimentFilter().with_cong_duration(duration)).get_mean_flex_per_congestion_start_per_ptu()
        df = pd.DataFrame(data).map(np.mean).transpose()
        
        if len(df.columns) == 0:
            raise AssertionError("No data. Cannot make plot.")
        self.__create_figure()

        # Displaying dataframe as an heatmap with diverging colourmap as RdYlBu 
        # The imshow command puts the rows to the y-axis, we want that on x-axis.
        plt.imshow(df, cmap ="RdYlBu", vmin=0, vmax=1)

        # Displaying a color bar to understand which color represents which range of data 
        plt.colorbar() 
        plt.title(f"{' ,'.join(container.get_groups())} - {duration}")
        plt.xticks(range(len(df.columns.values)), df.columns)
        plt.xlabel("PTU")
        plt.yticks(range(len(df)), df.index) 
        plt.ylabel("Cong. start")
        plt.show(block=self.block_on_plot)


    def flex_metric_histogram(self, container: ExperimentContainer):
        self.__create_figure()
        flex_metrics: pd.Series = pd.Series(container.get_mean_flex())
        plt.hist(flex_metrics, range=[0,1])
        plt.title(f"Mean weighted flex metric. {round(flex_metrics.mean(),2)}, {round(flex_metrics.std(),2)}, {round(np.percentile(container.get_mean_flex(), 10),2)}")
        plt.show(block=self.block_on_plot)


    def flex_metric_histogram_per_duration(self, container: ExperimentContainer):
        fig = self.__create_figure()
        flex_metrics_per_duration = container.get_mean_flex_per_duration()
        axes = fig.subplots(1, len(flex_metrics_per_duration))
        for idx, duration in enumerate(flex_metrics_per_duration):
            pd.DataFrame(flex_metrics_per_duration[duration]).hist(ax=axes[idx], range=[0,1], bins=20)
            axes[idx].set_title(str(duration))
        plt.show(block=self.block_on_plot)

    def flex_metric_histogram_per_time_of_day(self, container: ExperimentContainer):
        flex_metrics = container.get_mean_flex_for_time_of_day()
        flex_metric_keys = sorted(flex_metrics.keys())
        PLOTS_PER_FIG = 6
        for idx in range(int(len(flex_metric_keys) / PLOTS_PER_FIG) + 1):
            fig, axes = plt.subplots(1, min(PLOTS_PER_FIG, len(flex_metric_keys) - idx * PLOTS_PER_FIG))
            for plot_idx, ax in enumerate(axes):
                ptu = flex_metric_keys[plot_idx + idx * PLOTS_PER_FIG]
                df = pd.DataFrame(flex_metrics[ptu])
                df.hist(ax=ax, range=[0,1], bins=20)
                ax.set_title(str(ptu))
            plt.show(block=self.block_on_plot)
            self.figure_cnt += 1


    def __format_exp_name(exp) -> str:
        return f"start: {str(exp.get_congestion_start())}, duration: {exp.get_congestion_duration()}, window: {exp.get_flexwindow_duration()}"
    

if __name__ == "__main__":

    DAY = datetime(2020,1,15)

    # load_filter = ExperimentFilter().with_grout('9722')
    all_experiments = FileLoader(baselines_dir=Path(BASELINES_DIR), shifted_dir=Path(SHIFTED_DIR)).load_experiments()
    
    plot: Plotting = Plotting()

    # plot.plot_mean_baseline_and_shifted(all_experiments)

    # plot.flex_metric_histogram_per_duration(all_experiments)
    
    # plot.flex_metric_heat_map_for_cong_start(all_experiments, DAY.replace(hour=10))
    
    # plot.flex_metric_heat_map_for_duration(all_experiments, 16)
    # plot.flex_metric_heat_map_for_duration(all_experiments.filter(ExperimentFilter().with_group('9722')), 16)


    # plot.flex_metric_histogram_per_time_of_day(all_experiments)

    # plot.flex_metric_histogram_per_duration(all_experiments.filter(ExperimentFilter()))
    #plot.flex_metric_histogram(all_experiments.filter(ExperimentFilter().with_cong_start(DAY.replace(hour=7))))
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
    plot.flex_metric_histogram(all_experiments)

    
    plot.show()
    
    print("Done. Bye!")