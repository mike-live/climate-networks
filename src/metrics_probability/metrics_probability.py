import numpy as np


def compute_greater(train_metric, test_metric=None):
    if test_metric is None:
        inds = np.argsort(-train_metric)
        n_greater = np.zeros(len(train_metric), dtype='int32')
        n_greater[inds] = np.arange(len(train_metric))
    else:
        n_lower = np.searchsorted(
            np.sort(train_metric), 
            test_metric, 
            side='right'
        )
        n_greater = len(train_metric) - n_lower
        
    return n_greater


def compute_probability_for_metrics(train_metric, test_metric=None):
    # metric - 3D np.ndarray (lat, lon, time)

    n, m, k = train_metric.shape
    prob = np.zeros((n, m, k), dtype='float16')
    nan_mask = np.isnan(train_metric)
    is_test_metric = not test_metric is None
    if is_test_metric:
        nan_mask &= np.isnan(test_metric)

    for lat in range(n):
        for lon in range(m):
            train_metric_in_node = train_metric[lat, lon, :]
            if is_test_metric:
                test_metric_in_node = test_metric[lat, lon, :]
                n_greater = compute_greater(train_metric_in_node, test_metric_in_node)
            else:
                n_greater = compute_greater(train_metric_in_node)
            n_all = len(train_metric_in_node)
            prob[lat, lon, :] = n_greater / n_all
    prob[nan_mask] = np.nan

    return prob