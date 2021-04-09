import numpy as np
from cyclones_info.cyclones_info import read_cyclones_file, get_cyclones, get_only_known_data, get_lat_lon_for_cyclone, \
    create_cyclone_info_string, get_datetimes_for_cycline_points


def add_local_info_for_cyclone(cyclone, local_metric_means_stds, date_times, cyclone_metric, means, stds):
    local_metric_means_stds.append([create_cyclone_info_string(cyclone)])
    local_metric_means_stds.append(['times'])
    local_metric_means_stds.append(date_times)
    local_metric_means_stds.append(['metrics'])
    local_metric_means_stds.append(cyclone_metric)
    local_metric_means_stds.append(['means'])
    local_metric_means_stds.append(means)
    local_metric_means_stds.append(['stds'])
    local_metric_means_stds.append(stds)
    return local_metric_means_stds


def compute_mean_std(config, metric):
    # metric - 3D np.ndarray (lat, lon, time)

    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['times_file_name']
    times = np.loadtxt(file_name, dtype='str', delimiter='\n')
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['lat_file_name']
    all_lat = np.loadtxt(file_name, dtype='float', delimiter='\n')
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['lon_file_name']
    all_lon = np.loadtxt(file_name, dtype='float', delimiter='\n')

    local_metric_means_stds = []

    cyclones = get_cyclones(config.local_grid_metrics_options)
    for cyclone in cyclones:
        frame = read_cyclones_file(config.local_grid_metrics_options['cyclones_file_name'], cyclone['start'][0:4])
        cyclone_frame = frame[(frame['Serial Number of system during year'] == cyclone['number']) &
                              ~(frame['Date (DD/MM/YYYY)'] == '') & ~(frame['Time (UTC)'] == '')]
        cyclone_frame = get_only_known_data(cyclone_frame)

        lons, lats = get_lat_lon_for_cyclone(cyclone_frame)
        date_times = get_datetimes_for_cycline_points(cyclone_frame)

        cyclone_metric = []
        means = []
        stds = []
        for current_lon, current_lat, current_date_time in zip(lons, lats, date_times):
            ind_dt = np.where(times == current_date_time)[0][0]
            ind_lon = np.argmin(np.abs(all_lon - current_lon))
            ind_lat = np.argmin(np.abs(all_lat - current_lat))

            cyclone_metric.append(metric[ind_lat, ind_lon, ind_dt])

            metric_for_grid_point = metric[ind_lat, ind_lon, :]
            if np.all(np.isnan(metric_for_grid_point)):
                means.append(np.nan)
                stds.append(np.nan)
            else:
                means.append(np.nanmean(metric_for_grid_point))
                stds.append(np.nanstd(metric_for_grid_point, ddof=1))

        local_metric_means_stds = add_local_info_for_cyclone(cyclone, local_metric_means_stds, date_times,
                                                             cyclone_metric, means, stds)

    local_metric_means_stds = np.asarray(local_metric_means_stds, dtype=object)

    return local_metric_means_stds
