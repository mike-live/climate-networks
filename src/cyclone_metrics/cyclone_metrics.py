import numpy as np
import warnings

from cyclones_info.cyclones_info import get_only_known_data, get_lat_lon_for_cyclone, \
    create_cyclone_info_string, get_datetimes_for_cyclone_points, get_cyclone_for_special_number


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

            metric_time_array = metric[ind_lat, ind_lon, :]
            n_greater = len(metric_time_array[np.where(metric_time_array > metric[ind_lat, ind_lon, ind_dt])])
            n_all = len(metric_time_array)
            prob.append(n_greater / n_all)

        local_metric_means_stds[create_cyclone_info_string(cyclone)] = {'times': c_times,
                                                                        'metrics': c_metric,
                                                                        'means': means,
                                                                        'stds': stds,
                                                                        'prob': prob}
    return local_metric_means_stds
