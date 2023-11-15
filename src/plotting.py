from datetime import datetime
from typing import Dict, List

import matplotlib.pyplot as plt
import matplotlib.table as tbl
import matplotlib.ticker as tkr
import numpy as np
import pandas as pd

from experiment import Experiment
from experiment_container import ExperimentContainer, Metadata


class Plotting():

    def __init__(self, block_on_plot: bool = False) -> None:
        self.block_on_plot = block_on_plot
        self.figure_cnt: int = 1
        

    def show(self):
        plt.show(block=True)


    def __create_figure(self, *args, **kwargs):
        self.figure_cnt += 1
        return plt.figure(self.figure_cnt - 1, **kwargs)


    def plot_p_f(self, exp: Experiment, ptu: int):
        self.__create_figure()
        plt.scatter(exp.get_baseline(ptu), exp.get_flex_metric(ptu))
        plt.xlabel('Power (W)')
        plt.ylabel('Flex metric')
        plt.title(f"P-f, {__format_exp_name(exp)}, PTU: {ptu + 1}")   
        plt.show(block=self.block_on_plot)


    def plot_mean_baseline_and_shifted(self, exp: Experiment):
        self.__create_figure()
        ptus = range(exp.get_congestion_duration())
        plt.plot(ptus, exp.get_baseline_profiles().mean(axis=1))
        plt.plot(ptus, exp.get_shifted_profiles().mean(axis=1))
        plt.xlabel('PTU')
        plt.ylabel('Power (W)')
        plt.title(f"Mean Power {__format_exp_name(exp.exp_des)} ")
        plt.show(block=self.block_on_plot)


    def plot_sum_baseline_and_shifted(self, exp: Experiment):
        self.__create_figure()
        ptus = range(exp.get_congestion_duration())
        plt.plot(ptus, exp.get_baseline_profiles().sum(axis=1))
        plt.plot(ptus, exp.get_shifted_profiles.sum(axis=1))
        plt.xlabel('PTU')
        plt.ylabel('Power (W)')
        plt.title(f"Summed Power {__format_exp_name(exp.exp_des)} ")
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
        plt.title(f"P{percentile} Power, {__format_exp_name(exp.exp_des)}")
        plt.show(block=self.block_on_plot)


    def plot_multipe_percentile_and_mean(self, experiments: ExperimentContainer, percentile: int):
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
                baseline_percentile = []
                shifted_percentile = []
                count_len = []

                for i in ptus:
                    baseline_mean.append(exp.get_baseline(i).mean())
                    shifted_mean.append(exp.get_shifted(i).mean())
                    baseline_percentile.append(np.percentile(exp.get_baseline(i), percentile, axis=0))
                    shifted_percentile.append(np.percentile(exp.get_shifted(i), percentile, axis=0))
                    count_len.append(exp.get_num_active_baseline_devices(i))
                ax.plot(ptus, baseline_mean, label = 'Baseline mean')
                ax.plot(ptus, baseline_percentile, label = f'Baseline P{percentile}')
                ax.plot(ptus, shifted_mean, label = 'Shifted mean')
                ax.plot(ptus, shifted_percentile, label = f'Shifted P{percentile}')
                ax.xaxis.set_major_formatter(tkr.FormatStrFormatter('%d'))
                ax.set_title(f"Duration: {exp.get_congestion_duration()}", y=1.05)
                table = tbl.table(ax=ax, cellText=[count_len], loc='top')
            
                if subplot_idx % cols == 0 : ax.set_ylabel('Power (W)')
                
                subplot_idx += 1

            Line, Label = ax.get_legend_handles_labels()
            fig.legend(Line, Label) 
        plt.show(block=self.block_on_plot)


    def plot_mean_flex_metric(self, data : pd.DataFrame, metadata: Metadata):
        if len(data.columns) == 0:
            raise AssertionError("No data. Cannot make plot.")
        self.__create_figure()
        # data.to_csv('out.csv')
        # Displaying dataframe as an heatmap with diverging colourmap as RdYlBu 
        # The imshow command puts the rows to the y-axis, we want that on x-axis.
        plt.imshow(data.transpose(), cmap ="RdYlBu", vmin=0, vmax=1)

        # Displaying a color bar to understand which color represents which range of data 
        plt.colorbar() 
        plt.xticks(range(len(data)), data.index) 
        plt.xlabel(metadata.rows)
        plt.yticks(range(len(data.columns.values)), data.columns)
        plt.ylabel(metadata.colums)
        plt.show(block=self.block_on_plot)


    def flex_metric_histogram(self, flex_metrics: Dict[datetime, List[float]]):        
        flex_metric_keys = sorted(flex_metrics.keys())
        
        for idx in range(4):
            fig, axes = plt.subplots(1, 6)
            for plot_idx, key_idx in enumerate(range(0, 24, 4)):
                ptu = flex_metric_keys[key_idx + idx*24]
                df = pd.DataFrame(flex_metrics[ptu])
                df.hist(ax=axes[plot_idx], range=[0,1], bins=20)
                axes[plot_idx].set_title(str(ptu))
            plt.show(block=self.block_on_plot)
            self.figure_cnt += 1


def __format_exp_name(exp) -> str:
    return f"start: {str(exp.get_congestion_start())}, duration: {exp.get_congestion_duration()}, window: {exp.get_flexwindow_duration()}"