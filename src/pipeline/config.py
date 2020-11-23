from pathlib2 import Path

import os
print(os.getcwd())

correlations = {
    'work_dir': Path(r'../../../data/SST/All2019_6h_0.75resolution'),
    'input_file_name': 'resulting_cube_All2019_6h_0.75resolution.npz',
    'input_var_name': 'arr_0',
    'output_correlation_file_name': 'corr_online_All2019_6h_resolution_0.75_window_15d_delay_7d.npy',
#    'output_correlation_var_name': 'result',
    'delay_time': 0,
    'window_size': 2,
    'num_threads': 2,
}

download_ERA5_options = {
    'work_dir': 'ERA5/ERA5_MSLP_1982_2019_3h_0.75_new/',
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