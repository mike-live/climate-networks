import os
#os.environ["NUMBA_DISABLE_JIT"] = "1"
#os.environ["NUMBA_DUMP_ANNOTATION"] = "1"

import numpy as np
#import scipy
#import numba as nb
#from numba import float64, int32, int64, uint64, int8, jit, prange, config, threading_layer
#from numba.experimental import jitclass

#from scipy.stats import kendalltau
#from collections import namedtuple
#from tqdm import tqdm, tqdm_notebook
#from scipy import special
from time import time

num_threads = 1

from .parallel_maker import parallel_execute, make_args
from . import kendaltau_corr
from . import kendaltau_corr_online
from . import kendaltau_corr_scipy
from . import kendaltau_corr_online_bitset

import numpy as np
import os
from pathlib2 import Path

work_dir = Path(r'../../../data/SST/All2019_6h_0.75resolution')
file_name = 'resulting_cube_All2019_6h_0.75resolution.npz'
data = np.load(work_dir / file_name)
data_s = data['arr_0'].transpose((1, 2, 0))

data = data_s.reshape(-1, data_s.shape[2])
data = data[~np.any(np.isnan(data), axis = 1), :]

print(data.shape)

np.random.seed(42)
n = 10
m = 10
nt = 400
#data_s = np.random.rand(n, m, nt).astype(np.float64)
#data_s = np.random.randint(10, size = (n, m, nt)).astype(np.float64)

#data = data_s.reshape(-1, data_s.shape[2])
data_all = data.copy()
data = data_all[:n*m, :nt].astype(np.float64)

nm, nt = data.shape

print(data.shape)
#test_parallel = make_multithread(test, 1)
#test_parallel(np.zeros((10, 10)), np.array(list(range(10))))

#nb.set_num_threads(10)

#compute_tau_kendall_overall_parallel = make_multithread(compute_tau_kendall_overall, 10)
#tau_corr = compute_tau_kendall_overall_parallel(np.zeros((10, 10)), np.arange(10))

#tau_corr = np.zeros((2, 2, 90), dtype = np.float64)
#test(tau_corr, np.zeros((10, 10)), np.array(list(range(10))))
delay_time = 70
window_size = 130

###############################################################################################################################################

tau_corr = np.zeros((nm, nm, nt), dtype = np.float64)
#kendaltau_corr_online.compute_tau_kendall_overall_online(tau_corr, data, np.arange(nm), delay_time = delay_time, window_size = window_size)
#print('sum1:', tau_corr.sum())

ans = np.zeros((nm, nm, nt), dtype = np.float64)
kendaltau_corr.compute_tau_kendall_overall(ans, data, np.arange(nm), delay_time = delay_time, window_size = window_size)
print('ans1 = ', ans.sum())
print('diff1 = ', (np.abs(ans - tau_corr)).max(), np.allclose(ans, tau_corr))


ans = np.zeros((nm, nm, nt), dtype = np.float64)
kendaltau_corr.compute_tau_kendall_overall(ans, data, np.arange(nm), delay_time = delay_time, window_size = window_size)
print('ans1 = ', ans.sum())
print('diff1 = ', (np.abs(ans - tau_corr)).max(), np.allclose(ans, tau_corr))

sans = kendaltau_corr_scipy.compute_tau_kendall_overall(data, delay_time = delay_time, window_size = window_size)
print('ans2 = ', sans.sum())
print('diff2 = ', (np.abs(ans - sans)).max(), np.allclose(ans, sans))
#print(data[:, 1])

kendaltau_corr_online_bitset.compute_tau_kendall_overall_online_bitset(tau_corr, data, np.arange(nm), delay_time = delay_time, window_size = window_size)
print('sum3:', tau_corr.sum())
print('diff3 = ', (np.abs(ans - tau_corr)).max(), np.allclose(ans, tau_corr))
sdf
###############################################################################################################################################


#print(tau_corr[:, :, window_size:])
#print(sans[:, :, window_size:])

#res = test(data)
#tau_corr = np.zeros((nm, nm, nt), dtype = np.float64)
#test(tau_corr, data, np.array(list(range(10))))
#tau_corr = compute_tau_kendall_overall(data)
#tau_corr = compute_tau_kendall_overall_parallel(data, np.arange(data.shape[0]))
#res = test_parallel(data, np.array(list(range(data.shape[0]))))

#ans = corr_network_scipy.compute_tau_kendall_overall(data)
#n = 50
#m = 10
#nt = data_all.shape[1]
n = 10
m = 10
nt = 90

data = data_all.astype(np.float64)[:n*m, :nt].astype(np.float64)
nm, nt = data.shape
print(nm, nt)

'''be = time()
ans = np.zeros((nm, nm, nt), dtype=data.dtype)
#parallel_execute(num_threads, test, make_args(num_threads, result, data))

parallel_execute(num_threads, kendaltau_corr.compute_tau_kendall_overall, make_args(num_threads, ans, data))
en = time()
print('Time ok:', en - be)'''

###############################################################################################################################################

be = time()
result2 = np.zeros((nm, nm, nt), dtype=data.dtype)
parallel_execute(num_threads, kendaltau_corr_online_bitset.compute_tau_kendall_overall_online_bitset, make_args(num_threads, result2, data))
en = time()
print('Time 2:', en - be)
#np.save('corr_online_All2019_6h_resolution_0.75_window_15d_delay_7d.npy', result)
print('res =', result2.sum())

###############################################################################################################################################

be = time()
result = np.zeros((nm, nm, nt), dtype=data.dtype)
parallel_execute(num_threads, kendaltau_corr_online.compute_tau_kendall_overall_online, make_args(num_threads, result, data))
#print(result)
#print(ans)
'''window_size = 15 * 4 
corr = kendaltau_corr(window_size)


def get_ranks(x, y):
    size = x.size
    perm = np.argsort(y)  # sort on y and convert y to dense ranks
    x, y = x[perm], y[perm]
    y = np.concatenate([[True], y[1:] != y[:-1]]).cumsum(dtype=np.intp)

    # stable sort on x and convert x to dense ranks
    perm = np.argsort(x, kind='mergesort')
    x, y = x[perm], y[perm]
    x = np.concatenate([[True], x[1:] != x[:-1]]).cumsum(dtype=np.intp)
    return x, y'''


en = time()
print('Time fast:', en - be)
#np.save('corr_online_All2019_6h_resolution_0.75_window_15d_delay_7d.npy', result)
print('res =', result.sum())
#print('diff =', np.max(np.abs(ans - result)))
#print("Threading layer chosen: %s" % threading_layer())



print('Allclose:', np.allclose(result2, result))
