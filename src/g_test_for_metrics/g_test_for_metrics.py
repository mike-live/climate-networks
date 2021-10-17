import numpy as np
import pandas as pd
from pandas import ExcelWriter
import warnings
from tqdm import tqdm
from datetime import datetime
from scipy.stats import chi2_contingency
from cyclones_info.cyclones_info import get_cyclone_for_special_number, extension_df_for_cyclone,\
    full_extended_df_for_cyclone, get_cyclones_info, get_cyclones
from metric_store import get_metric_names, load_metric
from plot_network_metrics.utils import get_times_lats_lots


def get_cyclone_area(cur_lat, cur_lon, lats, lons):
    indexes_lat = np.where(lats >= cur_lat)[0]  # lats sorted as >=
    indexes_lon = np.where(lons <= cur_lon)[0]

    message = ''

    if len(indexes_lat) == 0:
        ind_lat = 0
    else:
        ind_lat = indexes_lat[-1]

    if len(indexes_lon) == 0:
        ind_lon = 0
    else:
        ind_lon = indexes_lon[-1]

    if ((ind_lat == 0) or (ind_lat == len(lats)-1)) and (np.abs(cur_lat - lats[ind_lat]) > 1.125):
        message = 'Cyclone outside the grid'
    if ((ind_lon == 0) or (ind_lon == len(lons)-1)) and (np.abs(cur_lon - lons[ind_lon]) > 1.125):
        message = 'Cyclone outside the grid'

    # область = 9 клеток (3 по широте и 3 по долготе)
    start_ind_lat = ind_lat - 1
    end_ind_lat = ind_lat + 2
    start_ind_lon = ind_lon - 1
    end_ind_lon = ind_lon + 2
    if ind_lat == 0:
        start_ind_lat = 0
    if ind_lon == 0:
        start_ind_lon = 0

    return message, start_ind_lat, end_ind_lat, start_ind_lon, end_ind_lon


def get_cyclone_events(cyclones_frame, cyclones_dict, times, lats, lons):
    shapes = (len(lats), len(lons), len(times))
    cyclones_events = np.zeros(shapes, dtype='float')

    for cyclone in cyclones_dict:
        curr_cyc_df = get_cyclone_for_special_number(cyclones_frame, cyclone['number'])
        # дополняем циклон точками каждые три часа (если в таблице нет данных за какое-то время,
        # то берём lon lat как в предыдущей известной временной точке)
        curr_cyc_df = extension_df_for_cyclone(curr_cyc_df)
        curr_cyc_df = full_extended_df_for_cyclone(curr_cyc_df)

        if not curr_cyc_df.empty:
            for k in range(len(curr_cyc_df)):
                d = datetime.strptime(curr_cyc_df['Date (DD/MM/YYYY)'][k] + ' ' + curr_cyc_df['Time (UTC)'][k],
                                      '%d/%m/%Y %H%M')
                ind_time = list(times).index(d.strftime('%Y.%m.%d %H:%M:%S'))
                message, start_ind_lat, end_ind_lat, start_ind_lon, end_ind_lon = get_cyclone_area(float(curr_cyc_df['Latitude (lat.)'][k]),
                                                                                                   float(curr_cyc_df['Longitude (lon.)'][k]),
                                                                                                   lats, lons)
                if message == '':
                    cyclones_events[start_ind_lat:end_ind_lat, start_ind_lon:end_ind_lon, ind_time] = 1

    return cyclones_events


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
        nan_mask = np.isnan(metric_prob)
        predicted_events = np.zeros(metric_prob.shape, dtype='float')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            if sign == 'less':
                predicted_events[metric_prob < thr] = 1
            elif sign == 'greater':
                predicted_events[metric_prob > thr] = 1
        predicted_events[nan_mask] = np.nan
        return predicted_events


def g_test(config, metric_name, metric_prob, thr, cyclones_events):
    predicted_events = get_metric_indicators(config, metric_name, metric_prob, thr)
    if len(predicted_events) == 0:
        return pd.DataFrame()
    else:
        nan_mask = np.isnan(metric_prob)
        cyclones_events_copy = cyclones_events.copy()
        cyclones_events_copy[nan_mask] = np.nan

        tn = np.sum((predicted_events == 0) & (cyclones_events_copy == 0))
        fp = np.sum((predicted_events == 0) & (cyclones_events_copy == 1))
        fn = np.sum((predicted_events == 1) & (cyclones_events_copy == 0))
        tp = np.sum((predicted_events == 1) & (cyclones_events_copy == 1))
        CM = np.array([[tn, fp], [fn, tp]])
        g_stat, p_val, dof, expctd = chi2_contingency(CM, lambda_="log-likelihood", correction=False)

        res_df = pd.DataFrame({'col1': ['metric_name', 'g-statistic', 'p-value', '', 'NoI', 'YesI', ''],
                               'col2': [metric_name, g_stat, p_val, 'NoE', tn, fn, ''],
                               'col3': ['', '', '', 'YesE', fp, tp, '']})
        return res_df


def g_test_for_different_metrics_and_thrs(config, path_name, file_name):
    all_times, all_lats, all_lons = get_times_lats_lots(config)
    cyclones_frame = get_cyclones_info(config)
    cyclones_dict = get_cyclones(cyclones_frame, config.g_test_options)

    file_name_cyclone = path_name / "cyclones_events.npy"
    if not file_name_cyclone.is_file():
        print('Calculation of cyclone events ...')
        file_name_cyclone.parent.mkdir(parents=True, exist_ok=True)
        cyclones_events = get_cyclone_events(cyclones_frame, cyclones_dict, all_times, all_lats, all_lons)
        np.save(file_name_cyclone, cyclones_events)
    else:
        cyclones_events = np.load(file_name_cyclone)

    writer = ExcelWriter(file_name)

    metric_names = list(get_metric_names(config, prefix='probability_for_metrics').keys())
    for thr in tqdm(list(config.g_test_options['thr'])):
        print(f'thr = {thr}')
        results = pd.DataFrame()
        for metric_name in tqdm(metric_names):
            main_metric_name = metric_name[metric_name.find("/") + 1:]
            print(main_metric_name)
            metric_prob = load_metric(config, metric_name)
            results = pd.concat([results, g_test(config, main_metric_name, metric_prob, thr, cyclones_events)], axis=0)
        results.to_excel(writer, index=False, header=False, sheet_name=f"thr_{thr}")
    writer.save()
