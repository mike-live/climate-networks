from datetime import timedelta, datetime
import pandas as pd
import numpy as np
import os


def is_float(st):
    try:
        float(st)
        return True
    except ValueError:
        return False


def delete_empty_rows(frame):
    new_frame = frame.copy()
    for ind, row in frame.iterrows():
        if new_frame.loc[ind].isna().values.all():
            new_frame.drop([ind], inplace=True)
    new_frame.index = range(0, len(new_frame))
    return new_frame


def convert_time_in_cyclone_frame(frame):
    new_frame = frame.copy()
    new_frame['Time (UTC)'] = new_frame['Time (UTC)'].apply(lambda x:
                                                            '' if x == ''
                                                            else (x.zfill(4)
                                                                  if type(x) is str
                                                                  else ('' if np.isnan(x)
                                                                        else '{:04d}'.format(int(x)))))
    return new_frame


def read_cyclones_file(file_name, sheet_name):
    frame = pd.read_excel(file_name, sheet_name=sheet_name)
    frame = delete_empty_rows(frame)
    frame = convert_time_in_cyclone_frame(frame)
    frame.fillna('', inplace=True)
    return frame


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
    considered_times = [datetime.strptime(cyclone['start'], '%Y.%m.%d %H:%M:%S') - timedelta(hours=(i + 1) * 3)
                        for i in range(0, config.cyclones_plot_options['n_3h_intervals_before_after'])]
    considered_times = considered_times[::-1]

    sheet_name = cyclone['start'][0:4]
    frame = read_cyclones_file(config.cyclones_plot_options['cyclones_file_name'], sheet_name)
    sub_frame = frame[frame['Serial Number of system during year'] == cyclone['number']]
    for ind, row in sub_frame.iterrows():
        if row['Date (DD/MM/YYYY)'] != '' and row['Time (UTC)'] != '':
            ct = datetime.strptime(row['Date (DD/MM/YYYY)'] + ' ' + row['Time (UTC)'], '%d/%m/%Y %H%M')
            considered_times.append(ct)

    considered_times += [datetime.strptime(cyclone['end'], '%Y.%m.%d %H:%M:%S') + timedelta(hours=(i + 1) * 3)
                         for i in range(0, config.cyclones_plot_options['n_3h_intervals_before_after'])]
    considered_times = [t.strftime('%Y.%m.%d %H:%M:%S') for t in considered_times]

    return considered_times


def update_config_for_plot_cyclone(config, cyclone):
    config.metrics_plot_options['start_time'] = cyclone['start']
    config.metrics_plot_options['end_time'] = cyclone['end']
    config.metrics_plot_options['time_split'] = None
    config.metrics_plot_options['plot_cyclones'] = True


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
    return run_time_dir_name


def create_cyclone_metric_dir(config, cyclone, images_dir):
    dir_name = str(cyclone['start'][0:4]) + '_cyclone_' + str(cyclone['number']) + '_'
    dir_name += datetime.strptime(cyclone['start'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d') + '_' \
                + datetime.strptime(cyclone['end'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d')
    cyclone_dir = images_dir / dir_name
    if not os.path.isdir(cyclone_dir):
        os.mkdir(cyclone_dir)
    cyclone_metric_dir = cyclone_dir / config.metrics_plot_options['metric_name']
    if not os.path.isdir(cyclone_metric_dir):
        os.mkdir(cyclone_metric_dir)
    return cyclone_metric_dir


def create_dir(config):
    if config.plotting_mode['metrics']:
        images_dir = config.metrics_plot_options['work_dir'] / config.metrics_plot_options['images_dir']
        images_subdir = images_dir / get_run_time_images_dir_name_for_metrics(config)
    elif config.plotting_mode['cyclones'] and config.plotting_mode['metrics'] == False:
        images_dir = config.cyclones_plot_options['work_dir'] / config.cyclones_plot_options['images_dir']
        images_subdir = images_dir / get_run_time_images_dir_name_for_cyclones(config)
    if not os.path.isdir(images_dir):
        os.mkdir(images_dir)
    if not os.path.isdir(images_subdir):
        os.mkdir(images_subdir)
    return images_subdir
