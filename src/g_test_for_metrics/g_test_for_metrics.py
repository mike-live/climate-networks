import math
import numpy as np
import pandas as pd
from pandas import ExcelWriter
import warnings
from tqdm import tqdm
from scipy.stats import chi2_contingency
from metric_store import get_metric_names, load_metric


def get_sign_for_metric(config, metric_name):
    if metric_name in config.g_test_options['less']:
        sign = '<'
    elif metric_name in config.g_test_options['greater']:
        sign = '>'
    else:
        print("There is no boxplot for probability of ", metric_name)
        sign = -1
    return sign


def get_metric_indicators(config, metric_name, metric_prob, thr):
    sign = get_sign_for_metric(config, metric_name)
    if sign == -1:
        return np.array([])
    else:
        predicted_events = np.zeros(metric_prob.shape, dtype='bool')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            if sign == '<':
                predicted_events = metric_prob < thr
            elif sign == '>':
                predicted_events = metric_prob > thr
        return predicted_events

def g_test(contigency_table):
    tn, fn, fp, tp = contigency_table.flatten()
    if ((tn == 0) and (fn == 0)) or ((fp == 0) and (tp == 0)):
        g_stat = p_val = tn = fn = fp = tp = np.nan
    else:
        g_stat, p_val, dof, expctd = chi2_contingency(contigency_table, lambda_="log-likelihood", correction=False)
    return g_stat, p_val

def g_test_events(cyclones_events, predicted_events, available_mask, subset_mask=None):
    if len(predicted_events) == 0:
        g_stat = p_val = tn = fn = fp = tp = np.nan
    else:
        not_nan_mask = available_mask
        if not subset_mask is None:
            subset_mask &= not_nan_mask
        else:
            subset_mask = not_nan_mask
        tn = np.sum(~predicted_events & ~cyclones_events & subset_mask)
        fn = np.sum(~predicted_events &  cyclones_events & subset_mask)
        fp = np.sum( predicted_events & ~cyclones_events & subset_mask)
        tp = np.sum( predicted_events &  cyclones_events & subset_mask)
        g_stat, p_val = g_test(np.array([[tn, fp], [fp, tp]]))

    return g_stat, p_val, tn, fn, fp, tp


def calc_f1_score(fn, fp, tp):
    # F1 score does not take into account how many negative examples there are in the dataset
    if (tp == 0) and (fp == 0) and (fn == 0):
        f1_score = 0
    else:
        f1_score = (2 * tp) / (2 * tp + fp + fn)
    return f1_score


def calc_balanced_accuracy(tn, fn, fp, tp):
    if (tp + fn == 0) and (tn + fp == 0):
        b_acc = 0
    else:
        b_acc = 0.5 * ((tp / (tp + fn)) + (tn / (tn + fp)))
    return b_acc


def calc_matthews_coefficient(tn, fn, fp, tp):
    if (tp + fp == 0) or (tp + fn == 0) or (tn + fp == 0) or (tn + fn == 0):
        mcc = 0
    else:
        denominator1 = math.sqrt(tp + fp) * math.sqrt(tp + fn)
        denominator2 = math.sqrt(tn + fp) * math.sqrt(tn + fn)
        mcc = ((tp / denominator1) * (tn / denominator2)) - ((fp / denominator1) * (fn / denominator2))
    return mcc

from scipy.signal import fftconvolve
def compute_shifted_bitwiseand_fft(x, y):
    x = x[::-1]
    y = np.concatenate([y, y])
    z = fftconvolve(x, y, 'same')
    return np.rint(z.real).astype(np.int32)

def g_test_fft(cyclones_events, predicted_events, available_mask, w_start):
    A = B = C = D = None
    
    for i in range(cyclones_events.shape[0]):
        for j in range(cyclones_events.shape[1]):
            if not available_mask[i, j, 0]:
                continue
            x, y = cyclones_events[i, j, w_start:].flatten(), predicted_events[i, j, w_start:].flatten()

            d = compute_shifted_bitwiseand_fft(x, y)
            b = x.sum() - d
            c = y.sum() - d
            a = (len(x) - x.sum()) - c
            
            if D is None:
                D = d
                B = b
                C = c
                A = a
            else:
                D += d
                B += b
                C += c
                A += a
    from scipy.stats import chi2_contingency
    g_stats_surrogate = []
    for i in range(len(A)):
        if ((A[i] == 0) and (B[i] == 0)) or ((C[i] == 0) and (D[i] == 0)):
            g_stat = p_val = tn = fn = fp = tp = np.nan
        else:
            CM = np.array([[A[i], B[i]], [C[i], D[i]]])
            g_stat, p_val, dof, expctd = chi2_contingency(CM, lambda_="log-likelihood", correction=False)
        g_stats_surrogate.append(g_stat)
    return g_stats_surrogate

def compute_g_stat_surrogate_cyclone_shifts(config, cyclones_events, predicted_events, available_mask, method='fft', num_surrogate=25000):
    if method == 'random':
        g_stats_surrogate = []
        for id_surrogate in tqdm(range(num_surrogate)):
            random_shift = np.random.randint(cyclones_events.shape[2])
            surrogate_events = np.roll(cyclones_events, random_shift, 2)
            g_stat_surrogate, *_ = g_test_events(surrogate_events, predicted_events, available_mask)
            g_stats_surrogate.append(g_stat_surrogate)
    elif method == 'fft':
        g_stats_surrogate = g_test_fft(cyclones_events, predicted_events, available_mask, w_start=config.correlations['window_size'])
    return g_stats_surrogate

def g_test_for_different_metrics_and_thrs(config, path_name, file_name):
    track_size = str(config.g_test_options['track_size'])
    cyclones_events_name = f'cyclone_events_{track_size}'
    cyclones_events = np.load("cyclones_events.npz")[cyclones_events_name]

    metric_names = list(get_metric_names(config, prefix='probability_for_metrics').keys()) # network_metrics/LCC_w
    pbar_for_metrics = tqdm(metric_names)

    results = dict.fromkeys([f"thr_{thr}" for thr in list(config.g_test_options['thr'])],\
                            pd.DataFrame(columns=['col1', 'col2', 'col3']))
    from corr_network import load_data, get_available_mask
    data = load_data(config)
    available_mask = get_available_mask(data)
    available_mask = np.repeat(available_mask[:, :, np.newaxis], data.shape[2], axis=2)
    print(available_mask.shape)
    for metric_name in pbar_for_metrics:
        main_metric_name = metric_name[metric_name.find("/") + 1:]
        metric_prob = load_metric(config, metric_name)
        for thr in list(config.g_test_options['thr']):
            pbar_for_metrics.set_postfix({'metric': main_metric_name, 'thr': thr})
            predicted_events = get_metric_indicators(config, main_metric_name, metric_prob, thr)                
            g_stat, p_val, tn, fn, fp, tp = g_test_events(cyclones_events, predicted_events, available_mask)
            if config.g_test_options['need_surrogate']:
                #g_stat, p_val, tn, fn, fp, tp = g_test(config, main_metric_name, metric_prob, thr, cyclones_events, subset_mask)
                g_stats_surrogate = compute_g_stat_surrogate_cyclone_shifts(config, cyclones_events, predicted_events, available_mask)
                surrogate_p_val = np.sum(np.array(g_stats_surrogate) > g_stat)
                max_g_stat = np.max(g_stats_surrogate)
            else:
                surrogate_p_val = np.nan
                max_g_stat = np.nan
                g_stats_surrogate = []


            if g_stat == 'NA':
                f1 = b_acc = mcc = 'NA'
            else:
                f1 = calc_f1_score(float(fn), float(fp), float(tp))
                b_acc = calc_balanced_accuracy(float(tn), float(fn), float(fp), float(tp))
                mcc = calc_matthews_coefficient(float(tn), float(fn), float(fp), float(tp))

            sign = get_sign_for_metric(config, main_metric_name)
            results[f"thr_{thr}"] = pd.concat([results[f"thr_{thr}"],
                                               pd.DataFrame({'col1': ['metric_name', 'prob_for_metric', 'g-statistic',
                                                                      'surrogate p-value', 'f1_score', 'balanced_acc',
                                                                      'matthews_coef', '', 'NoI', 'YesI', ''],
                                                             'col2': [main_metric_name,
                                                                      sign + str(thr) if type(sign) == str else '',
                                                                      g_stat, [surrogate_p_val, max_g_stat, g_stats_surrogate], f1, b_acc, mcc, 'NoE', tn, fp, ''],
                                                             'col3': ['', '', '', '', '', '', '', 'YesE', fn, tp, '']})],
                                              axis=0)

    return results


def save_full_results_for_g_test(res_dict, file_name):
    writer = ExcelWriter(file_name)
    for key, value in res_dict.items():
        value.to_excel(writer, sheet_name=key, startrow=0, index=False, header=False)
    writer.save()