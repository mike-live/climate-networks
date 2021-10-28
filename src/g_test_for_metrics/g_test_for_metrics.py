import numpy as np
import pandas as pd
from pandas import ExcelWriter
import warnings
from tqdm import tqdm
from scipy.stats import chi2_contingency
from metric_store import get_metric_names, load_metric


def get_sign_for_metric(config, metric_name):
    if metric_name in config.g_test_options['less']:
        sign = 'less'
    elif metric_name in config.g_test_options['greater']:
        sign = 'greater'
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
            if sign == 'less':
                predicted_events = metric_prob < thr
            elif sign == 'greater':
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
        CM = np.array([[tn, fn], [fp, tp]])
        g_stat, p_val, dof, expctd = chi2_contingency(CM, lambda_="log-likelihood", correction=False)

        return g_stat, p_val, tn, fn, fp, tp


def g_test_for_different_metrics_and_thrs(config, path_name, file_name):
    cyclones_events = np.load("cyclones_events.npz")['arr_0']

    writer = ExcelWriter(file_name)

    metric_names = list(get_metric_names(config, prefix='probability_for_metrics').keys())
    pbar_for_metrics = tqdm(metric_names)
    ii = 0
    for metric_name in pbar_for_metrics:
        main_metric_name = metric_name[metric_name.find("/") + 1:]
        metric_prob = load_metric(config, metric_name)
        for thr in list(config.g_test_options['thr']):
            pbar_for_metrics.set_postfix({'metric': main_metric_name, 'thr': thr})
            g_stat, p_val, tn, fn, fp, tp = g_test(config, main_metric_name, metric_prob, thr, cyclones_events)
            results = pd.DataFrame({'col1': ['metric_name', 'g-statistic', 'p-value', '', 'NoI', 'YesI', ''],
                                   'col2': [main_metric_name, g_stat, p_val, 'NoE', tn, fp, ''],
                                   'col3': ['', '', '', 'YesE', fn, tp, '']})
            #results = pd.concat([results, g_test(config, main_metric_name, metric_prob, thr, cyclones_events)], axis=0)
            results.to_excel(writer, sheet_name=f"thr_{thr}", startrow=ii, index=False, header=False)
        ii += len(results)
    writer.save()
