from numba import float64, int32, int64, uint64, int8, jit, prange, config, threading_layer
from numba.experimental import jitclass
import math
from kendalltau_helpers import *
import numba_config
import numpy as np


spec_kendal_tau = [
    ('kendall_dis_x', int64[:]),
    ('kendall_dis_y', int64[:]),
    ('kendall_dis_xx', int64[:]),
    ('kendall_dis_yy', int64[:]),
    ('kendalltau_x', int64[:]),
    ('kendalltau_y', int64[:]),
    ('kendalltau_tmp_x', float64[:]),
    ('kendalltau_tmp_y', float64[:]),
    ('kendalltau_tmp_y2', int64[:]),
    ('bincount_cnt', int64[:]),
    ('pvalue_sum', float64[:]),
    ('window', int64),
]

@jitclass(spec_kendal_tau)
class kendaltau_corr:
    def __init__(self, window):
        self.window = window
        self.kendall_dis_x = np.zeros(self.window, np.int64)
        self.kendall_dis_y = np.zeros(self.window, np.int64)
        self.kendall_dis_xx = np.zeros(self.window, np.int64)
        self.kendall_dis_yy = np.zeros(self.window, np.int64)
        
        self.kendalltau_x = np.zeros(self.window, np.int64)
        self.kendalltau_y = np.zeros(self.window, np.int64)
        self.kendalltau_tmp_x = np.zeros(self.window, np.float64)
        self.kendalltau_tmp_y = np.zeros(self.window, np.float64)
        self.kendalltau_tmp_y2 = np.zeros(self.window, np.int64)
        
        self.bincount_cnt = np.zeros(self.window + 1, np.int64)
        if self.window <= 33:
            self.pvalue_sum = np.zeros(self.window * self.window, np.float64)
            self.init_pvalue()
        #else:
        #    self.pvalue_sum = np.zeros(1, np.float64)
        
    def kendall_dis(self, x0, y0):
        self.kendall_dis_x[:] = x0[:]
        self.kendall_dis_y[:] = y0[:]
        
        self.kendall_dis_yy[:] = 0
        self.kendall_dis_xx[:] = 0

        res = merge_dis(self.kendall_dis_x, self.kendall_dis_y, \
                        self.kendall_dis_xx, self.kendall_dis_yy, 0, self.window - 1)
        #assert(np.all(np.diff(y) >= 0))
        return res

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

    def kendalltau(self, x0, y0, initial_lexsort=None, nan_policy='propagate'): # method='auto'
        """
        Calculate Kendall's tau, a correlation measure for ordinal data.

        Kendall's tau is a measure of the correspondence between two rankings.
        Values close to 1 indicate strong agreement, values close to -1 indicate
        strong disagreement.  This is the 1945 "tau-b" version of Kendall's
        tau [2]_, which can account for ties and which reduces to the 1938 "tau-a"
        version [1]_ in absence of ties.

        Parameters
        ----------
        x, y : array_like
            Arrays of rankings, of the same shape. If arrays are not 1-D, they will
            be flattened to 1-D.
        initial_lexsort : bool, optional
            Unused (deprecated).
        nan_policy : {'propagate', 'raise', 'omit'}, optional
            Defines how to handle when input contains nan.
            The following options are available (default is 'propagate'):

              * 'propagate': returns nan
              * 'raise': throws an error
              * 'omit': performs the calculations ignoring nan values
        method : {'auto', 'asymptotic', 'exact'}, optional
            Defines which method is used to calculate the p-value [5]_.
            The following options are available (default is 'auto'):

              * 'auto': selects the appropriate method based on a trade-off between
                speed and accuracy
              * 'asymptotic': uses a normal approximation valid for large samples
              * 'exact': computes the exact p-value, but can only be used if no ties
                are present

        Returns
        -------
        correlation : float
           The tau statistic.
        pvalue : float
           The two-sided p-value for a hypothesis test whose null hypothesis is
           an absence of association, tau = 0.

        See Also
        --------
        spearmanr : Calculates a Spearman rank-order correlation coefficient.
        theilslopes : Computes the Theil-Sen estimator for a set of points (x, y).
        weightedtau : Computes a weighted version of Kendall's tau.

        Notes
        -----
        The definition of Kendall's tau that is used is [2]_::

          tau = (P - Q) / sqrt((P + Q + T) * (P + Q + U))

        where P is the number of concordant pairs, Q the number of discordant
        pairs, T the number of ties only in `x`, and U the number of ties only in
        `y`.  If a tie occurs for the same pair in both `x` and `y`, it is not
        added to either T or U.

        References
        ----------
        .. [1] Maurice G. Kendall, "A New Measure of Rank Correlation", Biometrika
               Vol. 30, No. 1/2, pp. 81-93, 1938.
        .. [2] Maurice G. Kendall, "The treatment of ties in ranking problems",
               Biometrika Vol. 33, No. 3, pp. 239-251. 1945.
        .. [3] Gottfried E. Noether, "Elements of Nonparametric Statistics", John
               Wiley & Sons, 1967.
        .. [4] Peter M. Fenwick, "A new data structure for cumulative frequency
               tables", Software: Practice and Experience, Vol. 24, No. 3,
               pp. 327-336, 1994.
        .. [5] Maurice G. Kendall, "Rank Correlation Methods" (4th Edition),
               Charles Griffin & Co., 1970.

        Examples
        --------
        >>> from scipy import stats
        >>> x1 = [12, 2, 1, 12, 2]
        >>> x2 = [1, 4, 7, 1, 0]
        >>> tau, p_value = stats.kendalltau(x1, x2)
        >>> tau
        -0.47140452079103173
        >>> p_value
        0.2827454599327748

        """
        
        if x0.size != y0.size:
            #raise ValueError("All inputs to `kendalltau` must be of the same size, "
            #                 "found x-size %s and y-size %s" % (x.size, y.size))
            pass
        elif not x0.size or not y0.size:
            return np.nan, np.nan  # Return NaN if arrays are empty

        # check both x and y
        """
        cnx, npx = _contains_nan(x, nan_policy)
        cny, npy = _contains_nan(y, nan_policy)
        contains_nan = cnx or cny
        if npx == 'omit' or npy == 'omit':
            nan_policy = 'omit'

        if contains_nan and nan_policy == 'propagate':
            return KendalltauResult(np.nan, np.nan)

        elif contains_nan and nan_policy == 'omit':
            x = ma.masked_invalid(x)
            y = ma.masked_invalid(y)
            return mstats_basic.kendalltau(x, y, method=method)
        if initial_lexsort is not None:  # deprecate to drop!
            warnings.warn('"initial_lexsort" is gone!')
        """
        
        size = x0.size
        #perm = np.argsort(y0)  # sort on y and convert y to dense ranks
        mysort(y0, x0, self.kendalltau_tmp_y, self.kendalltau_tmp_x)

        y = self.kendalltau_y
        y[0] = 1
        for i in range(len(y) - 1):
            if y0[i] != y0[i + 1]:
                y[i + 1] = y[i] + 1
            else:
                y[i + 1] = y[i]

        #y[np.concatenate([[True], y0[1:] != y0[:-1]])] = 1
        #y = y.cumsum()

        # stable sort on x and convert x to dense ranks
        #perm = np.argsort(x0, kind='mergesort')
        mysort(x0, y, self.kendalltau_tmp_x, self.kendalltau_tmp_y2, kind = 1)
        x = self.kendalltau_x
        x[0] = 1
        for i in range(len(x) - 1):
            if x0[i] != x0[i + 1]:
                x[i + 1] = x[i] + 1
            else:
                x[i + 1] = x[i]
        #x[np.concatenate([[True], x0[1:] != x0[:-1]])] = 1
        #x = x.cumsum()
        #print(x, y)

        dis = self.kendall_dis(x, y)  # discordant pairs
        #print(dis)

        #obs = np.r_[True, (x[1:] != x[:-1]) | (y[1:] != y[:-1]), True]
        
        #obs = np.zeros(len(x) + 1, np.int64)
        #cur = [0]
        #for i in range(len(x) - 1):
        #    if x[i] != x[i + 1] or y[i] != y[i + 1]:
        #        cur.append(i + 1)
        #cur.append(len(x))
        #obs[np.concatenate([[True], (x[1:] != x[:-1]) | (y[1:] != y[:-1]), [True]])] = 1
        #cur = np.nonzero(obs)[0]

        #cnt = np.diff(np.array(cur, np.int64))
        ntie = 0
        prv = 0
        for i in range(len(x) - 1):
            if x[i] != x[i + 1] or y[i] != y[i + 1]:
                cur = i + 1 - prv
                ntie += cur * (cur - 1) // 2
                prv = i + 1
        cur = len(x) - prv
        ntie += cur * (cur - 1) // 2
        #cnt = np.array(cur)
        
        #ntie = (cnt * (cnt - 1) // 2).sum()  # joint ties
        xtie, x0, x1 = self.count_rank_tie(x)     # ties in x, stats
        ytie, y0, y1 = self.count_rank_tie(y)     # ties in y, stats

        tot = size * (size - 1) // 2

        if xtie == tot or ytie == tot:
            return np.nan, np.nan
        return self.compute_tau_pv(size, tot, xtie, x0, x1, ytie, y0, y1, ntie, dis)


    def compute_tau_pv(self, size, tot, xtie, x0, x1, ytie, y0, y1, ntie, dis):
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
        return tau, pvalue

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def compute_delayed_kendall_tau(corr, cur1, cur2, y1, y2, t, delay_time, window_size, alpha):
    mtau = 0.0
    best_shift = np.nan
    best_pv = np.nan
    for shift in range(-delay_time, delay_time + 1):
        #print(t, shift)
        shift_1 = max(0, shift)
        shift_2 = max(0, -shift)
        '''for i in range(window_size):
            cur1[i] = y1[t - window_size - shift_1 + i]
            cur2[i] = y2[t - window_size - shift_1 + i]'''
        cur1[:] = y1[t - window_size - shift_1:t - shift_1]
        cur2[:] = y2[t - window_size - shift_2:t - shift_2]
        '''ktau = 0
        for i in range(len(cur1)):
            ktau += cur1[i] + cur2[i]'''
        #ktau = cur1[0]
        #pv = cur2[-1]
        ktau, pv = corr.kendalltau(cur1, cur2)
        #print(ktau, pv)
        #ktau = ktau_res.correlation
        #pv = ktau_res.pvalue
        if ktau > mtau and pv < alpha:
            mtau = ktau
            best_shift = shift
            best_pv = pv
    #print(mtau)
    return mtau, best_shift, best_pv

@jit(nopython = numba_config.nopython, nogil = numba_config.nogil, cache = numba_config.cache)
def compute_tau_kendall_overall(tau_corr, data, ids, window_size = 15 * 4, delay_time = 7 * 4, alpha = 0.05):
    #print(ids[0], len(ids))
    nm, nt = data.shape
    #tau_corr = np.zeros((nm, nm, nt), dtype = np.float64)
    #tau_tmp = np.zeros((nm, nt), dtype = np.float64)
    corr = kendaltau_corr(window_size)
    y1 = np.zeros(nt, dtype = data.dtype)
    y2 = np.zeros(nt, dtype = data.dtype)
    ytmp1 = np.zeros(window_size, dtype = data.dtype)
    ytmp2 = np.zeros(window_size, dtype = data.dtype)
    for i in ids:
        print(ids[0], '<=', i, '<=', ids[-1], 'percent', (i - ids[0]) / (ids[-1] - ids[0] + 1))
        for j in range(nm):
            for t in range(nt):
                y1[t] = data[i, t]
                y2[t] = data[j, t]
            for t in range(window_size + delay_time, nt):
                #print(i, j, t)
                mtau, _, best_pv = compute_delayed_kendall_tau(corr, ytmp1, ytmp2, y1, y2, t, delay_time, window_size, alpha)
                '''mtau = 0
                for q in range(window_size):
                    mtau += y1[t - q] + y2[t - q]'''
                #print(i, j, mtau, best_pv)
                tau_corr[i, j, t] = mtau    #return 0
    print(ids[0], '-', ids[-1], 'finish')
