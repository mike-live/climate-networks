from .clustering_coef import compute_clustering_coefficient
from helpers.parallel_maker import parallel_execute, make_args

def save_metrics(config, metrics):
    metrics_file_name = config.network_metrics['work_dir'] / config.network_metrics['output_metrics_file_name']
    np.save(metrics_file_name, metrics)
	

def load_metrics(config):
    metrics_file_name = config.network_metrics['work_dir'] / config.network_metrics['output_metrics_file_name']
	metrics = np.load(metrics_file_name)
	return metrics

def get_metric(metrics, metric_name, m_shape, ):
	for metric in metrics:
		cur_metric = metric[metric_name]
		

def compute_metrics(result, corr_matricies, ids):
    #print('Start', ids[0], ids[-1], flush=True)
    for tid in ids:
        corr_matrix = corr_matricies[tid].copy()
        LCC, GCC = compute_clustering_coefficient(corr_matrix)
        result[tid] = {'LCC': LCC, 'GCC': GCC}
    #print('End', ids[0], ids[-1], flush = True)

def parallel_compute_metrics(config, corr_matricies):
    num_threads = config.network_metrics['num_threads']
    result = [0] * len(corr_matricies)
    parallel_execute(num_threads, compute_metrics, make_args(num_threads, result, corr_matricies))
    return result
