from .apps import *

config_name = "pipeline.config"


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
    parser.add_argument('--add_input_data', dest='need_input_data', action='store_const',
                    const=True, default=False,
                    help='add input data to metric store')
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

    parser.add_argument('--compute_cyclone_events', dest='need_cyclone_events', action='store_const',
                        const=True, default=False,
                        help='compute cyclone events')

    parser.add_argument('--compute_metrics_probability', dest='need_compute_metrics_probability', action='store_const',
                        const=True, default=False,
                        help='compute metrics probability')

    parser.add_argument('--compute_g_test_for_metrics', dest='need_compute_g_test_for_metrics', action='store_const',
                        const=True, default=False,
                        help='compute g-test for metrics')

    parser.add_argument('--compute_optimal_thr_for_g_test', dest='need_compute_optimal_thr_for_g_test', action='store_const',
                        const=True, default=False,
                        help='compute optimal threshold for g-test')

    parser.add_argument('--compute_cyclone_metric_deviation', dest='need_compute_cyclone_metric_deviation', action='store_const',
                        const=True, default=False,
                        help='compute cyclone metric maximal deviation over region')
    parser.add_argument('--plot_local_grid_cyclone_metric_deviation', dest='need_plot_local_grid_cyclone_metric_deviation', action='store_const',
                        const=True, default=False,
                        help='plot cyclone metric maximal deviation over region')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    config = load_config(config_name)
    if args.need_download:
        download_data(config)

    if args.need_input_data:
        add_input_data_to_metric(config)

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

    if args.need_cyclone_events:
        compute_cyclone_events(config)

    if args.need_compute_metrics_probability:
        compute_metrics_probability(config)

    if args.need_compute_g_test_for_metrics:
        compute_g_test(config)

    if args.need_compute_optimal_thr_for_g_test:
        compute_optimal_g_test_results(config)

    if args.need_compute_cyclone_metric_deviation:
        compute_cyclone_metric_deviation(config)

    if args.need_plot_local_grid_cyclone_metric_deviation:
        plot_local_grid_cyclone_metric_deviation(config)
