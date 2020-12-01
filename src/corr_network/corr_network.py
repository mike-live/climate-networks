import os
#os.environ["NUMBA_DISABLE_JIT"] = "1"
#os.environ["NUMBA_CACHE_DIR"] = "__numba_cache__"

import numpy as np
from time import time

from helpers.parallel_maker import parallel_execute, make_args
from . import kendaltau_corr
from . import kendaltau_corr_online
from . import kendaltau_corr_scipy
from . import kendaltau_corr_online_bitset

import numpy as np
from pathlib2 import Path

def load_data(config):
    work_dir = config.correlations['work_dir'] #Path(r'All2019_6h_0.75resolution')
    file_name = config.correlations['input_file_name'] #'resulting_cube_All2019_6h_0.75resolution.npz'
    var_name = config.correlations['input_var_name'] # arr_0
    data = np.load(work_dir / file_name)
    data_s = data[var_name].transpose((1, 2, 0))
    return data_s

def get_available_data(data, mask):
    return data[mask, :]

def get_available_mask(data):
    mask = ~np.any(np.isnan(data), axis = -1)
    return mask

def expand_to_2d_by_mask(data, mask):
    res = np.empty(mask.shape + (data.shape[-1], ))
    res[:] = np.nan
    res[mask, :] = data
    return res
           
def calc_online_optimized(data, delay_time, window_size):
    # Third optimization
    tau_corr = np.zeros((nm, nm, nt), dtype = np.float64)
    kendaltau_corr_online.compute_tau_kendall_overall_online(tau_corr, data, np.arange(nm), delay_time = delay_time, window_size = window_size)
    if config.correlations['output_level'] >= 2:
        print('res:', tau_corr.sum())
    return tau_corr

def calc_numba_optimized(data, delay_time, window_size, ans = None):
    # Second optimization
    ans = np.zeros((nm, nm, nt), dtype = np.float64)
    kendaltau_corr.compute_tau_kendall_overall(ans, data, np.arange(nm), delay_time = delay_time, window_size = window_size)
    if config.correlations['output_level'] >= 2:
        if not ans is None:
            print('ans = ', ans.sum())
            print('diff1 = ', (np.abs(ans - tau_corr)).max())

def calc_scipy(data, delay_time, window_size, ans = None):
    # Correct implementation
    sans = kendaltau_corr_scipy.compute_tau_kendall_overall(data, delay_time = delay_time, window_size = window_size)
    print('sans = ', sans.sum())

    print('diff2 = ', (np.abs(ans - sans)).max())
    print(data[:, 1])

def calc_parallel_online_optimized(data, delay_time, window_size, num_threads = 1, ans = None, output_level = 0):
    # Paralleled optimized implementation
    data = data.astype(np.float64)#[:n*m, :nt].astype(np.float64)
    nm, nt = data.shape
    if output_level >= 2:
        print(nm, nt)

    be = time()
    result = np.zeros((nm, nm, nt), dtype=data.dtype)
    
    compute_tau = lambda *args: kendaltau_corr_online_bitset.compute_tau_kendall_overall_online_bitset(*args, window_size, delay_time)
    parallel_execute(num_threads, compute_tau, make_args(num_threads, result, data))
    en = time()
    if output_level >= 2:
        print('Time:', en - be)
    return result

def save_result(config, result):
    work_dir = config.correlations['work_dir'] # Path(r'All2019_6h_0.75resolution')
    file_name = config.correlations['output_correlation_file_name'] # 'corr_online_All2019_6h_resolution_0.75_window_15d_delay_7d.npy'
    
    np.savez(work_dir / file_name, result)
    if config.correlations['output_level'] >= 2:
        print('res =', result.sum())

def get_parts(id_part, num_parts, nt):
    len_part = nt // num_parts
    pos_part = (len_part + 1) * min(id_part, nt % num_parts) + len_part * max(0, id_part - nt % num_parts)
    len_part += (id_part < nt % num_parts)
    return pos_part, len_part

def make_correlation_matricies(config, mask = None):
    delay_time = config.correlations['delay_time']
    window_size = config.correlations['window_size']
    num_threads = config.correlations['num_threads']
    
    if config.correlations['output_level'] >= 2:
        print('Window size:', window_size, 'Delay time:', delay_time)
        print('Num threads:', num_threads)
    data_s = load_data(config) # , latitutdes, longitudes, timeticks
    if mask is None:
        mask = get_available_mask(data)
    data = get_available_data(data, mask)
    if 'num_parts' in config.correlations:
        num_parts = config.correlations['num_parts']
        id_part = config.correlations['id_part']
        pos_part, len_part = get_parts(id_part, num_parts, data.shape[1])
        shifted_pos = max(0, pos_part - window_size - delay_time)
        if config.correlations['output_level'] >= 2:
            print('Part:', id_part, '/', num_parts, 'nt:', data.shape[1])
            print('Pos:', pos_part, 'len:', len_part, 'shifted:', shifted_pos)
        data = data[:, shifted_pos:pos_part + len_part]

    result = calc_parallel_online_optimized(data, delay_time, window_size, num_threads, output_level = config.correlations['output_level'])
    if 'num_parts' in config.correlations:
        if id_part != 0:
           result = result[:, :, window_size + delay_time:]

    if config.correlations['need_save']:
        save_result(config, result)
    return result


