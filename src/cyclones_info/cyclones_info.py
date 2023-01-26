import numpy as np
import pandas as pd
from datetime import timedelta, datetime


def check_is_number(st):
    try:
        float(st)
        return True
    except ValueError:
        return False


def get_cyclones_info(config):
    cyclones_frame = pd.read_csv(config.cyclones_info['cyclones_file_name'], sep='\t', dtype={'Time (UTC)': str})
    cyclones_frame.fillna('', inplace=True)
    return cyclones_frame


def get_cyclones_for_special_date(frame, date):
    d = '/'.join(date[0:10].split('.')[::-1])
    row = frame[frame['Date (DD/MM/YYYY)'] == d]
    if row.empty:
        return row
    serial_numbers = list(set(row['Serial Number of system during year']))
    sub_frame = frame[frame['Serial Number of system during year'].isin(serial_numbers)]
    sub_frame = sub_frame[~(sub_frame['Date (DD/MM/YYYY)'] == '') & ~(sub_frame['Time (UTC)'] == '')]
    sub_frame.index = range(0, len(sub_frame))
    return sub_frame


def get_cyclone_for_special_number(frame, number):
    sub_frame = frame[(frame['Serial Number of system during year'] == number) &
                      ~(frame['Date (DD/MM/YYYY)'] == '') & ~(frame['Time (UTC)'] == '')]
    sub_frame.index = range(0, len(sub_frame))
    return sub_frame


def get_current_cyclone_dict(df):
    cyclone = dict()
    cyclone['start'] = datetime.strptime(df['Date (DD/MM/YYYY)'][0] + ' '
                                         + df['Time (UTC)'][0], '%d/%m/%Y %H%M').strftime('%Y.%m.%d %H:%M:%S')
    cyclone['end'] = datetime.strptime(df['Date (DD/MM/YYYY)'][len(df)-1] + ' '
                                       + df['Time (UTC)'][len(df)-1], '%d/%m/%Y %H%M').strftime('%Y.%m.%d %H:%M:%S')
    cyclone['number'] = list(set(df['Serial Number of system during year']))[0]
    cyclone['name'] = df['Name'][0]
    return cyclone


def get_cyclones(cyclones_frame, options):
    cyclones_df_copy = cyclones_frame.copy()
    start_date = datetime.strptime(options['start_time'], '%Y.%m.%d %H:%M:%S')
    end_date = datetime.strptime(options['end_time'], '%Y.%m.%d %H:%M:%S')
    cyclones_df_copy['dates'] = pd.to_datetime(cyclones_df_copy['Date (DD/MM/YYYY)'], format='%d/%m/%Y')
    numbers = cyclones_df_copy[(cyclones_df_copy['dates'] >= start_date) &
                               (cyclones_df_copy['dates'] <= end_date)]['Serial Number of system during year'].values
    ready_numbers = []
    cyclones = []
    for cn in numbers:
        if cn not in ready_numbers:
            ready_numbers.append(cn)
            df = get_cyclone_for_special_number(cyclones_df_copy, cn)
            cyclone = get_current_cyclone_dict(df)
            cyclones.append(cyclone)
    return cyclones

def filter_cyclones_by_time(cyclones, selected_times, inside=True):
    selected_times = set(selected_times)
    def time_filter(cyclone, selected_times=selected_times):
        start, end = cyclone['start'], cyclone['end']
        #start = datetime.strptime(start, '%Y.%m.%d %H:%M:%S')
        #end = datetime.strptime(end, '%Y.%m.%d %H:%M:%S')
        if inside:
            return start in selected_times and end in selected_times
        else:
            return start in selected_times or end in selected_times
    
    filtered_cyclones = list(filter(time_filter, cyclones))
    return filtered_cyclones
        
    


def get_only_known_data(frame):
    l1 = list(map(check_is_number, frame['Longitude (lon.)'].values))
    l2 = list(map(check_is_number, frame['Latitude (lat.)'].values))
    mask = [a and b for a, b in zip(l1, l2)]
    sub_frame = frame[mask]
    sub_frame.index = range(0, len(sub_frame))
    return sub_frame


def get_times_and_positions_for_unknown_points(df, df_k):
    times = []
    lons = []
    lats = []
    d1 = datetime.strptime(df_k['Date (DD/MM/YYYY)'][0] + ' ' + df_k['Time (UTC)'][0], '%d/%m/%Y %H%M')
    for k in range(0, len(df)):
        if not (check_is_number(df['Longitude (lon.)'][k]) and check_is_number(df['Latitude (lat.)'][k])):
            d2 = datetime.strptime(df['Date (DD/MM/YYYY)'][k] + ' ' + df['Time (UTC)'][k], '%d/%m/%Y %H%M')
            times.append(d2)
            if d2 < d1:
                for i in range(k+1, len(df)):
                    if check_is_number(df['Longitude (lon.)'][i]) and check_is_number(df['Latitude (lat.)'][i]):
                        lons.append(float(df['Longitude (lon.)'][i]))
                        lats.append(float(df['Latitude (lat.)'][i]))
                        break
            else:
                for i in range(k-1, -1, -1):
                    if check_is_number(df['Longitude (lon.)'][i]) and check_is_number(df['Latitude (lat.)'][i]):
                        lons.append(float(df['Longitude (lon.)'][i]))
                        lats.append(float(df['Latitude (lat.)'][i]))
                        break
    return times, lons, lats


def extension_df_for_cyclone(df):
    df_extended = pd.DataFrame()
    start_date = datetime.strptime(df['Date (DD/MM/YYYY)'][0] + ' ' + df['Time (UTC)'][0], '%d/%m/%Y %H%M')
    end_date = datetime.strptime(df['Date (DD/MM/YYYY)'][len(df)-1] + ' ' + df['Time (UTC)'][len(df)-1], '%d/%m/%Y %H%M')

    d = start_date
    delta = timedelta(hours=3)
    while d <= end_date:
        current_date_str = d.strftime('%d/%m/%Y')
        current_time_str = d.strftime('%H%M')
        row = df[(df['Date (DD/MM/YYYY)'] == current_date_str) & (df['Time (UTC)'] == current_time_str)]
        if not row.empty:
            df_extended = df_extended.append(row)
        else:
            df_extended = df_extended.append(df_extended.iloc[-1, :])
            df_extended.iloc[-1, list(df_extended.columns).index('Date (DD/MM/YYYY)')] = current_date_str
            df_extended.iloc[-1, list(df_extended.columns).index('Time (UTC)')] = current_time_str
            df_extended.iloc[-1, list(df_extended.columns).index('Time (UTC)')+1:] = ' '
        d += delta
    df_extended.index = range(0, len(df_extended))
    return df_extended


def full_extended_df_for_cyclone(extended_df):
    res_df = extended_df.copy()
    df_k = get_only_known_data(extended_df)
    if not df_k.empty:
        times, lons, lats = get_times_and_positions_for_unknown_points(extended_df, df_k)
        for i in range(0, len(times)):
            d = times[i]
            row_ind = res_df[(res_df['Date (DD/MM/YYYY)'] == d.strftime('%d/%m/%Y')) &
                             (res_df['Time (UTC)'] == d.strftime('%H%M'))].index[0]
            res_df.loc[row_ind, ['Latitude (lat.)', 'Longitude (lon.)']] = [lats[i], lons[i]]
    else:
        res_df = pd.DataFrame()
    return res_df


def get_lat_lon_for_cyclone(df):
    lons = list(map(float, df['Longitude (lon.)'].values))
    lats = list(map(float, df['Latitude (lat.)'].values))
    return lons, lats


def get_sizes_for_cyclone(df):
    s = 20
    sizes_dict = {'L': s, '-': s, 'D over': s, np.nan: s, '': s,
                  'D': s*2, 'DD': s*3, 'CS': s*4, 'SCS': s*5,
                  'VSCS': s*6, 'ESCS': s*7, 'SUCS': s*8}
    sizes = [sizes_dict[key] for key in df['Grade (text)'].values]
    return sizes


def update_config_for_plot_cyclone(config, cyclone):
    config.metrics_plot_options['start_time'] = cyclone['start']
    config.metrics_plot_options['end_time'] = cyclone['end']
    config.metrics_plot_options['time_split'] = None
    config.metrics_plot_options['plot_cyclones'] = True


def get_datetimes_for_cyclone_points(df):
    date_times = []
    for ind, row in df.iterrows():
        if row['Date (DD/MM/YYYY)'] != '' and row['Time (UTC)'] != '':
            ct = datetime.strptime(row['Date (DD/MM/YYYY)'] + ' ' + row['Time (UTC)'], '%d/%m/%Y %H%M')
            date_times.append(ct.strftime('%Y.%m.%d %H:%M:%S'))
    return date_times


def create_cyclone_info_string(cyclone):
    info_str = str(cyclone['start'][0:4]) + '_cyclone_' + cyclone['number'].split('_')[0] + '_' + cyclone['name'] + '_'\
           + datetime.strptime(cyclone['start'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d') + '_' \
           + datetime.strptime(cyclone['end'], '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d')
    return info_str
