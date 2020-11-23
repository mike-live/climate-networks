config_name = "pipeline.config"

def load_config(config_name):
    import importlib
    config = importlib.import_module(config_name)
    return config

def download_data(config):
    pass

def make_corr_networks(config):
    from corr_network.corr_network import make_correlation_matricies
    return make_correlation_matricies(config)

def compute_metrics(config, corr_networks):
    corr_networks = np.moveaxis(corr_networks, 2, 0)
    for i in range(corr_networks.shape[0]):
        corr_network = corr_networks[i]
        #metrics = compute_network_metrics(config, corr_network)
    
    pass

def compute_metrics_by_parts(config):
    from tqdm import tqdm
    from network_metrics.compute_metrics import parallel_compute_metrics
    import numpy as np
    metrics = []
    for id_part in tqdm(range(1)): # config.correlations['num_parts']
        config.correlations['id_part'] = id_part
        corr_networks = make_corr_networks(config)
        corr_networks = np.moveaxis(corr_networks, -1, 0)
        metrics += parallel_compute_metrics(config, corr_networks[-2:])
    print(len(metrics))
    print(metrics[0])
    metrics_file_name = config.network_metrics['work_dir'] / config.network_metrics['output_metrics_file_name']
    np.save(metrics_file_name, metrics)

def plot_2d_metrics(config):
    pass

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

    if args.need_correlations_and_metrics:
        compute_metrics_by_parts(config)

    if args.need_plot:
        plot_2d_metrics(config)