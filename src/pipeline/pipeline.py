from .apps import *

def load_config(config_name):
    import importlib
    config = importlib.import_module(config_name)
    return config

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

    parser.add_argument('--compute_cyclone_metrics', dest='need_cyclone_metrics', action='store_const',
                    const=True, default=False,
                    help='compute cyclone metrics')

    parser.add_argument('--plot_cyclone_metrics', dest='need_plot_cyclone_metrics', action='store_const',
                    const=True, default=False,
                    help='plot cyclone metrics')

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
        plot_metrics(config)

    if args.need_cyclone_metrics:
        compute_cyclone_metrics(config)

    if args.need_plot_cyclone_metrics:
        plot_local_grid_cyclone_metrics(config)