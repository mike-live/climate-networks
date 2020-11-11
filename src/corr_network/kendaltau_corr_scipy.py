import numpy as np
import scipy
import numba as nb
from numba import float64, int32, jit
#from scipy.stats import kendalltau
from scipy.stats._stats import _kendall_dis
from collections import namedtuple
from tqdm import tqdm
from scipy import special
import os
import math

KendalltauResult = namedtuple('KendalltauResult', ('correlation', 'pvalue'))

def kendalltau(x, y, initial_lexsort=None, nan_policy='propagate', method='auto'):
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
    x = np.asarray(x).ravel()
    y = np.asarray(y).ravel()

    if x.size != y.size:
        raise ValueError("All inputs to `kendalltau` must be of the same size, "
                         "found x-size %s and y-size %s" % (x.size, y.size))
    elif not x.size or not y.size:
        return KendalltauResult(np.nan, np.nan)  # Return NaN if arrays are empty

    # check both x and y
    '''
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
    '''
    def count_rank_tie(ranks):
        cnt = np.bincount(ranks).astype('int64', copy=False)
        cnt = cnt[cnt > 1]
        return ((cnt * (cnt - 1) // 2).sum(),
            (cnt * (cnt - 1.) * (cnt - 2)).sum(),
            (cnt * (cnt - 1.) * (2*cnt + 5)).sum())

    size = x.size
    perm = np.argsort(y)  # sort on y and convert y to dense ranks
    x, y = x[perm], y[perm]
    y = np.r_[True, y[1:] != y[:-1]].cumsum(dtype=np.intp)

    # stable sort on x and convert x to dense ranks
    perm = np.argsort(x, kind='mergesort')
    x, y = x[perm], y[perm]
    x = np.r_[True, x[1:] != x[:-1]].cumsum(dtype=np.intp)

    dis = _kendall_dis(x, y)  # discordant pairs

    obs = np.r_[True, (x[1:] != x[:-1]) | (y[1:] != y[:-1]), True]
    cnt = np.diff(np.nonzero(obs)[0]).astype('int64', copy=False)

    ntie = (cnt * (cnt - 1) // 2).sum()  # joint ties
    xtie, x0, x1 = count_rank_tie(x)     # ties in x, stats
    ytie, y0, y1 = count_rank_tie(y)     # ties in y, stats

    tot = (size * (size - 1)) // 2

    if xtie == tot or ytie == tot:
        return KendalltauResult(np.nan, np.nan)

    # Note that tot = con + dis + (xtie - ntie) + (ytie - ntie) + ntie
    #               = con + dis + xtie + ytie - ntie
    con_minus_dis = tot - xtie - ytie + ntie - 2 * dis
    tau = con_minus_dis / np.sqrt(tot - xtie) / np.sqrt(tot - ytie)
    # Limit range to fix computational errors
    tau = min(1., max(-1., tau))

    if method == 'exact' and (xtie != 0 or ytie != 0):
        raise ValueError("Ties found, exact method cannot be used.")

    if method == 'auto':
        if (xtie == 0 and ytie == 0) and (size <= 33 or min(dis, tot-dis) <= 1):
            method = 'exact'
        else:
            method = 'asymptotic'

    if xtie == 0 and ytie == 0 and method == 'exact':
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
            pvalue = 2.0/math.factorial(size) if size < 171 else 0.0
        elif c == 1:
            pvalue = 2.0/math.factorial(size-1) if (size-1) < 171 else 0.0
        elif 2*c == tot:
            pvalue = 1.0
        else:
            new = [0.0]*(c+1)
            new[0] = 1.0
            new[1] = 1.0
            for j in range(3,size+1):
                old = new[:]
                for k in range(1,min(j,c+1)):
                    new[k] += new[k-1]
                for k in range(j,c+1):
                    new[k] += new[k-1] - old[k-j]
            pvalue = 2.0*sum(new)/math.factorial(size) if size < 171 else 0.0

    elif method == 'asymptotic':
        # con_minus_dis is approx normally distributed with this variance [3]_
        var = (size * (size - 1) * (2.*size + 5) - x1 - y1) / 18. + (
            2. * xtie * ytie) / (size * (size - 1)) + x0 * y0 / (9. *
            size * (size - 1) * (size - 2))
        pvalue = special.erfc(np.abs(con_minus_dis) / np.sqrt(var) / np.sqrt(2))
    else:
        raise ValueError("Unknown method "+str(method)+" specified, please use auto, exact or asymptotic.")

    return KendalltauResult(tau, pvalue)


def compute_delayed_kendall_tau(y1, y2, t, delay_time, window_size, alpha):
    mtau = 0.0
    best_shift = np.nan
    best_pv = np.nan
    for shift in range(-delay_time, delay_time + 1):
        shift_1 = max(0, shift)
        shift_2 = max(0, -shift)
        cur1 = y1[t - window_size - shift_1:t - shift_1]
        cur2 = y2[t - window_size - shift_2:t - shift_2]
        ktau, pv = kendalltau(cur1, cur2)
        #print(ktau, pv)
        #ktau = ktau_res.correlation
        #pv = ktau_res.pvalue
        if ktau > mtau and pv < alpha:
            mtau = ktau
            best_shift = shift
            best_pv = pv
    #print(mtau)
    return mtau, best_shift, best_pv

def compute_tau_kendall_overall(data, window_size = 15, delay_time = 7, alpha = 0.05):
    nm, nt = data.shape
    tau_corr = np.zeros((nm, nm, nt), dtype = np.float32)
    for i in tqdm(range(nm)):
        for j in range(nm):
            y1 = data[i, :].flatten()
            y2 = data[j, :].flatten()
            for t in range(window_size + delay_time, nt):
                mtau, _, best_pv = compute_delayed_kendall_tau(y1, y2, t, delay_time, window_size, alpha)
                #print(i, j, mtau, best_pv)
                tau_corr[i, j, t] = mtau
    return tau_corr
