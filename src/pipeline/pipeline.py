config_name = "pipeline.config"

def load_config(config_name):
    import importlib
    config = importlib.import_module(config_name)
    return config

def download_data(config):
    pass

def make_corr_networks(config, mask):
    from corr_network.corr_network import make_correlation_matricies
    return make_correlation_matricies(config, mask)

def compute_metrics(config, corr_networks):
    corr_networks = np.moveaxis(corr_networks, 2, 0)
    for i in range(corr_networks.shape[0]):
        corr_network = corr_networks[i]
        #metrics = compute_network_metrics(config, corr_network)
    
    pass

def compute_metrics_by_parts(config):
    from tqdm import tqdm
    from network_metrics import parallel_compute_metrics, combine_metric_parts
    from corr_network import load_data, get_available_mask
    from metric_store import save_metrics 
    import numpy as np
    metrics = []
    data = load_data(config)
    available_mask = get_available_mask(data)

    for id_part in tqdm(range(config.correlations['num_parts'])):
        config.correlations['id_part'] = id_part
        corr_networks = make_corr_networks(config, available_mask)
        corr_networks = np.moveaxis(corr_networks, -1, 0)
        res = parallel_compute_metrics(config, corr_networks)
        metrics += [res]
        break

    metrics = combine_metric_parts(config, metrics)
    save_metrics(config, metrics)


def compute_diff_metrics(config):
    from corr_network import load_data, get_available_mask
    from diff_metrics import parallel_compute_diff_metric
    from network_metrics import extract_metric
    from metric_store import save_metrics, save_metric, load_metrics, get_metric_names
    import numpy as np
    data = load_data(config)
    available_mask = get_available_mask(data)
    prefix = str(config.network_metrics['output_network_metrics_dir'])
    metrics = load_metrics(config, prefix = prefix)
    metric_names = get_metric_names(config, prefix = prefix)

    #diff_metrics_dir = config.diff_metrics['work_dir'] / config.diff_metrics['output_diff_metrics_dir']
    #diff_metrics_dir.mkdir(parents=True, exist_ok=True)

    for metric_name in metric_names:
        #diff_metric_file_name = diff_metrics_dir / (metric_name + '_diff.npz')
        metric = extract_metric(metrics, metric_name, available_mask)
        diff_metric = parallel_compute_diff_metric(config, metric)
        save_metric(config, diff_metric, str(config.diff_metrics['output_diff_metrics_dir'] / metric_name))


def plot_2d_metrics(config):
    from corr_network import load_data, get_available_mask
    from network_metrics import load_metrics, get_metric_names, get_metric
    data = load_data(config)
    available_mask = get_available_mask(data)
    metrics = load_metrics(config)
    metric_names = get_metric_names(metrics)
    for metric_name in metric_names:
        metric = get_metric(metrics, metric_name, available_mask)
    


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description='Climate analysis.')
    parser.add_argument('--download', dest='need_download', action='store_const',
                    const=True, default=False,
                    help='download era5 data and preprocess')
    parser.add_argument('--compute_correlations', dest='need_corr_network', action='store_const',
                    const=True, default=False,
                    help='compute correlation matricies')
    parser.add_argument('--compute_correlations_and_metrics', dest='need_correlations_and_metrics', action='store_const',
                    const=True, default=False,
                    help='plot network metrics')
    parser.add_argument('--compute_metrics', dest='need_metrics', action='store_const',
                    const=True, default=False,
                    help='compute network metrics')
    parser.add_argument('--compute_diff_metrics', dest='need_diff_metrics', action='store_const',
                    const=True, default=False,
                    help='compute diff metrics')
                    
    parser.add_argument('--plot_metrics', dest='need_plot', action='store_const',
                    const=True, default=False,
                    help='plot network metrics')

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    config = load_config(config_name)
    if args.need_download:
        download_data(config)

    if args.need_corr_network:
        make_corr_networks(config)

    if args.need_metrics:
        compute_metrics(config)

    if args.need_diff_metrics:
        compute_diff_metrics(config)

    if args.need_correlations_and_metrics:
        compute_metrics_by_parts(config)

    if args.need_plot:
        plot_2d_metrics(config)