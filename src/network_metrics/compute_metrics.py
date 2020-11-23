from .clustering_coef import compute_clustering_coefficient
from helpers.parallel_maker import parallel_execute, make_args

def compute_metrics(result, corr_matricies, ids):
    for tid in ids:
        LCC, GCC = compute_clustering_coefficient(corr_matricies[tid])
        result[tid] = {'LCC': LCC, 'GCC': GCC}

def parallel_compute_metrics(config, corr_matricies):
    num_threads = config.network_metrics['num_threads']
    result = [0] * len(corr_matricies)
    parallel_execute(num_threads, compute_metrics, make_args(num_threads, result, corr_matricies))
    return result
