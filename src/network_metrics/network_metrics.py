from .clustering_coef import compute_clustering_coefficient, compute_weighted_clustering_coefficient
from .simple_metrics import compute_degrees, compute_eigenvector_centrality, compute_closeness
from corr_network.corr_network import expand_to_2d_by_mask
from helpers.parallel_maker import parallel_execute, make_args
import numpy as np

def prepare_metric(metric_name, sel_metric, mask):
    if str(metric_name).startswith('network_metrics'):
        sel_metric = np.array(sel_metric)
        cur_metric = sel_metric[0]
        sel_metric = np.moveaxis(sel_metric, 0, -1)
        if np.isscalar(cur_metric):
            pass
        elif mask.sum() == len(cur_metric):
            sel_metric = expand_to_2d_by_mask(sel_metric, mask)
        else:
            assert(False)
    if str(metric_name).startswith('input_data'):
        sel_metric = np.moveaxis(sel_metric, 0, -1)
    return sel_metric

def extract_metric(metrics, metric_name, mask):
    sel_metric = []
    for metric in metrics[metric_name]:
        cur_metric = metric
        if metric_name == 'EVC' or metric_name == 'EVC_w':
            cur_metric = np.abs(cur_metric)
        if type(cur_metric) is np.ndarray:
            cur_metric = cur_metric.flatten()
        sel_metric.append(cur_metric)
    sel_metric = prepare_metric(metric_name, sel_metric, mask)
    return sel_metric

def compute_metrics(result, corr_matricies, ids):
    #print('Start', ids[0], ids[-1], flush=True)
    for tid in ids:
        corr_matrix = corr_matricies[tid].copy()
        weight_thr = np.quantile(corr_matrix, 0.95)
        corr_matrix_thr = corr_matrix > weight_thr

        LCC_w, GCC_w = compute_weighted_clustering_coefficient(corr_matrix)
        LCC, GCC = compute_clustering_coefficient(corr_matrix_thr)

        degree   = compute_degrees(corr_matrix_thr)
        degree_w = compute_degrees(corr_matrix)

        eigenvector_centrality   = compute_eigenvector_centrality(corr_matrix_thr)
        eigenvector_centrality_w = compute_eigenvector_centrality(corr_matrix)

        closeness   = compute_closeness(corr_matrix_thr, is_weighted = False)
        closeness_w = compute_closeness(corr_matrix, is_weighted = True)

        result['LCC'][tid]         = LCC
        result['GCC'][tid]         = GCC 
        result['LCC_w'][tid]       = LCC_w
        result['GCC_w'][tid]       = GCC_w
        result['degree'][tid]      = degree
        result['degree_w'][tid]    = degree_w
        result['EVC'][tid]         = eigenvector_centrality
        result['EVC_w'][tid]       = eigenvector_centrality_w
        result['closeness'][tid]   = closeness
        result['closeness_w'][tid] = closeness_w
    #print('End', ids[0], ids[-1], flush = True)

def parallel_compute_metrics(config, corr_matricies):
    num_threads = config.network_metrics['num_threads']
    result = {
        'LCC':          np.zeros((corr_matricies.shape[0], corr_matricies.shape[1]), dtype = np.float32),
        'GCC':          np.zeros((corr_matricies.shape[0],), dtype = np.float32), 
        'LCC_w':        np.zeros((corr_matricies.shape[0], corr_matricies.shape[1]), dtype = np.float32), 
        'GCC_w':        np.zeros((corr_matricies.shape[0],), dtype = np.float32),
        'degree':       np.zeros((corr_matricies.shape[0], corr_matricies.shape[1]), dtype = np.float32), 
        'degree_w':     np.zeros((corr_matricies.shape[0], corr_matricies.shape[1]), dtype = np.float32),
        'EVC':          np.zeros((corr_matricies.shape[0], corr_matricies.shape[1]), dtype = np.float32),
        'EVC_w':        np.zeros((corr_matricies.shape[0], corr_matricies.shape[1]), dtype = np.float32),
        'closeness':    np.zeros((corr_matricies.shape[0], corr_matricies.shape[1]), dtype = np.float32),
        'closeness_w':  np.zeros((corr_matricies.shape[0], corr_matricies.shape[1]), dtype = np.float32),
    }
    parallel_execute(num_threads, compute_metrics, make_args(num_threads, result, corr_matricies))
    return result

def combine_metric_parts(config, metrics_old):
    metrics = {}
    for metric_name in metrics_old[0].keys():
        metric_name_new = str(config.network_metrics['output_network_metrics_dir'] / metric_name)
        metrics[metric_name_new] = np.concatenate([metric[metric_name] for metric in metrics_old], axis = 0)
    return metrics
