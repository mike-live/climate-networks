import time
import numpy as np
from numba import jit
from helpers import numba_config

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache, error_model="numpy")
def compute_clustering_coefficient(a):
    (n, m) = a.shape

    Ci = np.empty(n)

    Div = np.sqrt(np.maximum(0, 1-np.multiply(a, a)))
    #Ridx1, Ridx2 = np.triu_indices(n, 1)
    #mymask = np.ones((n, n), np.bool_)

    for i in range(n):
        #M = np.outer(a[i,:], a[i,:])
        #D = np.outer(Div[i,:],Div[i,:])
        '''for p1, p2 in zip(Ridx1, Ridx2):
            mymask[p1, p2] = False
        mymask[i, :] = True
        mymask[:, i] = True'''
        sumDown = sumUp = 0.0
        for j in range(n):
            for k in range(j):
                if j != i and i != k:
                    D = Div[i, j] * Div[i, k]
                    if D > 1.e-5:
                        M = a[i, j] * a[i, k]
                        ro = (a[j, k] - M) / D
                        up2abs = np.abs(M * ro)
                        sumUp += up2abs
                        sumDown += np.abs(M)
        if sumDown == 0:
            Ci[i] = np.nan
        else:
            Ci[i] = sumUp / sumDown

        '''M1 = np.fabs(M)
        r1 = a
        up1 = r1 - M
        ro = up1 / D
        up2 = M * ro
        up2abs = np.fabs(up2)
        sumDown = sumUp = 0
        for j in range(n):
            for k in range(n):
                if mymask[j, k]:
                    sumUp += up2abs[j, k]
                    sumDown += M1[j, k]
        Ci[i] = sumUp / sumDown'''

    Cglob = np.mean(Ci)
    return Ci, Cglob

