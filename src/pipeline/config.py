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

debug_level = 1