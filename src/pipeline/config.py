from pathlib2 import Path

import os
print(os.getcwd())

correlations = {
    'work_dir': Path(r'../../../data/ERA5/ERA5_SST_1982_2019_3h_0.75'),
    'input_file_name': 'resulting_cube_after_preproc_ERA5_SST_1982_2019_3h_0.75.npz',
    'input_var_name': 'arr_0',
    'output_correlation_file_name': 'corr_online_preproc_ERA5_SST_1982_2019_3h_0.75_window_10d_delay_0d.npy',
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
    'output_metrics_file_name': 'metrics_corr_preproc_ERA5_SST_1982_2019_3h_0.75_window_10d_delay_0d.npy',
}

download_ERA5_options = {
    'work_dir': 'ERA5/ERA5_MSLP_1982_2019_3h_0.75/',
    'pref': 'ERA5_MSLP_1982_2019_3h_0.75',
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
}

debug_level = 1