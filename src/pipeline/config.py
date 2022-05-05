from pathlib2 import Path
from .config_project import project_data_dir

download_ERA5_options = {
    'work_dir': '',
    'lat_file_name': 'lat.txt',
    'lon_file_name': 'lon.txt',
    'times_file_name': 'times.txt',
    'res_cube_file_name': 'resulting_cube.npz',
    'res_cube_land_masked_file_name': 'resulting_cube_land_masked.npz',
    'res_cube_preproc_file_name': 'resulting_cube_preproc.npz',
    'res_cube_land_masked_and_preproc_file_name': 'resulting_cube_land_masked_and_preproc.npz',
    'variable': 'mean_sea_level_pressure',   #'mean_sea_level_pressure' or 'sea_surface_temperature'
    'name_var': 'msl',                       #'msl' or 'sst'
    'land_mask': True,
    'preprocessing': True,
    'start_year': 1982,
    'end_year': 2020,
    'start_month': 1,
    'end_month': 12,
    'start_day': 1,
    'end_day': 31,
    'start_time': 0,
    'end_time': 21,
    'step_time': 3,
    'north': 30.75,
    'west': 49.5,
    'south': 4.5,
    'east': 100.5,
    'resolution': 0.75,
}

work_dir = project_data_dir / 'ERA5' / '_'.join(['ERA5',
                                                         download_ERA5_options['name_var'].upper(),
                                                         str(download_ERA5_options['start_year']),
                                                         str(download_ERA5_options['end_year']),
                                                         str(download_ERA5_options['step_time']) + 'h',
                                                         str(download_ERA5_options['resolution'])])
download_ERA5_options['work_dir'] = work_dir

correlations = {
    'work_dir': download_ERA5_options['work_dir'],
    'input_file_name': download_ERA5_options['res_cube_land_masked_and_preproc_file_name'],
    'input_var_name': 'arr_0',
    'delay_time': 0,
    'window_size': 8 * 2,
    'num_threads': 85,
    'need_save': False,
    'num_parts': 666,
    'id_part': 1,
    'output_level': 1,
}

prefix_for_preproc_data = 'land_masked_and_preproc'
prefix_for_corr = f'window_{correlations["window_size"] // 8}d_delay_{correlations["delay_time"] // 8}d'
correlations['output_correlation_file_name'] = 'corr_online_' + 'land_masked_and_preproc' + '_' + prefix_for_corr + '.npy'


metrics = {
    'work_dir': correlations['work_dir'],
    'output_metrics_dir': 'metrics_corr_' + 'land_masked_and_preproc' + '_' + prefix_for_corr,
    'metric_names_file_name': 'metric_names.npy',
}

network_metrics = {
    'num_threads': 84,
    'work_dir': correlations['work_dir'] / metrics['output_metrics_dir'],
    'output_network_metrics_dir': Path('network_metrics'),
    'corr_thrs': [None, 0.9, 0.95],
}

diff_metrics = {
    'num_threads': 2,
    'work_dir': correlations['work_dir'] / metrics['output_metrics_dir'],
    'output_diff_metrics_dir': Path('diff_metrics'),
}


cyclones_info = {
    'cyclones_file_name': 'tropical_cyclones_data_1982_2020.csv',
}

plotting_mode = {
    'metrics': False,
    'cyclones': True,
}

metrics_plot_options = {
    'work_dir': download_ERA5_options['work_dir'],
    'cyclones_file_name': cyclones_info['cyclones_file_name'],
    'metric_name': 'LCC',
    'metric_names': None,
    'time_split': None,    # 'years', 'months', None
    'images_dir': 'images',
    'start_time': '2004.09.29 00:00:00',
    'end_time': '2004.10.05 00:00:00',
    'step_time_in_hours': 24,
    'dpi': 200,
    'scaling_by_selected_data': False,
    'plot_cyclones': True,
}

cyclones_plot_options = {
    'work_dir': download_ERA5_options['work_dir'],
    'cyclones_file_name': cyclones_info['cyclones_file_name'],
    'images_dir': 'cyclones',
    'start_time': '1982.11.27 00:00:00',
    'end_time': '1982.11.30 00:00:00',
    'n_3h_intervals_before_after': 2 * 8, 
}

cyclone_metrics_options = {
    'work_dir': download_ERA5_options['work_dir'],
    'cyclones_file_name': cyclones_info['cyclones_file_name'],
    'output_local_metrics_dir': Path('local_grid_metrics_for_cyclones'),
    'output_local_metrics_max_deviation_dir': Path('lgm_deviation_for_cyclones'),
    'start_time': '1982.01.01 00:00:00',
    'end_time': '2020.12.31 21:00:00',
    'plot_probability': True,
}

import numpy as np

g_test_options = {
    'need_surrogate': True,
    'thr': np.linspace(0, 1, 101),  # threshold list for metric indication
    #'thr': [0.0, 0.25, 0.5, 0.75, 1.0],  # threshold list for metric indication
    #'thr': [0.001],
    'track_size': 8,
    'track_sizes': [2, 4, 6, 8, 10, 12], #
    'less': ['network_metrics/LCC', 'network_metrics/LCC_w', 'network_metrics/closeness_w', 'network_metrics/LCC_0.9',
             'network_metrics/LCC_0.95', 'diff_metrics/network_metrics/LCC', 'diff_metrics/network_metrics/LCC_w',
             'diff_metrics/network_metrics/LCC_0.9', 'diff_metrics/network_metrics/LCC_0.95',
             'diff_metrics/network_metrics/closeness_w'],
    'greater': ['network_metrics/degree', 'network_metrics/degree_w', 'network_metrics/EVC', 'network_metrics/EVC_w',
                'network_metrics/closeness', 'network_metrics/degree_0.9', 'network_metrics/EVC_0.9',
                'network_metrics/closeness_0.9', 'network_metrics/degree_0.95', 'network_metrics/EVC_0.95',
                'network_metrics/closeness_0.95', 'input_data/MSLP', 'input_data/MSLP_preproc', 'input_data/MSLP_land',
                'diff_metrics/input_data/MSLP', 'diff_metrics/input_data/MSLP_preproc', 'diff_metrics/input_data/MSLP_land',
                'diff_metrics/network_metrics/degree', 'diff_metrics/network_metrics/degree_w',
                'diff_metrics/network_metrics/EVC', 'diff_metrics/network_metrics/EVC_w',
                'diff_metrics/network_metrics/closeness', 'diff_metrics/network_metrics/degree_0.9',
                'diff_metrics/network_metrics/degree_0.95', 'diff_metrics/network_metrics/EVC_0.9',
                'diff_metrics/network_metrics/EVC_0.95', 'diff_metrics/network_metrics/closeness_0.9',
                'diff_metrics/network_metrics/closeness_0.95']
}

metric_dimension = {
    'network_metrics/LCC':         '2D',
    'network_metrics/GCC':         '1D',
    'network_metrics/degree':      '2D',
    'network_metrics/EVC':         '2D',
    'network_metrics/closeness':   '2D',

    'network_metrics/degree_w':    '2D',
    'network_metrics/LCC_w':       '2D',
    'network_metrics/GCC_w':       '1D',
    'network_metrics/EVC_w':       '2D',
    'network_metrics/closeness_w': '2D',

    'network_metrics/LCC_0.9':         '2D',
    'network_metrics/GCC_0.9':         '1D',
    'network_metrics/degree_0.9':      '2D',
    'network_metrics/EVC_0.9':         '2D',
    'network_metrics/closeness_0.9':   '2D',

    'network_metrics/LCC_0.95':         '2D',
    'network_metrics/GCC_0.95':         '1D',
    'network_metrics/degree_0.95':      '2D',
    'network_metrics/EVC_0.95':         '2D',
    'network_metrics/closeness_0.95':   '2D',

    'diff_metrics/network_metrics/LCC':            '2D',
    'diff_metrics/network_metrics/GCC':            '1D',
    'diff_metrics/network_metrics/degree':         '2D',
    'diff_metrics/network_metrics/EVC':            '2D',
    'diff_metrics/network_metrics/closeness':      '2D',

    'diff_metrics/network_metrics/LCC_w':          '2D',
    'diff_metrics/network_metrics/GCC_w':          '1D',
    'diff_metrics/network_metrics/degree_w':       '2D',
    'diff_metrics/network_metrics/EVC_w':          '2D',
    'diff_metrics/network_metrics/closeness_w':    '2D',

    'diff_metrics/network_metrics/LCC_0.9':            '2D',
    'diff_metrics/network_metrics/GCC_0.9':            '1D',
    'diff_metrics/network_metrics/degree_0.9':         '2D',
    'diff_metrics/network_metrics/EVC_0.9':            '2D',
    'diff_metrics/network_metrics/closeness_0.9':      '2D',

    'diff_metrics/network_metrics/LCC_0.95':            '2D',
    'diff_metrics/network_metrics/GCC_0.95':            '1D',
    'diff_metrics/network_metrics/degree_0.95':         '2D',
    'diff_metrics/network_metrics/EVC_0.95':            '2D',
    'diff_metrics/network_metrics/closeness_0.95':      '2D',

    'input_data/MSLP':             '2D',
    'input_data/MSLP_preproc':     '2D',
    'input_data/MSLP_land':        '2D',

    'diff_metrics/input_data/MSLP':             '2D',
    'diff_metrics/input_data/MSLP_preproc':     '2D',
    'diff_metrics/input_data/MSLP_land':        '2D',
}

debug_level = 1
