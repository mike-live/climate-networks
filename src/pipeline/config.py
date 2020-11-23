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
    'num_threads': 5,
    'need_save': False,
    'num_parts': 666,
    'id_part': 1,
    'output_level': 1,
}

network_metrics = {
    'num_threads': 1,
    'work_dir': correlations['work_dir'],
    'output_metrics_file_name': 'metrics_corr_preproc_ERA5_SST_1982_2019_3h_0.75_window_10d_delay_0d.npy',
}

debug_level = 1