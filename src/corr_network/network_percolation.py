import os
os.environ["NUMBA_DISABLE_JIT"] = "1"

import numpy as np
from numba import float64, int32, int64, uint64, int8, jit
from numba.experimental import jitclass

import numba_config
from pathlib2 import Path

spec = [
    ('p', int32[:]),
    ('cnt', int32[:]),
]

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def find_index(p, elem):
    if p[elem] == -1:
        return elem
    p[elem] = find_index(p, p[elem])
    return p[elem]

@jitclass(spec)
class DisjointSet:    
    def __init__(self, n):
        self.p = -np.ones(n, dtype = np.int32)
        self.cnt = np.ones(n, dtype = np.int32)

    def find(self, elem):
        return find_index(self.p, elem)
    
    def union(self, elem1, elem2):
        elem1 = self.find(elem1)
        elem2 = self.find(elem2)
        if elem1 == elem2:
            return self.cnt[elem1]
        if self.cnt[elem1] < self.cnt[elem2]:
            elem1, elem2 = elem2, elem1
        
        self.cnt[elem1] += self.cnt[elem2]
        self.cnt[elem2] = 0
        self.p[elem2] = elem1
        return self.cnt[elem1]

    def get(self):
        return self.p

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def unravel_index(index, shape):
    sizes = np.zeros(len(shape), dtype=np.int64)
    result = np.zeros((len(shape), len(index)), dtype=np.int64)
    sizes[-1] = 1
    for i in range(len(shape) - 2, -1, -1):
        sizes[i] = sizes[i + 1] * shape[i + 1]
    remainder = index.copy()
    for i in range(len(shape)):
        result[i] = remainder // sizes[i]
        remainder %= sizes[i]
    return result.T
'''
def unravel_index(index, shape):
    sizes = np.zeros(len(shape), dtype=np.int64)
    result = tuple(shape)
    sizes[-1] = 1
    for i in range(len(shape) - 2, -1, -1):
        sizes[i] = sizes[i + 1] * shape[i + 1]
    remainder = index
    for i in range(len(shape)):
        result = result[:i] + (remainder // sizes[i], ) + result[i+1:]
        remainder %= sizes[i]
    return result'''

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def compute_percolation(A):
    b = A.ravel()
    ravel_sorted_ids = np.argsort(b)
    sorted_ids = unravel_index(ravel_sorted_ids, A.shape)
    #print(sorted_ids)
    sorted_ids = sorted_ids[b[ravel_sorted_ids] > 0, :]
    #print(sorted_ids)
    sorted_ids = sorted_ids[::-1]
    #print(sorted_ids)
    #from disjoint_set import DisjointSet
    dsu = DisjointSet(len(A))
    mx = 1
    delta_max = 0
    giant_size = np.zeros(len(sorted_ids))
    thresholds = np.zeros(len(giant_size))
    for i, (x, y) in enumerate(sorted_ids):
        cnt = dsu.union(x, y)
        mx_prev = mx
        mx = max(mx, cnt)
        delta = mx - mx_prev
        delta_max = max(delta_max, delta)
        #print(i, x, y, mx, cnt)
        thresholds[i] = A[x, y]
        giant_size[i] = mx
    import matplotlib.pyplot as plt
    plt.plot(thresholds, giant_size, '*')
    plt.xlim([0.8, 1])
    plt.show()
    return delta_max

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def compute_percolation_time(data):
    nt = data.shape[2]
    delta_max = np.zeros(nt, dtype = np.int32)
    for t in range(nt):
        delta_max[t] = compute_percolation(data[:, :, t])
    return delta_max

data = work_dir = Path(r'..\..\data\SST')
file_name = 'corr_online_1979_2019_6h_resolution_0.75_window_15d_delay_7d.npy'
data = np.load(work_dir / file_name, mmap_mode = 'r')
data = data[:, :, 99:100]

print(data.shape)

'''np.random.seed(42)
A = np.random.rand(170, 170)
mask = np.random.randint(2, size = A.shape, dtype = np.bool)
A[mask] = 0
mask_upper = np.tril(np.ones(A.shape, np.bool))
A[mask_upper] = 0
#plt.imshow(A)
print(compute_percolation(A))
'''

from time import time
be = time()
delta_max = compute_percolation_time(data)
en = time()
print(en - be)
np.save(work_dir / 'delta.npy', delta_max)

#'''