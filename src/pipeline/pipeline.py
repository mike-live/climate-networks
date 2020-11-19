config_name = "pipeline.config"

def load_config(config_name):
    import importlib
    config = importlib.import_module(config_name)
    return config

def download_data(config):
    pass

def make_corr_networks(config):
    from corr_network.corr_network import make_correlation_matricies
    make_correlation_matricies(config)

def compute_metrics(config):
    pass

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

    if args.need_plot:
        plot_2d_metrics(config)