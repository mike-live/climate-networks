from numba import float64, int32, int64, uint64, int8, jit
import math
from helpers import numba_config

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def merge_dis(x, y, xx, yy, l, r):
    if l == r:
        return 0
    m = (l + r) // 2
    res = merge_dis(x, y, xx, yy, l, m)
    res += merge_dis(x, y, xx, yy, m + 1, r)
    
    i = l
    j = m + 1
    k = l
    mx = x[l]
    for q in range(l, m + 1):
        if mx < x[q]:
            mx = x[q]
    cntmxmy = cntmx = cntmy = 0
    last = -1
    while i <= m and j <= r:
        if y[i] < y[j]: 
            yy[k] = y[i]
            xx[k] = x[i]
            res += j - (m + 1)
            if x[i] == mx and y[i] == last:
                res -= cntmx + cntmy - cntmxmy
            elif x[i] == mx:
                res -= cntmx
            elif y[i] == last:
                res -= cntmy
            k += 1
            i += 1
        else:
            yy[k] = y[j] 
            xx[k] = x[j]
            if x[j] == mx and y[j] == y[i]:
                cntmxmy += 1
            if x[j] == mx:
                cntmx += 1
            if y[j] == y[i]:
                cntmy += 1
                last = y[i]
                
            k += 1
            j += 1
        if y[i] != last:
            cntmxmy = 0
            cntmy = 0
        

    while i <= m:
        yy[k] = y[i] 
        xx[k] = x[i] 
        res += j - (m + 1)
        if x[i] == mx and y[i] == last:
            res -= cntmx + cntmy - cntmxmy
        elif x[i] == mx:
            res -= cntmx
        elif y[i] == last:
            res -= cntmy
        k += 1
        i += 1
        if y[i] != last:
            cntmxmy = 0
            cntmy = 0
        
    while j <= r: 
        yy[k] = y[j]
        xx[k] = x[j]
        k += 1
        j += 1
        
    for k in range(l, r + 1):
        y[k] = yy[k]
        x[k] = xx[k]

    return res

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def merge_sort(arr0, arr1, tmp0, tmp1, l, r):
    if l == r:
        return 0
    m = (l + r) // 2
    merge_sort(arr0, arr1, tmp0, tmp1, l, m)
    merge_sort(arr0, arr1, tmp0, tmp1, m + 1, r)
    
    i = l
    j = m + 1
    k = l
    while i <= m and j <= r:
        if arr0[i] < arr0[j]: 
            tmp0[k] = arr0[i]
            tmp1[k] = arr1[i]
            k += 1
            i += 1
        else:
            tmp0[k] = arr0[j]
            tmp1[k] = arr1[j]
            k += 1
            j += 1

    while i <= m:
        tmp0[k] = arr0[i]
        tmp1[k] = arr1[i]
        k += 1
        i += 1

    while j <= r: 
        tmp0[k] = arr0[j]
        tmp1[k] = arr1[j]
        k += 1
        j += 1

    for k in range(l, r + 1):
        arr0[k] = tmp0[k]
        arr1[k] = tmp1[k]

    #arr0[l:r + 1] = tmp0[l:r + 1]
    #arr1[l:r + 1] = tmp1[l:r + 1]

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def partition(arr0, arr1, low, high): 
    i = low - 1
    pivot = arr0[high]
    
    for j in range(low, high): 
        if arr0[j] <= pivot:
            i += 1
            arr0[i], arr0[j] = arr0[j], arr0[i]
            arr1[i], arr1[j] = arr1[j], arr1[i]
  
    arr0[i + 1], arr0[high] = arr0[high], arr0[i + 1] 
    arr1[i + 1], arr1[high] = arr1[high], arr1[i + 1] 
    return i + 1
  
@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def quick_sort(arr0, arr1, low, high): 
    if low < high:
        pi = partition(arr0, arr1, low, high) 
  
        quick_sort(arr0, arr1, low, pi - 1) 
        quick_sort(arr0, arr1, pi + 1, high) 

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def mysort(arr0, arr1, tmp0, tmp1, kind = 0):
    if kind == 0:
        quick_sort(arr0, arr1, 0, len(arr0) - 1)
    if kind == 1:
        merge_sort(arr0, arr1, tmp0, tmp1, 0, len(arr0) - 1)

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def factorial(x):
    #res = 1
    #for i in range(x):
    #    res *= i + 1
    res = math.gamma(x + 1)
    return res
