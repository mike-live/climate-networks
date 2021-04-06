import numpy as np
from datetime import datetime
from plot_network_metrics.plot_cyclones import get_cyclones, get_only_known_data, get_lat_lon_for_cyclone
from plot_network_metrics.utils import read_cyclones_file


def get_datetimes_for_cycline_points(df):
    date_times = []
    for ind, row in df.iterrows():
        if row['Date (DD/MM/YYYY)'] != '' and row['Time (UTC)'] != '':
            ct = datetime.strptime(row['Date (DD/MM/YYYY)'] + ' ' + row['Time (UTC)'], '%d/%m/%Y %H%M')
            date_times.append(ct.strftime('%Y.%m.%d %H:%M:%S'))
    return date_times


def create_cyclone_name(cyclone):
    name = str(cyclone['start'][0:4]) + '_cyclone_' + str(cyclone['number']) + '_' + cyclone['name'] + '_'\
           + datetime.strptime(cyclone['start'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d') + '_' \
           + datetime.strptime(cyclone['end'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d')
    return name


def add_local_metrics_means_stds(cyclone, local_metrics_means_stds, cyclone_metric, means, stds):
    local_metrics_means_stds.append(create_cyclone_name(cyclone))
    local_metrics_means_stds.append(['metrics'])
    local_metrics_means_stds.append(cyclone_metric)
    local_metrics_means_stds.append(['means'])
    local_metrics_means_stds.append(means)
    local_metrics_means_stds.append(['stds'])
    local_metrics_means_stds.append(stds)
    return local_metrics_means_stds


def compute_mean_std(config, metric_name, metric):
    # metric - 3D np.ndarray (lat, lon, time)

    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['times_file_name']
    times = np.loadtxt(file_name, dtype='str', delimiter='\n')
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['lat_file_name']
    all_lat = np.loadtxt(file_name, dtype='float', delimiter='\n')
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['lon_file_name']
    all_lon = np.loadtxt(file_name, dtype='float', delimiter='\n')

    local_metrics_means_stds = []

    cyclones = get_cyclones(config.local_metrics_options) ##############
    for cyclone in cyclones:
        frame = read_cyclones_file(config.local_metrics_options['cyclones_file_name'], cyclone['start'][0:4])
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

            #print(current_date_time, '->', ind_dt)
            #print(current_lat, '->', ind_lat, '->', all_lat[ind_lat], '\t', current_lon, '->', ind_lon, '->', all_lon[ind_lon])

            means.append(np.nanmean(metric[ind_lat, ind_lon, :]))
            stds.append(np.nanstd(metric[ind_lat, ind_lon, :], ddof=1))

        #print('\n')

        local_metrics_means_stds = add_local_metrics_means_stds(cyclone, local_metrics_means_stds,
                                                                cyclone_metric, means, stds)

    with open('djdjsj.txt', 'w') as file_handler:
        for item in local_metrics_means_stds:
            file_handler.write("{}\n".format(item))

