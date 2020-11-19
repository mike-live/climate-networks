from numba import float64, int32, int64, uint64, int8, jit, prange, config, threading_layer
from numba.experimental import jitclass
import math
from .kendalltau_helpers import *
from . import numba_config
import numpy as np

spec_kendal_tau = [
    ('corr', int64),
    ('window', uint64),
    ('window_64', uint64),
    ('subset', uint64[:]),
    ('data', float64[:, :]),
    ('tot', int64),
    ('ntie', int64),
    ('dis', int64),
    ('ti', int64),
    ('tj', int64),
    ('si', int64),
    ('sj', int64),
    ('popcnt_mask', int32),
    ('popcnt', int32[:]),
    ('xtie', uint64[:, :]),
    ('xtie0', float64[:, :]),
    ('xtie1', float64[:, :]),
    ('mask_left_less', uint64[:, :, :]),
    ('mask_left_greater', uint64[:, :, :]),
    ('mask_left_equal', uint64[:, :, :]),
    ('mask_right_less', uint64[:, :, :]),
    ('mask_right_greater', uint64[:, :, :]),
    ('mask_right_equal', uint64[:, :, :]),
    ('bincount_cnt', int64[:]),
    ('pvalue_sum', float64[:]),
    ('kendalltau_x', int64[:]),
    ('kendalltau_y', int64[:]),
    ('kendalltau_tmp_x', float64[:]),
    ('kendalltau_tmp_y', float64[:]),
    ('kendalltau_tmp_y2', int64[:]),
    ('kendalldis_tmp_x', float64[:]),
    ('kendalldis_tmp_y', float64[:]),
]

@jitclass(spec_kendal_tau)
class kendalltau_corr_online:
    def __init__(self, data, window):

        #assert(window < 64)
        self.window = window
        self.data = data
        self.window_64 = (window + 64) // 64
        print('window_64', self.window_64)
        self.subset = np.zeros(self.window_64, dtype = np.uint64)

        self.tot = self.window * (self.window - 1) // 2

        self.kendalltau_x = np.zeros(self.window, np.int64)
        self.kendalltau_y = np.zeros(self.window, np.int64)
        self.kendalltau_tmp_x = np.zeros(self.window, np.float64)
        self.kendalltau_tmp_y = np.zeros(self.window, np.float64)
        self.kendalltau_tmp_y2 = np.zeros(self.window, np.int64)

        self.kendalldis_tmp_x = np.zeros(self.window, np.float64)
        self.kendalldis_tmp_y = np.zeros(self.window, np.float64)

        self.popcnt_mask = np.uint64((1 << 16) - 1)
        self.popcnt = np.zeros((1 << 16), dtype = np.int32)
        for i in range(len(self.popcnt)):
            cnt = 0
            cur = i
            while cur > 0:
                cnt += cur & 1
                cur >>= 1
            self.popcnt[i] = cnt

        self.bincount_cnt = np.zeros(self.window + 1, np.int64)
        if self.window <= 33:
            self.pvalue_sum = np.zeros(self.window * self.window, np.float64)
            self.init_pvalue()

        self.precompute_masks()

    def bincount(self, x):
        self.bincount_cnt[:] = 0
        for q in x:
            self.bincount_cnt[q] += 1
        return self.bincount_cnt

        
    def count_rank_tie(self, ranks):
        bins = self.bincount(ranks)
        res2 = res1 = res0 = 0
        for x in bins:
            if x > 1:
                res0 += x * (x - 1) // 2
                res1 += x * (x - 1.) * (x - 2)
                res2 += x * (x - 1.) * (2 * x + 5)
        return res0, res1, res2

    def init_pvalue(self):
        new = np.zeros(self.window * self.window, dtype = np.float64)
        old = np.zeros(self.window * self.window, dtype = np.float64)
        for c in range(2, self.window * self.window):
            for i in range(c + 1):
                new[i] = 0
            new[0] = 1.0
            new[1] = 1.0
            for j in range(3, self.window + 1):
                old[:] = new[:]
                for k in range(1, min(j, c + 1)):
                    new[k] += new[k - 1]
                for k in range(j, c + 1):
                    new[k] += new[k - 1] - old[k - j]
            sum_new = 0
            for i in range(c + 1):
                sum_new += new[i]
            self.pvalue_sum[c] = sum_new

    def get_ranks(self, x0):
        mysort(x0, self.kendalltau_tmp_y, self.kendalltau_tmp_x, self.kendalltau_tmp_y)

        x = self.kendalltau_x
        x[0] = 1
        for i in range(len(x0) - 1):
            if x0[i] != x0[i + 1]:
                x[i + 1] = x[i] + 1
            else:
                x[i + 1] = x[i]
        return x

    def compute_initial_dis_ntie(self, x0, y0):
        mysort(y0, x0, self.kendalltau_tmp_y, self.kendalltau_tmp_x)

        y = self.kendalltau_y
        y[0] = 1
        for i in range(len(y) - 1):
            if y0[i] != y0[i + 1]:
                y[i + 1] = y[i] + 1
            else:
                y[i + 1] = y[i]

        mysort(x0, y, self.kendalltau_tmp_x, self.kendalltau_tmp_y2, kind = 1)
        x = self.kendalltau_x
        x[0] = 1
        for i in range(len(x) - 1):
            if x0[i] != x0[i + 1]:
                x[i + 1] = x[i] + 1
            else:
                x[i + 1] = x[i]
        dis = self.kendall_dis(x, y)  # discordant pairs
        ntie = 0
        prv = 0
        for i in range(len(x) - 1):
            if x[i] != x[i + 1] or y[i] != y[i + 1]:
                cur = i + 1 - prv
                ntie += cur * (cur - 1) // 2
                prv = i + 1
        cur = len(x) - prv
        ntie += cur * (cur - 1) // 2
        return dis, ntie

    def kendall_dis(self, x0, y0):
        self.kendall_dis_x[:] = x0[:]
        self.kendall_dis_y[:] = y0[:]
        
        self.kendall_dis_yy[:] = 0
        self.kendall_dis_xx[:] = 0

        res = merge_dis(self.kendall_dis_x, self.kendall_dis_y, \
                        self.kendall_dis_xx, self.kendall_dis_yy, 0, self.window - 1)
        #assert(np.all(np.diff(y) >= 0))
        return res

    def compute_tau_pv(self, size, tot, xtie, x0, x1, ytie, y0, y1, ntie, dis):
        if xtie == tot or ytie == tot:
            return np.nan, np.nan

        # Note that tot = con + dis + (xtie - ntie) + (ytie - ntie) + ntie
        #               = con + dis + xtie + ytie - ntie
        con_minus_dis = tot - xtie - ytie + ntie - 2 * dis
        #print(tot, xtie, ytie, con_minus_dis)
        tau = con_minus_dis / np.sqrt(tot - xtie) / np.sqrt(tot - ytie)
        # Limit range to fix computational errors
        tau = min(np.float64(1.), max(np.float64(-1.), tau))
        #print(type(tau))

        #if method == 'exact' and (xtie != 0 or ytie != 0):
        #    raise ValueError("Ties found, exact method cannot be used.")
        #    pass

        #if method == 'auto':
        #    if (xtie == 0 and ytie == 0) and (size <= 33 or min(dis, tot-dis) <= 1):
        #        method = 'exact'
        #    else:
        #        method = 'asymptotic'
        #print('start')
        if xtie == 0 and ytie == 0 and (size <= 33 or min(dis, tot-dis) <= 1): #and method == 'exact':
            # Exact p-value, see p. 68 of Maurice G. Kendall, "Rank Correlation Methods" (4th Edition), Charles Griffin & Co., 1970.
            c = min(dis, tot-dis)
            if size <= 0:
                raise ValueError
            elif c < 0 or 2*c > size*(size-1):
                raise ValueError
            elif size == 1:
                pvalue = 1.0
            elif size == 2:
                pvalue = 1.0
            elif c == 0:
                pvalue = 2.0 / factorial(size) if size < 171 else 0.0
            elif c == 1:
                pvalue = 2.0 / factorial(size-1) if (size-1) < 171 else 0.0
            elif 2*c == tot:
                pvalue = 1.0
            else:
                pvalue = 2.0 * self.pvalue_sum[c] / factorial(size) if size < 171 else 0.0
        else:#if method == 'asymptotic':
            # con_minus_dis is approx normally distributed with this variance [3]_
            var = (size * (size - 1) * (2.*size + 5) - x1 - y1) / 18. + (
                2. * xtie * ytie) / (size * (size - 1)) + x0 * y0 / (9. *
                size * (size - 1) * (size - 2))
            pvalue = math.erfc(np.abs(con_minus_dis) / np.sqrt(var) / np.sqrt(2))
        #else:
        #    raise ValueError("Unknown method "+str(method)+" specified, please use auto, exact or asymptotic.")
        #    pass
        #print('good')
        return tau, pvalue


    def popcount(self, x):
        return self.popcnt[x & (self.popcnt_mask)] + \
               self.popcnt[(x >> np.uint64(16)) & (self.popcnt_mask)] + \
               self.popcnt[(x >> np.uint64(32)) & (self.popcnt_mask)] + \
               self.popcnt[(x >> np.uint64(48)) & (self.popcnt_mask)]

    def popcount_array(self, x):
        s = 0
        for v in x:
            s += self.popcount(v)
        return s

    def popcount_and_array_2(self, x, y):
        s = 0
        for i in range(self.window_64):
            s += self.popcount(x[i] & y[i])
        return s

    def popcount_and_array_3(self, x, y, z):
        s = 0
        #for a in x:
        #    s += self.popcount(a)
        for i in range(self.window_64):
            s += self.popcount(x[i] & y[i] & z[i])
            #s += self.popcount(x[i]) #  & y[i] & z[i]
        return s

    def set_bit(self, a, pos):
        # assume a.dtype == np.uint64
        a[pos >> np.uint64(6)] |= np.uint64(1) << (pos & np.uint64(63))
        

    def get_bit(self, a, pos):
        # assume a.dtype == np.uint64
        return (a[pos >> np.uint64(6)] >> (pos & np.uint64(63))) & np.uint64(1)


    def precompute_masks(self):
        nm, nt = self.data.shape

        xtie = np.zeros((nm, nt), dtype = np.uint64)
        xtie0 = np.zeros((nm, nt), dtype = np.float64)
        xtie1 = np.zeros((nm, nt), dtype = np.float64)

        mask_shape = (nm, nt, self.window_64)
        
        mask_left_less = np.zeros(mask_shape, dtype = np.uint64)
        mask_left_greater = np.zeros(mask_shape, dtype = np.uint64)
        mask_left_equal = np.zeros(mask_shape, dtype = np.uint64)

        mask_right_less = np.zeros(mask_shape, dtype = np.uint64)
        mask_right_greater = np.zeros(mask_shape, dtype = np.uint64)
        mask_right_equal = np.zeros(mask_shape, dtype = np.uint64)

        x = np.zeros(self.window, dtype = np.float64)
        
        mask_rl = np.zeros(self.window_64, dtype = np.uint64)
        mask_rg = np.zeros(self.window_64, dtype = np.uint64)
        mask_re = np.zeros(self.window_64, dtype = np.uint64)

        mask_ll = np.zeros(self.window_64, dtype = np.uint64)
        mask_lg = np.zeros(self.window_64, dtype = np.uint64)
        mask_le = np.zeros(self.window_64, dtype = np.uint64)

        for i in range(nm):
            for j in range(nt):
                mask_rl[:] = 0
                mask_rg[:] = 0
                mask_re[:] = 0
                for k in range(j + 1, min(nt, j + self.window)):
                    pos = np.uint64(k - j - 1)
                    if self.data[i, k] > self.data[i, j]:
                        self.set_bit(mask_rg, pos)
                    if self.data[i, k] < self.data[i, j]:
                        self.set_bit(mask_rl, pos)
                    if self.data[i, k] == self.data[i, j]:
                        self.set_bit(mask_re, pos)
                
                mask_ll[:] = 0
                mask_lg[:] = 0
                mask_le[:] = 0
                for k in range(max(0, j - self.window + 1), j):
                    pos = np.uint64(j - k - 1)
                    if self.data[i, k] > self.data[i, j]:
                        self.set_bit(mask_lg, pos)
                    if self.data[i, k] < self.data[i, j]:
                        self.set_bit(mask_ll, pos)
                    if self.data[i, k] == self.data[i, j]:
                        self.set_bit(mask_le, pos)

                mask_left_less[i, j, :] = mask_ll
                mask_left_greater[i, j, :] = mask_lg
                mask_left_equal[i, j, :] = mask_le

                mask_right_less[i, j, :] = mask_rl
                mask_right_greater[i, j, :] = mask_rg
                mask_right_equal[i, j, :] = mask_re

                if j + self.window <= nt:
                    x[:] = self.data[i, j:j + self.window]
                    ranks = self.get_ranks(x)
                    xtie[i, j], xtie0[i, j], xtie1[i, j] = self.count_rank_tie(ranks)

        #print(mask_right_equal, mask_left_equal)

        self.mask_left_less = mask_left_less
        self.mask_left_greater = mask_left_greater
        self.mask_left_equal = mask_left_equal

        self.mask_right_less = mask_right_less
        self.mask_right_greater = mask_right_greater
        self.mask_right_equal = mask_right_equal

        self.xtie = xtie
        self.xtie0 = xtie0
        self.xtie1 = xtie1

        #print(xtie, xtie0, xtie1)

    def init(self, i, j, ti, tj):
        self.ntie = 0
        self.dis = 0
        self.ti = ti
        self.tj = tj
        self.si = i
        self.sj = j
        nt = self.data.shape[1]
        self.subset[:] = 0
        for k in range(self.window):
            if self.ti + k >= nt or self.tj + k >= nt:
                break
            # subset = np.uint64((1 << k) - 1)
            self.add_pair_subset(i, j, self.ti + k, self.tj + k)
            self.set_bit(self.subset, k)
            pi = self.ti + k - self.window
            pj = self.tj + k - self.window
            #print('add', self.dis, self.ntie)
            #if pi >= 0 and pj >= 0:
            #    self.remove_pair(i, j, pi, pj)
            #print('remove', self.dis, self.ntie)
           
        '''
        x0 = self.kendalldis_tmp_x
        y0 = self.kendalldis_tmp_y
        x0[:] = data[i, ti:ti + self.window]
        y0[:] = data[j, tj:tj + self.window]
        dis, ntie = self.compute_initial_dis_ntie(x0, y0)
        '''
        #print('init', ti, tj, self.dis, self.ntie)

    def move_window(self):
        self.remove_pair(self.si, self.sj, self.ti, self.tj)
        self.add_pair(self.si, self.sj, self.ti + self.window, self.tj + self.window)
        #print('move', self.ti, self.tj, self.dis, self.ntie)
        self.ti += 1
        self.tj += 1

    def add_pair(self, i, j, ti, tj):
        for k in range(self.window_64):
            self.dis  += self.popcount(self.mask_left_less   [i, ti, k] & self.mask_left_greater[j, tj, k])
            self.dis  += self.popcount(self.mask_left_greater[i, ti, k] & self.mask_left_less   [j, tj, k])
            self.ntie += self.popcount(self.mask_left_equal  [i, ti, k] & self.mask_left_equal  [j, tj, k])

    def add_pair_subset(self, i, j, ti, tj):
        for k in range(self.window_64):
            self.dis  += self.popcount(self.mask_left_less   [i, ti, k] & self.mask_left_greater[j, tj, k] & self.subset[k])
            self.dis  += self.popcount(self.mask_left_greater[i, ti, k] & self.mask_left_less   [j, tj, k] & self.subset[k])
            self.ntie += self.popcount(self.mask_left_equal  [i, ti, k] & self.mask_left_equal  [j, tj, k] & self.subset[k])
        #self.dis  += self.popcount_and_array_2(self.mask_left_less   [i, ti], self.mask_left_greater[j, tj])
        #self.dis  += self.popcount_and_array_3(self.mask_left_greater[i, ti], self.mask_left_less   [j, tj], subset)
        #self.ntie += self.popcount_and_array_3(self.mask_left_equal  [i, ti], self.mask_left_equal  [j, tj], subset)
        pass

    def remove_pair(self, i, j, ti, tj):
        for k in range(self.window_64):
            self.dis  -= self.popcount(self.mask_right_less   [i, ti, k] & self.mask_right_greater[j, tj, k])
            self.dis  -= self.popcount(self.mask_right_greater[i, ti, k] & self.mask_right_less   [j, tj, k])
            self.ntie -= self.popcount(self.mask_right_equal  [i, ti, k] & self.mask_right_equal  [j, tj, k])
        pass

    def get_kendaltau(self):
        return self.compute_tau_pv(self.window, self.tot, self.xtie[self.si, self.ti], 
                                                          self.xtie0[self.si, self.ti], 
                                                          self.xtie1[self.si, self.ti], 
                                                          self.xtie[self.sj, self.tj], 
                                                          self.xtie0[self.sj, self.tj], 
                                                          self.xtie1[self.sj, self.tj], 
                                                          self.ntie, self.dis)

from time import time
                                                          
@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def compute_tau_kendall_overall_online_bitset(tau_corr, data, ids, window_size = 15 * 4, delay_time = 7 * 4, alpha = 0.05):
    #print(ids[0], len(ids))
    nm, nt = data.shape
    corr = kendalltau_corr_online(data, window_size)
    print(nm, nt)
    print(tau_corr.shape)

    y1 = np.zeros(nt, dtype = data.dtype)
    y2 = np.zeros(nt, dtype = data.dtype)
    cur1 = np.zeros(window_size, dtype = data.dtype)
    cur2 = np.zeros(window_size, dtype = data.dtype)
    for i in ids:
        #print(ids[0], '<=', i, '<=', ids[-1], 'percent', (i - ids[0]) / (ids[-1] - ids[0] + 1))
        for j in range(nm):
            for t in range(nt):
                tau_corr[i, j, t] = 0

            for shift in range(-delay_time, delay_time + 1):
                shift_1 = max(0, shift)
                shift_2 = max(0, -shift)

                corr.init(i, j, delay_time - shift_1, delay_time - shift_2)

                for t in range(window_size + delay_time, nt):
                    #print(i, j, shift, t)
                    ktau, pv = corr.get_kendaltau()
                    if ktau > tau_corr[i, j, t] and pv < alpha:
                        #best_shift = shift
                        #best_pv = pv
                        tau_corr[i, j, t] = ktau
                    corr.move_window()
    print(ids[0], '-', ids[-1], 'finish')


