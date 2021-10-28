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


def g_test(config, metric_name, metric_prob, thr, cyclones_events):
    predicted_events = get_metric_indicators(config, metric_name, metric_prob, thr)
    if len(predicted_events) == 0:
        return pd.DataFrame()
    else:
        not_nan_mask = np.logical_not(np.isnan(metric_prob))
        tn = np.sum(np.logical_not(predicted_events) & np.logical_not(cyclones_events) & not_nan_mask)
        fn = np.sum(np.logical_not(predicted_events) & cyclones_events & not_nan_mask)
        fp = np.sum(predicted_events & np.logical_not(cyclones_events) & not_nan_mask)
        tp = np.sum(predicted_events & cyclones_events & not_nan_mask)

        if ((tn == 0) and (fn == 0)) or ((fp == 0) and (tp == 0)):
            g_stat = p_val = tn = fn = fp = tp = 'NA'
        else:
            CM = np.array([[tn, fn], [fp, tp]])
            g_stat, p_val, dof, expctd = chi2_contingency(CM, lambda_="log-likelihood", correction=False)

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


def g_test_for_different_metrics_and_thrs(config, path_name, file_name):
    cyclones_events = np.load("cyclones_events.npz")['arr_0']

    writer = ExcelWriter(file_name)

    metric_names = list(get_metric_names(config, prefix='probability_for_metrics').keys())
    pbar_for_metrics = tqdm(metric_names)

    optimal_results = dict.fromkeys(metric_names, {'prob_for_metric': '', 'g_statistic': -999999, 'f1_score': 'NA',
                                                   'balanced_acc': 'NA', 'matthews_coef': 'NA'})

    ii = 0
    for metric_name in pbar_for_metrics:
        main_metric_name = metric_name[metric_name.find("/") + 1:]
        metric_prob = load_metric(config, metric_name)
        for thr in list(config.g_test_options['thr']):
            pbar_for_metrics.set_postfix({'metric': main_metric_name, 'thr': thr})
            g_stat, p_val, tn, fn, fp, tp = g_test(config, main_metric_name, metric_prob, thr, cyclones_events)
            if g_stat == 'NA':
                f1 = b_acc = mcc = 'NA'
            else:
                f1 = calc_f1_score(float(fn), float(fp), float(tp))
                b_acc = calc_balanced_accuracy(float(tn), float(fn), float(fp), float(tp))
                mcc = calc_matthews_coefficient(float(tn), float(fn), float(fp), float(tp))

            sign = get_sign_for_metric(config, main_metric_name)
            results = pd.DataFrame({'col1': ['metric_name', 'prob_for_metric', 'g-statistic', 'p-value', 'f1_score',
                                             'balanced_acc', 'matthews_coef', '', 'NoI', 'YesI', ''],
                                   'col2': [main_metric_name, sign + str(thr) if type(sign) == str else '', g_stat,
                                            p_val, f1, b_acc, mcc, 'NoE', tn, fp, ''],
                                   'col3': ['', '', '', '', '', '', '', 'YesE', fn, tp, '']})
            #results = pd.concat([results, g_test(config, main_metric_name, metric_prob, thr, cyclones_events)], axis=0)
            results.to_excel(writer, sheet_name=f"thr_{thr}", startrow=ii, index=False, header=False)

            if (g_stat != 'NA') and (g_stat > optimal_results[metric_name]['g_statistic']):
                optimal_results[metric_name] = {'prob_for_metric': sign + str(thr) if type(sign) == str else '',
                                                'g_statistic': g_stat, 'f1_score': f1, 'balanced_acc': b_acc,
                                                'matthews_coef': mcc}
        ii += len(results)
    writer.save()

    return optimal_results


def save_optimal_results_for_g_test(opt_res_dict, file_name):
    df_res = pd.DataFrame(columns=['metric_name', 'prob_for_metric', 'g_statistic', 'f1_score', 'balanced_acc',
                                   'matthews_coef'])
    for metric_name, internal_dict in opt_res_dict.items():
        df_res.loc[len(df_res)] = [metric_name[metric_name.find("/") + 1:]] + \
                                  [v for k, v in opt_res_dict[metric_name].items()]

    df_res.to_excel(file_name, index=False)
