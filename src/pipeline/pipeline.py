config_name = "pipeline.config"

def load_config(config_name):
    import importlib
    config = importlib.import_module(config_name)
    return config

def download_data(config):
    from metric_store import add_metric
    #from download_data.download_ERA5_data import download_and_preprocessing_ERA5_data
    #download_and_preprocessing_ERA5_data(config.download_ERA5_options)
    add_metric(config, 'input_data/MSLP', config.download_ERA5_options['work_dir'] / config.download_ERA5_options['res_cube_land_masked_and_preproc_file_name'])


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
        save_metric(config, diff_metric, "/".join((config.diff_metrics['output_diff_metrics_dir'] / metric_name).parts))


def plot_metrics(config):
    from corr_network import load_data, get_available_mask
    from network_metrics import extract_metric, prepare_metric
    from metric_store import load_metrics, get_metric_names, load_metric
    from plot_network_metrics.plot_network_metrics import plot_2d_metric_on_map, plot_1d_metric_from_time
    from plot_network_metrics.utils import create_dir, create_cyclone_metric_dir, \
        get_considered_times, get_considered_times_for_cyclone, update_config_for_plot_cyclone
    from plot_network_metrics.plot_cyclones import get_cyclones
    from tqdm import tqdm

    data = load_data(config)
    available_mask = get_available_mask(data)
    #metrics = load_metrics(config)

    if config.metrics_plot_options['metric_names'] is None:
        config.metrics_plot_options['metric_names'] = get_metric_names(config)

    if config.plotting_mode['metrics']:
        considered_times = get_considered_times(config)
        for metric_name in config.metrics_plot_options['metric_names']:
            config.metrics_plot_options['metric_name'] = metric_name
            metric_dir = create_dir(config)
            metric = load_metric(config, metric_name)
            metric = prepare_metric(metric_name, metric, available_mask)
            print(metric_name, metric.shape)
            if config.metric_dimension[metric_name] == '2D':
                empty_dict = dict.fromkeys(['start', 'end', 'number', 'name'], '')
                plot_2d_metric_on_map(metric, considered_times, config, metric_dir, empty_dict)
            elif config.metric_dimension[metric_name] == '1D':
                plot_1d_metric_from_time(metric, considered_times, config, metric_dir)

    elif config.plotting_mode['cyclones'] and config.plotting_mode['metrics'] == False:
        cyclones = get_cyclones(config)
        cyclones_dir = create_dir(config)
        for cyclone in tqdm(cyclones):
            print('\ncyclone:', cyclone)
            considered_times = get_considered_times_for_cyclone(cyclone, config)
            update_config_for_plot_cyclone(config, cyclone)
            for metric_name in config.metrics_plot_options['metric_names']:
                config.metrics_plot_options['metric_name'] = metric_name
                cyclone_metric_dir = create_cyclone_metric_dir(config, cyclone, cyclones_dir)
                metric = load_metric(config, metric_name)
                print(metric.shape)
                metric = prepare_metric(metric_name, metric, available_mask)
                print(metric.shape)
                if config.metric_dimension[metric_name] == '2D':
                    plot_2d_metric_on_map(metric, considered_times, config, cyclone_metric_dir, cyclone)
                elif config.metric_dimension[metric_name] == '1D':
                    plot_1d_metric_from_time(metric, considered_times, config, cyclone_metric_dir)


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
        plot_metrics(config)
