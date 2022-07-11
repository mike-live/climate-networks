import numpy as np
import warnings
from datetime import datetime

from cyclones_info.cyclones_info import get_only_known_data, get_lat_lon_for_cyclone, \
    create_cyclone_info_string, get_datetimes_for_cyclone_points, get_cyclone_for_special_number,\
    extension_df_for_cyclone, full_extended_df_for_cyclone


def compute_mean_std(metric, cyclones, frame, all_times, all_lons, all_lats):

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        means_array = np.nanmean(metric, axis=2)
        stds_array = np.nanstd(metric, axis=2, ddof=1)

    local_metric_means_stds = {}

    for cyclone in cyclones:
        cyclone_frame = get_cyclone_for_special_number(frame, cyclone['number'])
        cyclone_frame = get_only_known_data(cyclone_frame)
        c_lons, c_lats = get_lat_lon_for_cyclone(cyclone_frame)
        c_times = get_datetimes_for_cyclone_points(cyclone_frame)

        c_metric = []
        means = []
        stds = []
        prob = []
        for current_lon, current_lat, current_date_time in zip(c_lons, c_lats, c_times):
            ind_dt = np.where(all_times == current_date_time)[0][0]
            ind_lon = np.argmin(np.abs(all_lons - current_lon))
            ind_lat = np.argmin(np.abs(all_lats - current_lat))

            c_metric.append(metric[ind_lat, ind_lon, ind_dt])
            means.append(means_array[ind_lat, ind_lon])
            stds.append(stds_array[ind_lat, ind_lon])

            if np.isnan(metric[ind_lat, ind_lon, ind_dt]):
                prob.append(np.nan)
            else:
                metric_time_array = metric[ind_lat, ind_lon, :]
                n_greater = len(np.where(metric_time_array > metric[ind_lat, ind_lon, ind_dt])[0])
                n_all = len(metric_time_array)
                prob.append(n_greater / n_all)

        local_metric_means_stds[create_cyclone_info_string(cyclone)] = {'times': c_times,
                                                                        'metrics': c_metric,
                                                                        'means': means,
                                                                        'stds': stds,
                                                                        'prob': prob}
    return local_metric_means_stds


def get_cyclone_area(cur_lat, cur_lon, lats, lons, track_size=2):
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

    if ((ind_lat == 0) or (ind_lat == len(lats)-1)) and (np.abs(cur_lat - lats[ind_lat]) > 0.75):
        message = 'Cyclone outside the grid'
    if ((ind_lon == 0) or (ind_lon == len(lons)-1)) and (np.abs(cur_lon - lons[ind_lon]) > 0.75):
        message = 'Cyclone outside the grid'

    # по умолчанию область = 4 клетки (2 по широте и 2 по долготе)
    window_half = (track_size - 2) // 2
    start_ind_lat = max(0, ind_lat - window_half)
    end_ind_lat = min(ind_lat + 2 + window_half, len(lats))
    start_ind_lon = max(0, ind_lon - window_half)
    end_ind_lon = min(ind_lon + 2 + window_half, len(lons))

    return message, start_ind_lat, end_ind_lat, start_ind_lon, end_ind_lon

def get_cyclone_events(cyclones_frame, cyclones_dict, times, lats, lons, track_size=2, need_shift=False, shift_lo=20 * 8, shift_hi=50 * 8):
    shapes = (len(lats), len(lons), len(times))
    cyclones_events = np.zeros(shapes, dtype='bool')
    
    for cyclone in cyclones_dict:
        curr_cyc_df = get_cyclone_for_special_number(cyclones_frame, cyclone['number'])
        # дополняем циклон точками каждые три часа (если в таблице нет данных за какое-то время,
        # то берём lon lat как в предыдущей известной временной точке)
        curr_cyc_df = extension_df_for_cyclone(curr_cyc_df)
        curr_cyc_df = full_extended_df_for_cyclone(curr_cyc_df)
        if need_shift:
            shift = np.random.randint(shift_lo, shift_hi)
        else:
            shift = 0
        if not curr_cyc_df.empty:
            for k in range(len(curr_cyc_df)):
                d = datetime.strptime(curr_cyc_df['Date (DD/MM/YYYY)'][k] + ' ' + curr_cyc_df['Time (UTC)'][k],
                                      '%d/%m/%Y %H%M')
                ind_time = np.searchsorted(times, d.strftime('%Y.%m.%d %H:%M:%S'))
                ind_time = (ind_time + shift) % shapes[2]
                message, start_ind_lat, end_ind_lat, \
                start_ind_lon, end_ind_lon = get_cyclone_area(float(curr_cyc_df['Latitude (lat.)'][k]),
                                                              float(curr_cyc_df['Longitude (lon.)'][k]),
                                                              lats, lons, track_size)
                if message == '':
                    cyclones_events[start_ind_lat:end_ind_lat, start_ind_lon:end_ind_lon, ind_time] = True

    return cyclones_events

def compute_max_deviation(metric, cyclones_frame, cyclones_dict, all_times, all_lons, all_lats, opt_func='max', track_size=2):
    local_metric_max_deviation = {}

    for cyclone in cyclones_dict:
        curr_cyc_df = get_cyclone_for_special_number(cyclones_frame, cyclone['number'])
        # дополняем циклон точками каждые три часа (если в таблице нет данных за какое-то время,
        # то берём lon lat как в предыдущей известной временной точке)
        curr_cyc_df = extension_df_for_cyclone(curr_cyc_df)
        curr_cyc_df = full_extended_df_for_cyclone(curr_cyc_df)
    
        c_metric_max_deviation = []
        c_times = []
        if not curr_cyc_df.empty:
            for k in range(len(curr_cyc_df)):
                d = datetime.strptime(curr_cyc_df['Date (DD/MM/YYYY)'][k] + ' ' + curr_cyc_df['Time (UTC)'][k],
                                        '%d/%m/%Y %H%M')
                cur_time = d.strftime('%Y.%m.%d %H:%M:%S')
                ind_time = np.searchsorted(all_times, cur_time)
                
                message, start_ind_lat, end_ind_lat, \
                start_ind_lon, end_ind_lon = get_cyclone_area(float(curr_cyc_df['Latitude (lat.)'][k]),
                                                                float(curr_cyc_df['Longitude (lon.)'][k]),
                                                                all_lats, all_lons, track_size)
                res = np.nan
                if message == '':
                    if opt_func == 'max':
                        res = np.nanmax(metric[start_ind_lat:end_ind_lat, start_ind_lon:end_ind_lon, ind_time])
                    elif opt_func == 'min':
                        res = np.nanmin(metric[start_ind_lat:end_ind_lat, start_ind_lon:end_ind_lon, ind_time])
                c_metric_max_deviation.append(res)
                c_times.append(cur_time)

        local_metric_max_deviation[create_cyclone_info_string(cyclone)] = {
            'times': c_times,
            'metrics': c_metric_max_deviation
        }
    return local_metric_max_deviation

def all_cyclones_iterator(cyclones_frame, cyclones_dict):
    
    for cyclone in cyclones_dict:
        cyclone_df = get_cyclone_for_special_number(cyclones_frame, cyclone['number'])
        cyclone_df = extension_df_for_cyclone(cyclone_df)
        cyclone_df = full_extended_df_for_cyclone(cyclone_df)
    
        if not cyclone_df.empty:
            yield cyclone, cyclone_df

def cyclone_iterator(cyclone_df, all_times, all_lons, all_lats, track_size=2):
    for k in range(len(cyclone_df)):
        d = datetime.strptime(cyclone_df['Date (DD/MM/YYYY)'][k] + ' ' + cyclone_df['Time (UTC)'][k],
                                '%d/%m/%Y %H%M')
        cur_time = d.strftime('%Y.%m.%d %H:%M:%S')
        ind_time = np.searchsorted(all_times, cur_time)
        
        message, start_ind_lat, end_ind_lat, \
        start_ind_lon, end_ind_lon = get_cyclone_area(float(cyclone_df['Latitude (lat.)'][k]),
                                                      float(cyclone_df['Longitude (lon.)'][k]),
                                                      all_lats, all_lons, track_size)
        yield (k, cur_time, ind_time), message == '', (start_ind_lat, end_ind_lat, start_ind_lon, end_ind_lon)
    

def compute_metric_in_track(metric, cyclones_frame, cyclones_dict, all_times, all_lons, all_lats, track_size=2):
    local_metric_metric_in_track = {}
    for cyclone, cyclone_df in all_cyclones_iterator(cyclones_frame, cyclones_dict):
        c_metric_metric_in_track = []
        c_times = []
        for cyclone_time, is_inside, cyclone_region in cyclone_iterator(cyclone_df, all_times, all_lons, all_lats, track_size=track_size):
            k, cur_time, ind_time = cyclone_time
            start_ind_lat, end_ind_lat, start_ind_lon, end_ind_lon = cyclone_region
            res = np.nan
            if is_inside:
                res = metric[start_ind_lat:end_ind_lat, start_ind_lon:end_ind_lon, ind_time]
            c_metric_metric_in_track.append(res)
            c_times.append(cur_time)

            local_metric_metric_in_track[create_cyclone_info_string(cyclone)] = {
                'times': c_times,
                'metrics': c_metric_metric_in_track
            }
    return local_metric_metric_in_track
