from typing import Dict

import matplotlib.pyplot as plt
import matplotlib.table as tbl
import matplotlib.ticker as tkr
import numpy as np
import pandas as pd

from experiment import Experiment
from experiment_container import Metadata


def plot_p_f(exp: Experiment, ptu: int):
    plt.figure(1)
    plt.scatter(exp.get_baseline(ptu), exp.get_flex_metric(ptu))
    plt.xlabel('Power (W)')
    plt.ylabel('Flex metric')
    plt.title(f"P-f, {__format_exp_name(exp)}, PTU: {ptu + 1}")
    plt.show()


def plot_mean_baseline_and_shifted(exp: Experiment):
    plt.figure(1)
    ptus = range(exp.get_congestion_duration())
    plt.plot(ptus, exp.get_baseline_profiles().mean(axis=1))
    plt.plot(ptus, exp.get_shifted_profiles().mean(axis=1))
    plt.xlabel('PTU')
    plt.ylabel('Power (W)')
    plt.title(f"Mean Power {__format_exp_name(exp.exp_des)} ")
    plt.show()


def plot_sum_baseline_and_shifted(exp: Experiment):
    plt.figure(1)
    ptus = range(exp.get_congestion_duration())
    plt.plot(ptus, exp.get_baseline_profiles().sum(axis=1))
    plt.plot(ptus, exp.get_shifted_profiles.sum(axis=1))
    plt.xlabel('PTU')
    plt.ylabel('Power (W)')
    plt.title(f"Summed Power {__format_exp_name(exp.exp_des)} ")
    plt.show()


def plot_percentile_baseline_and_shifted(exp: Experiment, percentile):
    plt.figure(1)
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
    plt.show()


def plot_multipe_percentile_and_mean(experiments: Dict[str, Experiment], percentile: int, single_plot: bool = False):

    exp_per_cong_start :Dict[str, Experiment] = {}

    for e in experiments.values():
        exp_per_cong_start.setdefault(e.get_congestion_start(), [])
        exp_per_cong_start[e.get_congestion_start()].append(e)
    
    fig_idx = 0
    subplot_idx = 1

    if single_plot:
        fig = plt.figure(fig_idx, figsize=(15, 12))

    for cong_start in exp_per_cong_start:
        if not single_plot:
            fig = plt.figure(fig_idx, figsize=(15, 12))
            subplot_idx = 1
        # plt.ion()
        plt.subplots_adjust(hspace=0.5)
        fig.suptitle(f"Congestion start: {cong_start}")
        ax = None

        for exp in sorted(exp_per_cong_start[cong_start], key=lambda x: x.get_congestion_duration()):
            num_of_rows = len(exp_per_cong_start) if single_plot else 1
            ax = plt.subplot(num_of_rows, len(exp_per_cong_start[cong_start]), subplot_idx, sharey=ax)
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
        
            if subplot_idx == 1: ax.set_ylabel('Power (W)')
            
            subplot_idx += 1
            
        if not single_plot : fig_idx += 1
        
        Line, Label = ax.get_legend_handles_labels()
        fig.legend(Line, Label) 
    plt.show()


def plot_mean_flex_metric(data : pd.DataFrame, metadata: Metadata):
    if len(data.columns) == 0:
        raise AssertionError("No data. Cannot make plot.")
    
    # Displaying dataframe as an heatmap with diverging colourmap as RdYlBu 
    # The imshow command puts the rows to the y-axis, we want that on x-axis.
    plt.imshow(data.transpose(), cmap ="RdYlBu", vmin=0, vmax=1)
    
    # Displaying a color bar to understand which color represents which range of data 
    plt.colorbar() 
    
    plt.xticks(range(len(data)), data.index) 
    plt.xlabel(metadata.rows)
    plt.yticks(range(len(data.columns.values)), data.columns)
    plt.ylabel(metadata.colums)
    
    plt.show()


def __format_exp_name(exp) -> str:
    return f"start: {str(exp.get_congestion_start())}, duration: {exp.get_congestion_duration()}, window: {exp.get_flexwindow_duration()}"