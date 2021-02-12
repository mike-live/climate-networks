from pathlib2 import Path

import os
print(os.getcwd())

correlations = {
    'work_dir': Path(r'../../../data/ERA5/ERA5_MSLP_1982_2019_3h_0.75'),
    'input_file_name': 'resulting_cube_land_masked_after_preproc_ERA5_MSLP_1982_2019_3h_0.75.npz',
    'input_var_name': 'arr_0',
    'output_correlation_file_name': 'corr_online_land_masked_after_preproc_ERA5_MSLP_1982_2019_3h_0.75_window_10d_delay_0d.npy',
#    'output_correlation_var_name': 'result',
    'delay_time': 0,
    'window_size': 80,
    'num_threads': 85,
    'need_save': False,
    'num_parts': 666,
    'id_part': 1,
    'output_level': 1,
}

metrics = {
    'work_dir': correlations['work_dir'],
    'output_metrics_dir': 'metrics_corr_land_masked_after_preproc_ERA5_MSLP_1982_2019_3h_0.75_window_10d_delay_0d',
    #'output_metrics_file_name': 'metrics_corr_land_masked_after_preproc_ERA5_MSLP_1982_2019_3h_0.75_window_10d_delay_0d.npy',
    'metric_names_file_name': 'metric_names.npy',
}

network_metrics = {
    'num_threads': 84,
    'work_dir': correlations['work_dir'] / metrics['output_metrics_dir'],
    #'output_metrics_file_name': 'metrics_corr_land_masked_after_preproc_ERA5_MSLP_1982_2019_3h_0.75_window_10d_delay_0d.npy',
    'output_network_metrics_dir': Path('network_metrics'),
}

diff_metrics = {
    'num_threads': 2,
    'work_dir': correlations['work_dir'] / metrics['output_metrics_dir'],
    'output_diff_metrics_dir': Path('diff_metrics'),
}

debug_level = 1