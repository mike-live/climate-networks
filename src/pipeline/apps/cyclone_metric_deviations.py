
def make_max_deviation_metric_in_track(
        config, metric_name, metric, 
        cyclones_frame, cyclones_dict, 
        all_times, all_lons, all_lats, track_size, sign
    ):
    # Max deviation in cyclone track with track_size
    from metric_store import save_metric
    from cyclone_metrics import compute_max_deviation
    local_metric_max_deviation = compute_max_deviation(
        metric, cyclones_frame, cyclones_dict, all_times, all_lons, 
        all_lats, opt_func='max' if sign == '>' else 'min', track_size=track_size
    )
    path_to_file = "/".join(
    (
        config.cyclone_metrics_options['output_local_metrics_max_deviation_dir'] / 
        (f'track_size_{track_size}') / 
        metric_name
    ).parts)
    save_metric(config, local_metric_max_deviation, path_to_file)

def make_metric_in_track(
        config, metric_name, metric, 
        cyclones_frame, cyclones_dict, 
        all_times, all_lons, all_lats, track_size
    ):
    # All metric values in cyclone track with track_size
    from metric_store import save_metric
    from cyclone_metrics import compute_metric_in_track
    local_metric_metric_in_track = compute_metric_in_track(
        metric, cyclones_frame, cyclones_dict, 
        all_times, all_lons, all_lats, track_size=track_size
    )
    path_to_file = "/".join((
        config.cyclone_metrics_options['output_local_metric_in_track_dir'] / 
        (f'track_size_{track_size}') / 
        metric_name
    ).parts)
    save_metric(config, local_metric_metric_in_track, path_to_file)

def make_shifted_metric_in_track(
        config, metric_name, metric, 
        cyclones_frame, cyclones_dict, 
        all_times, all_lons, all_lats, track_size
    ):
    # Shifted metric values in cyclone track with track_size
    from metric_store import save_metric
    from cyclone_metrics import compute_metric_in_track
    import numpy as np
    local_metric_metric_in_track = compute_metric_in_track(
        np.roll(metric, 1000, axis=2), cyclones_frame, cyclones_dict, 
        all_times, all_lons, all_lats, track_size=track_size
    )
    path_to_file = "/".join((
        config.cyclone_metrics_options['output_local_metric_in_track_shifted_dir'] / 
            f'track_size_{track_size}' / 
            metric_name
    ).parts)
    save_metric(config, local_metric_metric_in_track, path_to_file)

def make_cyclone_metric_deviations_all(
        config, metric_names, available_mask, track_sizes,
        cyclones_frame, cyclones_dict, 
        all_times, all_lons, all_lats,
        skip_metric_name_prefix=1
    ):
    from metric_store import load_metric
    from network_metrics import prepare_metric
    from tqdm import tqdm
    from g_test_for_metrics.g_test_for_metrics import get_sign_for_metric

    for metric_name in tqdm(metric_names):
        main_metric_name = "/".join(metric_name.split("/")[skip_metric_name_prefix:])
        sign = get_sign_for_metric(config, main_metric_name)
        if sign == -1:
            print(metric_name)
            continue
        
        metric = load_metric(config, metric_name)
        metric = prepare_metric(metric_name, metric, available_mask)
        if config.metric_dimension[main_metric_name] != '2D':
            continue
        for track_size in tqdm(track_sizes):
            make_metric_in_track(
                config, metric_name, metric, 
                cyclones_frame, cyclones_dict, 
                all_times, all_lons, all_lats, track_size
            )
            make_max_deviation_metric_in_track(
                config, metric_name, metric, 
                cyclones_frame, cyclones_dict, 
                all_times, all_lons, all_lats, track_size, sign
            )
            make_shifted_metric_in_track(
                config, metric_name, metric, 
                cyclones_frame, cyclones_dict, 
                all_times, all_lons, all_lats, track_size
            )

def compute_cyclone_metric_deviation(config):
    from corr_network import load_data, get_available_mask
    from metric_store import get_metric_names
    from plot_network_metrics.utils import get_times_lats_lots
    from cyclones_info.cyclones_info import get_cyclones_info, get_cyclones, filter_cyclones_by_time
    from plot_network_metrics.utils import get_sond_times

    all_times, all_lats, all_lons = get_times_lats_lots(config)
    cyclones_frame = get_cyclones_info(config)
    cyclones_dict = get_cyclones(cyclones_frame, config.cyclone_metrics_options)

    data = load_data(config)
    available_mask = get_available_mask(data)
    track_sizes = config.g_test_options['track_sizes']
    
    prefix = ['probability_for_metrics']
    metric_names = get_metric_names(config, prefix=prefix)
    # make_cyclone_metric_deviations_all(
    #     config, metric_names, available_mask, track_sizes,
    #     cyclones_frame, cyclones_dict, 
    #     all_times, all_lons, all_lats,
    # )
    
    prefix = ['sond']
    metric_names = get_metric_names(config, prefix=prefix)
    sond_time_inds = get_sond_times(config, all_times)
    sond_times = all_times[sond_time_inds]
    cyclones_dict_sond = filter_cyclones_by_time(cyclones_dict, sond_times)
    #print(cyclones_dict_sond)

    make_cyclone_metric_deviations_all(
        config, metric_names, available_mask, track_sizes,
        cyclones_frame, cyclones_dict_sond, 
        sond_times, all_lons, all_lats,
        skip_metric_name_prefix=2
    )