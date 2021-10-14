import sys
import numpy as np
import pandas as pd
from datetime import datetime
from more_itertools import unique_everseen
from scipy.stats import chi2_contingency
from cyclones_info.cyclones_info import get_cyclone_for_special_number, extension_df_for_cyclone,\
    full_extended_df_for_cyclone


def get_sign_and_thr(config, metric_name):
    sign = ''
    if metric_name in config.g_test_options['less']:
        sign = 'less'
    elif metric_name in config.g_test_options['greater']:
        sign = 'greater'
    else:
        print("There is no boxplot for", metric_name)
        sys.exit()

    thr = config.g_test_options['thr']

    return sign, thr


def get_events(config, metric_name, metric, cyclones_frame, times, lons, lats):
    lons.sort()
    lats.sort()
    shapes = (len(lats), len(lons), len(times))
    cyclones_events = np.zeros(shapes, dtype='int')
    predicted_events = np.zeros(shapes, dtype='int')

    sign, thr = get_sign_and_thr(config, metric_name)

    for cur_cyclone in metric.items():
        cyclone_number = "_".join([cur_cyclone[0].split("_")[2], cur_cyclone[0].split("_")[0]])
        # Вероятности вычислялись только в указанных в таблице точках циклона
        cur_times = (cur_cyclone[1]['times'])
        cur_times = np.array([datetime.strptime(dt, '%Y.%m.%d %H:%M:%S') for dt in cur_times])
        cur_prob = np.array(cur_cyclone[1]['prob'])

        if len(cur_times) != 0:
            curr_cyc_df = get_cyclone_for_special_number(cyclones_frame, cyclone_number)
            # дополняем циклон точками каждые три часа (если в таблице нет данных за какое-то время,
            # то берём lon lat как в предыдущей известной временной точке)
            curr_cyc_df = extension_df_for_cyclone(curr_cyc_df)
            curr_cyc_df = full_extended_df_for_cyclone(curr_cyc_df)

            for k in range(len(curr_cyc_df)):
                d = datetime.strptime(curr_cyc_df['Date (DD/MM/YYYY)'][k] + ' ' + curr_cyc_df['Time (UTC)'][k], '%d/%m/%Y %H%M')
                # Если в какой-то временной точке нет информации о вероятности, то вероятность берётся из предыдущей
                # известной временной точки
                indices = np.where(cur_times <= d)[0]
                if len(indices) != 0:
                    pr = cur_prob[indices[-1]]
                else:
                    pr = cur_prob[0]

                # Рассматриваются только точки, в которых метрика посчитана (метрика и вероятность не nan)
                if not np.isnan(pr):
                    ind_time = list(times).index(d.strftime('%Y.%m.%d %H:%M:%S'))
                    ind_lon = np.argmin(np.abs(lons - float(curr_cyc_df['Longitude (lon.)'][k])))
                    ind_lat = np.argmin(np.abs(lats - float(curr_cyc_df['Latitude (lat.)'][k])))

                    cyclones_events[ind_lat-1:ind_lat+1, ind_lon-1:ind_lon+1, ind_time] = 1   # 2 клетки
                    #xx, yy = np.meshgrid(lons, lats) # lons, lats д б отсортрованы по возрастанию
                    #cyclones_events[:, :, ind_time][(xx - float(curr_cyc_df['Longitude (lon.)'][k])) ** 2 +
                                                            #(yy - float(curr_cyc_df['Latitude (lat.)'][k])) ** 2 <= radius ** 2] = 1

                    if (sign == 'less' and pr < thr) or (sign == 'greater' and pr > thr):
                        predicted_events[ind_lat-1:ind_lat+1, ind_lon-1:ind_lon+1, ind_time] = 1

    return cyclones_events, predicted_events


def g_test(config, metric_name, metric, cyclones_frame, times, lats, lons):
    cyclones_events, predicted_events = get_events(config, metric_name, metric, cyclones_frame, times, lons, lats)
    tn = np.sum((predicted_events == 0) & (cyclones_events == 0))
    fp = np.sum((predicted_events == 0) & (cyclones_events == 1))
    fn = np.sum((predicted_events == 1) & (cyclones_events == 0))
    tp = np.sum((predicted_events == 1) & (cyclones_events == 1))
    CM = np.array([[tn, fp], [fn, tp]])
    g_stat, p_val, dof, expctd = chi2_contingency(CM, lambda_="log-likelihood", correction=False)

    res_df = pd.DataFrame({'col1': ['metric_name', 'g-statistic', 'p-value', '', 'NoI', 'YesI', ''],
                           'col2': [metric_name, g_stat, p_val, 'NoE', tn, fn, ''],
                           'col3': ['', '', '', 'YesE', fp, tp, '']})

    return res_df
