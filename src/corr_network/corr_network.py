import os
#os.environ["NUMBA_DISABLE_JIT"] = "1"

import numpy as np
from time import time

from parallel_maker import parallel_execute, make_args
import kendaltau_corr
import kendaltau_corr_online
import kendaltau_corr_scipy

import numpy as np
from pathlib2 import Path

def load_data():
    work_dir = Path(r'All2019_6h_0.75resolution')
    file_name = 'resulting_cube_All2019_6h_0.75resolution.npz'
    data = np.load(work_dir / file_name)
    data_s = data['arr_0'].transpose((1, 2, 0))

    data = data_s.reshape(-1, data_s.shape[2])
    data = data[~np.any(np.isnan(data), axis = 1), :]

    print(data.shape)
    data_all = data.copy()
    data = data_all[:n*m, :nt].astype(np.float64)

    nm, nt = data.shape

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
        if ans not is None:
            print('ans = ', ans.sum())
            print('diff1 = ', (np.abs(ans - tau_corr)).max())

def calc_scipy(data, delay_time, window_size, ans = None)
    # Correct implementation
    sans = kendaltau_corr_scipy.compute_tau_kendall_overall(data, delay_time = delay_time, window_size = window_size)
    print('sans = ', sans.sum())

    print('diff2 = ', (np.abs(ans - sans)).max())
    print(data[:, 1])

def calc_parallel_online_optimized(config, data, delay_time, window_size, num_threads = 1, ans = None)
    # Paralleled optimized implementation
    data = data_all.astype(np.float64)#[:n*m, :nt].astype(np.float64)
    nm, nt = data.shape
    print(nm, nt)

    be = time()
    result = np.zeros((nm, nm, nt), dtype=data.dtype)
    parallel_execute(num_threads, kendaltau_corr_online.compute_tau_kendall_overall_online, make_args(num_threads, result, data))
    en = time()
    print('Time fast:', en - be)

def save_result():
    'corr_online_All2019_6h_resolution_0.75_window_15d_delay_7d.npy'
    np.save(, result)
    print('res =', result.sum())

def compute_correlation_matricies(config):
    #delay_time = 28
    #window_size = 60
    delay_time = config.correlations.delay_time
    window_size = config.correlations.window_size
    num_threads = config.correlations.num_threads


