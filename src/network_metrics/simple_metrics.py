import scipy
import numpy as np
from numba import jit
from helpers import numba_config

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache, error_model="numpy")
def compute_degrees(a):
    degree = np.sum(a, axis = 1)
    return degree

def compute_eigenvector_centrality(a):
    v, w = scipy.linalg.eigh(a, subset_by_index = [len(a) - 1, len(a) - 1], driver = 'evr')
    return np.abs(w.flatten())

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache, error_model="numpy")
def compute_shortest_paths(a, is_weighted = False):
    dist = a.copy().astype(np.float64)
    n = len(dist)
    for k in range(n): 
        for i in range(n): 
            for j in range(n):
                if dist[i][k] == 0 or dist[k][j] == 0:
                    continue
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j]) 
    return dist

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache, error_model="numpy")
def compute_closeness(a, is_weighted = False):
    if is_weighted:
        a = np.abs(a)
    shortest_paths = compute_shortest_paths(a, is_weighted)
    closeness_centrality = np.zeros(len(a), np.float64)
    n = len(a)
    for i in range(n):
        sp = shortest_paths[i, :]
        if not is_weighted:
            sp[sp == 0] = n
            sp[i] = 0
        totsp = np.sum(sp)
        if totsp > 0.0:
            closeness_centrality[i] = (n - 1.0) / totsp
        else: 
            closeness_centrality[i] = 0
    return closeness_centrality