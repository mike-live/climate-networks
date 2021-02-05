from pathlib2 import Path

import os
print(os.getcwd())

correlations = {
    'work_dir': Path(r'ERA5/ERA5_MSLP_1982_2019_3h_0.75'),
    'input_file_name': 'resulting_cube_land_masked_after_preproc_ERA5_MSLP_1982_2019_3h_0.75.npz',
    'input_var_name': 'arr_0',
    'output_correlation_file_name': 'corr_online_preproc_ERA5_MSLP_1982_2019_3h_0.75_window_10d_delay_0d.npy',
#    'output_correlation_var_name': 'result',
    'delay_time': 0,
    'window_size': 80,
    'num_threads': 85,
    'need_save': False,
    'num_parts': 666,
    'id_part': 1,
    'output_level': 1,
}

network_metrics = {
    'num_threads': 84,
    'work_dir': correlations['work_dir'],
    'output_metrics_file_name': 'metrics_corr_land_masked_ERA5_MSLP_1982_2019_3h_0.75_window_10d_delay_0d.npy',
}

download_ERA5_options = {
    'work_dir': Path(r'ERA5/ERA5_MSLP_1982_2019_3h_0.75'),
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
    'end_year': 2019,
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

plotting_mode = {
    'metrics': False,
    'cyclones': True,
}

metrics_plot_options = {
    'work_dir': download_ERA5_options['work_dir'],
    'metric_name': 'LCC',
    'metric_names': ['LCC', 'GCC'],
    'time_split': None,    # 'years', 'months', None
    'images_dir': 'images',
    'start_time': '2004.09.29 00:00:00',
    'end_time': '2004.10.05 00:00:00',
    'step_time_in_hours': 24,
    'dpi': 200,
    'scaling_by_selected_data': False,
    'plot_cyclones': True,
    'cyclones_file_name': 'best_track_ecscsuc_2020_m.xls',
}

cyclones_plot_options = {
    'work_dir': download_ERA5_options['work_dir'],
    'images_dir': 'cyclones',
    'start_time': '2004.09.20 00:00:00',
    'end_time': '2004.10.20 00:00:00',
    'n_3h_intervals_before_after': 16,
    'cyclones_file_name': 'best_track_ecscsuc_2020_m.xls',
}

metric_dimension = {
    'LCC': '2D',
    'GCC': '1D',
}

debug_level = 1
