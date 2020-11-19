import os
#os.environ["NUMBA_DISABLE_JIT"] = "1"
#os.environ["NUMBA_CACHE_DIR"] = "__numba_cache__"

import numpy as np
from time import time

from .parallel_maker import parallel_execute, make_args
from . import kendaltau_corr
from . import kendaltau_corr_online
from . import kendaltau_corr_scipy

import numpy as np
from pathlib2 import Path

def load_data(config):
    work_dir = config.correlations['work_dir'] #Path(r'All2019_6h_0.75resolution')
    file_name = config.correlations['input_file_name'] #'resulting_cube_All2019_6h_0.75resolution.npz'
    var_name = config.correlations['input_var_name'] # arr_0
    data = np.load(work_dir / file_name)
    data_s = data[var_name].transpose((1, 2, 0))
    return data_s

def exclude_not_available(data_s):
    data = data_s.reshape(-1, data_s.shape[2])
    data = data[~np.any(np.isnan(data), axis = 1), :]

    print(data.shape)

    return data

def calc_online_optimized(data, delay_time, window_size):
    # Third optimization
    tau_corr = np.zeros((nm, nm, nt), dtype = np.float64)
    kendaltau_corr_online.compute_tau_kendall_overall_online(tau_corr, data, np.arange(nm), delay_time = delay_time, window_size = window_size)
    if config.debug_level:
        print('res:', tau_corr.sum())
    return tau_corr

def calc_numba_optimized(data, delay_time, window_size, ans = None):
    # Second optimization
    ans = np.zeros((nm, nm, nt), dtype = np.float64)
    kendaltau_corr.compute_tau_kendall_overall(ans, data, np.arange(nm), delay_time = delay_time, window_size = window_size)
    if config.debug_level:
        if not ans is None:
            print('ans = ', ans.sum())
            print('diff1 = ', (np.abs(ans - tau_corr)).max())

def calc_scipy(data, delay_time, window_size, ans = None):
    # Correct implementation
    sans = kendaltau_corr_scipy.compute_tau_kendall_overall(data, delay_time = delay_time, window_size = window_size)
    print('sans = ', sans.sum())

    print('diff2 = ', (np.abs(ans - sans)).max())
    print(data[:, 1])

def calc_parallel_online_optimized(data, delay_time, window_size, num_threads = 1, ans = None):
    # Paralleled optimized implementation
    data = data.astype(np.float64)#[:n*m, :nt].astype(np.float64)
    nm, nt = data.shape
    print(nm, nt)

    be = time()
    result = np.zeros((nm, nm, nt), dtype=data.dtype)
    parallel_execute(num_threads, kendaltau_corr_online.compute_tau_kendall_overall_online, make_args(num_threads, result, data))
    en = time()
    print('Time:', en - be)
    return result

def save_result(config, result):
    work_dir = config.correlations['work_dir'] # Path(r'All2019_6h_0.75resolution')
    file_name = config.correlations['output_correlation_file_name'] # 'corr_online_All2019_6h_resolution_0.75_window_15d_delay_7d.npy'
    
    np.savez(work_dir / file_name, result)
    print('res =', result.sum())

def make_correlation_matricies(config):
    #delay_time = 28
    #window_size = 60
    delay_time = config.correlations['delay_time']
    window_size = config.correlations['window_size']
    num_threads = config.correlations['num_threads']
    data_s = load_data(config) # , latitutdes, longitudes, timeticks
    data = exclude_not_available(data_s)
    result = calc_parallel_online_optimized(data, delay_time, window_size, num_threads)
    save_result(config, result)

