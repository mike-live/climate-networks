import numpy as np
from datetime import timedelta, datetime


def get_times_lats_lots(config):
    # metric - 3D np.ndarray (lat, lon, time)
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['times_file_name']
    times = np.loadtxt(file_name, dtype='str', delimiter='\n')
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['lat_file_name']
    lats = np.loadtxt(file_name, dtype='float', delimiter='\n')
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['lon_file_name']
    lons = np.loadtxt(file_name, dtype='float', delimiter='\n')
    return times, lats, lons

def get_times_subset(all_times, months=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]):
    selected_time_inds = [ind for ind, time in enumerate(all_times) if int(time[5:7]) in months]
    return selected_time_inds

def get_sond_times(config, all_times):
    return get_times_subset(all_times, months=config.prob_metrics["sond_months"])

def get_considered_years(config):
    start_year = int(config.metrics_plot_options['start_time'][0:4])
    end_year = int(config.metrics_plot_options['end_time'][0:4])
    years = list(range(start_year, end_year + 1))
    return years


def get_considered_times(config):
    considered_times = []
    start_date = datetime.strptime(config.metrics_plot_options['start_time'], '%Y.%m.%d %H:%M:%S')
    end_date = datetime.strptime(config.metrics_plot_options['end_time'], '%Y.%m.%d %H:%M:%S')
    d = start_date
    delta = timedelta(hours=config.metrics_plot_options['step_time_in_hours'])
    while d <= end_date:
        considered_times.append(d.strftime("%Y.%m.%d %H:%M:%S"))
        d += delta
    return considered_times


def get_considered_times_for_cyclone(cyclone, config):
    considered_times = []

    start_date = datetime.strptime(cyclone['start'], '%Y.%m.%d %H:%M:%S') - \
                 timedelta(hours=3*config.cyclones_plot_options['n_3h_intervals_before_after'])
    end_date = datetime.strptime(cyclone['end'], '%Y.%m.%d %H:%M:%S') + \
                 timedelta(hours=3*config.cyclones_plot_options['n_3h_intervals_before_after'])

    d = start_date
    delta = timedelta(hours=3)
    while d <= end_date:
        considered_times.append(d.strftime("%Y.%m.%d %H:%M:%S"))
        d += delta

    return considered_times


def get_run_time_images_dir_name_for_metrics(config):
    start_time_plot = datetime.strptime(config.metrics_plot_options['start_time'],
                                        '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d-%H-%M-%S')
    end_time_plot = datetime.strptime(config.metrics_plot_options['end_time'],
                                      '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d-%H-%M-%S')

    if config.metric_dimension[config.metrics_plot_options['metric_name']] == '2D':
        run_time_dir_name = config.metrics_plot_options['metric_name'] + '_' + start_time_plot + '_' \
                            + end_time_plot + '_' + str(config.metrics_plot_options['step_time_in_hours']) + 'h'

    elif config.metric_dimension[config.metrics_plot_options['metric_name']] == '1D':
        if config.metrics_plot_options['time_split'] == 'years':
            start_time_plot = start_time_plot[0:4]
            end_time_plot = end_time_plot[0:4]
        elif config.metrics_plot_options['time_split'] == 'months':
            start_time_plot = start_time_plot[0:7]
            end_time_plot = end_time_plot[0:7]

        run_time_dir_name = config.metrics_plot_options['metric_name'] + '_' + start_time_plot + '_' \
                            + end_time_plot + '_' + str(config.metrics_plot_options['time_split'])

    return run_time_dir_name


def get_run_time_images_dir_name_for_cyclones(config):
    start_date = datetime.strptime(config.cyclones_plot_options['start_time'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d')
    end_date = datetime.strptime(config.cyclones_plot_options['end_time'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d')
    run_time_dir_name = 'cyclones_' + start_date + '_' + end_date
    run_time_dir_name = ''
    return run_time_dir_name

def create_cyclone_dir(config, cyclone, images_dir):
    dir_name = str(cyclone['start'][0:4]) + '_cyclone_' + cyclone['number'].split('_')[0] + '_'
    dir_name += datetime.strptime(cyclone['start'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d') + '_' \
                + datetime.strptime(cyclone['end'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d')
    cyclone_metric_dir = images_dir / dir_name
    return cyclone_metric_dir


def create_cyclone_metric_dir(config, cyclone, images_dir):
    cyclone_metric_dir = create_cyclone_dir(config, cyclone, images_dir) / config.metrics_plot_options['metric_name']
    cyclone_metric_dir.mkdir(parents=True, exist_ok=True)
    return cyclone_metric_dir


def create_dir(config):
    if config.plotting_mode['metrics']:
        images_dir = config.metrics_plot_options['work_dir'] / config.metrics_plot_options['images_dir']
        images_subdir = images_dir / get_run_time_images_dir_name_for_metrics(config)
    elif config.plotting_mode['cyclones'] and config.plotting_mode['metrics'] == False:
        images_dir = config.cyclones_plot_options['work_dir'] / config.cyclones_plot_options['images_dir']
        images_subdir = images_dir / get_run_time_images_dir_name_for_cyclones(config)
    images_subdir.mkdir(parents=True, exist_ok=True)
    return images_subdir
