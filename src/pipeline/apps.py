def download_data(config):
    from metric_store import add_metric
    from download_data.download_ERA5_data import download_and_preprocessing_ERA5_data
    download_and_preprocessing_ERA5_data(config)
    #add_metric(config, 'input_data/MSLP', config.download_ERA5_options['work_dir'] / config.download_ERA5_options['res_cube_land_masked_file_name'])
    #add_metric(config, 'input_data/MSLP_preproc', config.download_ERA5_options['work_dir'] / config.download_ERA5_options['res_cube_land_masked_and_preproc_file_name'])


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
    prefix = [str(config.network_metrics['output_network_metrics_dir']), 'input_data']
    metrics = load_metrics(config, prefix=prefix)
    metric_names = get_metric_names(config, prefix=prefix)

    #diff_metrics_dir = config.diff_metrics['work_dir'] / config.diff_metrics['output_diff_metrics_dir']
    #diff_metrics_dir.mkdir(parents=True, exist_ok=True)

    for metric_name in metric_names:
        #diff_metric_file_name = diff_metrics_dir / (metric_name + '_diff.npz')
        metric = extract_metric(metrics, metric_name, available_mask)
        diff_metric = parallel_compute_diff_metric(config, metric)
        save_metric(config, diff_metric, "/".join((config.diff_metrics['output_diff_metrics_dir'] / metric_name).parts))


def plot_metrics(config):
    from corr_network import load_data, get_available_mask
    from network_metrics import prepare_metric
    from metric_store import get_metric_names, load_metric
    from plot_network_metrics.plot_network_metrics import plot_2d_metric_on_map, plot_1d_metric_from_time
    from plot_network_metrics.utils import create_dir, create_cyclone_metric_dir, \
        get_considered_times, get_considered_times_for_cyclone
    from cyclones_info.cyclones_info import get_cyclones_info, get_cyclones, update_config_for_plot_cyclone
    from tqdm import tqdm

    data = load_data(config)
    available_mask = get_available_mask(data)

    cyclones_frame = get_cyclones_info(config)

    if config.metrics_plot_options['metric_names'] is None:
        #config.metrics_plot_options['metric_names'] = get_metric_names(config)
        prefixes = ['network_metrics', 'input_data', 'diff_metrics']
        config.metrics_plot_options['metric_names'] = get_metric_names(config, prefixes)

    if config.plotting_mode['metrics']:
        considered_times = get_considered_times(config)
        for metric_name in tqdm(config.metrics_plot_options['metric_names']):
            config.metrics_plot_options['metric_name'] = metric_name
            metric_dir = create_dir(config)
            metric = load_metric(config, metric_name)
            metric = prepare_metric(metric_name, metric, available_mask)
            print()
            print(metric_name, metric.shape)
            if config.metric_dimension[metric_name] == '2D':
                empty_dict = dict.fromkeys(['start', 'end', 'number', 'name'], '')
                plot_2d_metric_on_map(metric, considered_times, config, metric_dir, cyclones_frame, empty_dict)
            elif config.metric_dimension[metric_name] == '1D':
                plot_1d_metric_from_time(metric, considered_times, config, metric_dir)

    elif config.plotting_mode['cyclones'] and config.plotting_mode['metrics'] == False:
        cyclones = get_cyclones(cyclones_frame, config.cyclones_plot_options)
        cyclones_dir = create_dir(config)
        for cyclone in tqdm(cyclones):
            print('\ncyclone:', cyclone)
            considered_times = get_considered_times_for_cyclone(cyclone, config)
            update_config_for_plot_cyclone(config, cyclone)
            for metric_name in config.metrics_plot_options['metric_names']:
                config.metrics_plot_options['metric_name'] = metric_name
                cyclone_metric_dir = create_cyclone_metric_dir(config, cyclone, cyclones_dir)
                metric = load_metric(config, metric_name)
                metric = prepare_metric(metric_name, metric, available_mask)
                print(metric_name, metric.shape)
                if config.metric_dimension[metric_name] == '2D':
                    plot_2d_metric_on_map(metric, considered_times, config, cyclone_metric_dir, cyclones_frame, cyclone)
                elif config.metric_dimension[metric_name] == '1D':
                    plot_1d_metric_from_time(metric, considered_times, config, cyclone_metric_dir)


def compute_cyclone_metrics(config):
    from corr_network import load_data, get_available_mask
    from metric_store import get_metric_names, save_metric, load_metric
    from network_metrics import prepare_metric
    from plot_network_metrics.utils import get_times_lats_lots  ###
    from cyclones_info.cyclones_info import get_cyclones_info, get_cyclones
    from cyclone_metrics import compute_mean_std
    from tqdm import tqdm

    all_times, all_lats, all_lons = get_times_lats_lots(config)
    cyclones_frame = get_cyclones_info(config)
    cyclones_dict = get_cyclones(cyclones_frame, config.cyclone_metrics_options)

    data = load_data(config)
    available_mask = get_available_mask(data)
    prefix = ['diff_metrics', 'network_metrics', 'input_data']
    metric_names = get_metric_names(config, prefix=prefix)

    for metric_name in tqdm(metric_names):
        metric = load_metric(config, metric_name)
        metric = prepare_metric(metric_name, metric, available_mask)
        if config.metric_dimension[metric_name] == '2D':
            local_metric_means_stds = compute_mean_std(metric, cyclones_dict, cyclones_frame,
                                                       all_times, all_lons, all_lats)
            path_to_file = "/".join((config.cyclone_metrics_options['output_local_metrics_dir'] / metric_name).parts)
            save_metric(config, local_metric_means_stds, path_to_file)
            #local_metric_means_stds = load_metric(config, path_to_file)


def plot_local_grid_cyclone_metrics(config):
    from plot_network_metrics.utils import create_dir, create_cyclone_metric_dir, create_cyclone_dir
    from metric_store import get_metric_names, save_metric, load_metric
    from network_metrics import prepare_metric
    from corr_network import load_data, get_available_mask
    from tqdm import tqdm
    import numpy as np

    data = load_data(config)
    available_mask = get_available_mask(data)

    from plot_network_metrics.utils import get_times_lats_lots
    from cyclones_info.cyclones_info import get_cyclones_info, get_cyclones
    all_times, all_lats, all_lons = get_times_lats_lots(config)
    cyclones_frame = get_cyclones_info(config)
    cyclones_dict = get_cyclones(cyclones_frame, config.cyclone_metrics_options)

    cyclones_dir = create_dir(config)
    metric_names = list(get_metric_names(config, prefix='local_grid_metrics_for_cyclones').keys())
    for metric_name in tqdm(metric_names):
        config.metrics_plot_options['metric_name'] = metric_name
        metric = load_metric(config, metric_name)
        metric = prepare_metric(metric_name, metric, available_mask).item()
        print(metric_name, len(metric))
        from plot_network_metrics.plot_cyclone_metrics import plot_local_grid_metric, plot_metric_probability
        for cid, (cyclone, (cyclone_name, cur_cyclone_metric)) in enumerate(zip(cyclones_dict, metric.items())):
            if np.sum(~np.isnan(cur_cyclone_metric['metrics'])) < 4:
                continue
            cyclone_metric_dir = create_cyclone_dir(config, cyclone, cyclones_dir)
            plot_local_grid_metric(cur_cyclone_metric, metric_name, image_path=cyclone_metric_dir)
            if config.cyclone_metrics_options['plot_probability']:
                plot_metric_probability(cur_cyclone_metric, metric_name, image_path=cyclone_metric_dir)
        del metric
