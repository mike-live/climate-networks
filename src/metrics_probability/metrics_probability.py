import numpy as np


def compute_greater(metric_array):
    inds = np.argsort(-metric_array)
    n_greater = np.zeros(len(metric_array))
    n_greater[inds] = range(len(metric_array))
    return n_greater


def compute_probability_for_metrics(metric):
    # metric - 3D np.ndarray (lat, lon, time)

    n, m, k = metric.shape
    prob = np.zeros((n, m, k), dtype='float')
    nan_mask = np.isnan(metric)

    for lat in range(n):
        for lon in range(m):
            metric_in_node = metric[lat, lon, :]
            n_all = len(metric_in_node)
            n_greater = compute_greater(metric_in_node)
            prob[lat, lon, :] = n_greater / n_all
    prob[nan_mask] = np.nan

    return prob
