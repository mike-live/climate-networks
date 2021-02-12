from helpers.parallel_maker import parallel_execute, make_args
import numpy as np

def compute_diff(result, metric, ids):
    #print('Start', ids[0], ids[-1], flush=True)
    for tid in ids:
        metric_2 = metric[tid].copy()
        if tid - 2 < 0:
            result[tid] = np.zeros_like(metric_2)
            continue
        metric_0 = metric[tid - 2].copy()
        metric_1 = metric[tid - 1].copy()

        # f'(x) by Newton polynomial approximation of second order
        # https://en.wikipedia.org/wiki/Finite_difference_coefficient
        # Backward finite difference. 1st derivative. Accuracy = 2
        # Uniform step: division is skipped for now
        diff = (metric_0 - 4 * metric_1 + 3 * metric_2) / 2
        result[tid] = diff

    #print('End', ids[0], ids[-1], flush = True)

def parallel_compute_diff_metric(config, metric):
    num_threads = config.diff_metrics['num_threads']
    result = [0] * len(metric)
    parallel_execute(num_threads, compute_diff, make_args(num_threads, result, metric))
    return np.array(result)

