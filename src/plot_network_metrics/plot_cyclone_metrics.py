import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def plot_local_grid_metric(cur_cyclone, metric_name, image_path):
    cur_times = pd.to_datetime(cur_cyclone['times']).values
    cur_metric = np.array(cur_cyclone['metrics'])
    cur_means = np.array(cur_cyclone['means'])
    cur_stds = np.array(cur_cyclone['stds'])
    
    import matplotlib.dates as mdates
    fig = plt.figure(figsize=(7, 4), dpi=200)
    ax = plt.gca()
    plt.plot(cur_times, cur_metric, label='Metric')
    plt.plot(cur_times, cur_means, label='Mean')
    plt.fill_between(cur_times, cur_means + cur_stds, cur_means - cur_stds, color='b', alpha=0.15)
    plt.legend(loc='upper left')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d %H:%M'))
    
    plt.title(metric_name)    
    fig.autofmt_xdate()
    plt.tight_layout()

    file_name = image_path / (metric_name + '.png')
    file_name.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(file_name)
    plt.close()


def plot_metric_probability(cur_cyclone, metric_name, image_path):
    import matplotlib.dates as mdates

    cur_times = pd.to_datetime(cur_cyclone['times']).values
    cur_prob = np.array(cur_cyclone['prob'])

    fig = plt.figure(figsize=(7, 4), dpi=200)
    ax = plt.gca()
    ax.plot(cur_times, cur_prob, zorder=1)
    ax.axhline(0.5, color='gray', zorder=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d %H:%M'))
    ax.set_title(metric_name)
    ax.set_ylabel('Probability')
    ax.set_ylim([0, 1])

    fig.autofmt_xdate()
    fig.tight_layout()

    file_name = image_path / (metric_name + '_probability.png')
    file_name.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(file_name)
    plt.close()
