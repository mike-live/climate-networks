import numpy as np
import pandas as pd
from datetime import timedelta, datetime


def is_float(st):
    try:
        float(st)
        return True
    except ValueError:
        return False


def delete_empty_rows(frame):
    new_frame = frame.copy()
    for ind, row in frame.iterrows():
        if new_frame.loc[ind].isna().values.all():
            new_frame.drop([ind], inplace=True)
    new_frame.index = range(0, len(new_frame))
    return new_frame


def convert_time_in_cyclone_frame(frame):
    new_frame = frame.copy()
    new_frame['Time (UTC)'] = new_frame['Time (UTC)'].apply(lambda x:
                                                            '' if x == ''
                                                            else (x.zfill(4)
                                                                  if type(x) is str
                                                                  else ('' if np.isnan(x)
                                                                        else '{:04d}'.format(int(x)))))
    return new_frame


def read_cyclones_file(file_name, sheet_name):
    frame = pd.read_excel(file_name, sheet_name=sheet_name)
    frame = delete_empty_rows(frame)
    frame = convert_time_in_cyclone_frame(frame)
    frame.fillna('', inplace=True)
    return frame


def get_cyclones_for_special_date(frame, date):
    d = '/'.join(date[0:10].split('.')[::-1])
    row = frame[frame['Date (DD/MM/YYYY)'] == d]
    if row.empty:
        return row
    serial_numbers = list(map(int, set(row['Serial Number of system during year'])))
    sub_frame = frame[frame['Serial Number of system during year'].isin(serial_numbers)]
    sub_frame = sub_frame[~(sub_frame['Date (DD/MM/YYYY)'] == '') & ~(sub_frame['Time (UTC)'] == '')]
    sub_frame.index = range(0, len(sub_frame))
    return


def get_cyclones(config):
    start_date = datetime.strptime(config.cyclones_plot_options['start_time'], '%Y.%m.%d %H:%M:%S')
    end_date = datetime.strptime(config.cyclones_plot_options['end_time'], '%Y.%m.%d %H:%M:%S')

    cyclones = []
    current_date = start_date
    for year in range(int(start_date.strftime('%Y')), int(end_date.strftime('%Y')) + 1):
        frame = read_cyclones_file(config.cyclones_plot_options['cyclones_file_name'], str(year))
        while current_date <= end_date:
            sub_frame = get_cyclones_for_special_date(frame, current_date.strftime('%Y.%m.%d %H:%M:%S'))
            if not sub_frame.empty:
                unique_serial_numbers = sorted(list(set(sub_frame['Serial Number of system during year'])))
                for number in unique_serial_numbers:
                    df = sub_frame[sub_frame['Serial Number of system during year'] == number]
                    df.index = range(0, len(df))
                    cyclone = get_current_cyclone_dict(df)
                    if cyclone not in cyclones:
                        cyclones.append(cyclone)
                if number + 1 in frame['Serial Number of system during year'].values:
                    df = frame[frame['Serial Number of system during year'] == number + 1]
                    current_date = datetime.strptime(df['Date (DD/MM/YYYY)'].values[0], '%d/%m/%Y')
                else:
                    current_date = datetime(year=year+1, month=1, day=1)
                    break
            else:
                current_date += timedelta(days=1)
    return cyclones


def get_only_known_data(frame):
    l1 = list(map(is_float, frame['Longitude (lon.)'].values))
    l2 = list(map(is_float, frame['Latitude (lat.)'].values))
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
        if not (is_float(df['Longitude (lon.)'][k]) and is_float(df['Latitude (lat.)'][k])):
            d2 = datetime.strptime(df['Date (DD/MM/YYYY)'][k] + ' ' + df['Time (UTC)'][k], '%d/%m/%Y %H%M')
            times.append(d2)
            if d2 < d1:
                for i in range(k+1, len(df)):
                    if is_float(df['Longitude (lon.)'][i]) and is_float(df['Latitude (lat.)'][i]):
                        lons.append(float(df['Longitude (lon.)'][i]))
                        lats.append(float(df['Latitude (lat.)'][i]))
                        break
            else:
                for i in range(k-1, -1, -1):
                    if is_float(df['Longitude (lon.)'][i]) and is_float(df['Latitude (lat.)'][i]):
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


def get_current_cyclone_dict(df):
    cyclone = dict()
    cyclone['start'] = datetime.strptime(df['Date (DD/MM/YYYY)'][0] + ' '
                                         + df['Time (UTC)'][0], '%d/%m/%Y %H%M').strftime('%Y.%m.%d %H:%M:%S')
    cyclone['end'] = datetime.strptime(df['Date (DD/MM/YYYY)'][len(df)-1] + ' '
                                       + df['Time (UTC)'][len(df)-1], '%d/%m/%Y %H%M').strftime('%Y.%m.%d %H:%M:%S')
    cyclone['number'] = int(list(set(df['Serial Number of system during year']))[0])
    cyclone['name'] = df['Name'][0]
    return cyclone


def update_config_for_plot_cyclone(config, cyclone):
    config.metrics_plot_options['start_time'] = cyclone['start']
    config.metrics_plot_options['end_time'] = cyclone['end']
    config.metrics_plot_options['time_split'] = None
    config.metrics_plot_options['plot_cyclones'] = True


def get_datetimes_for_cycline_points(df):
    date_times = []
    for ind, row in df.iterrows():
        if row['Date (DD/MM/YYYY)'] != '' and row['Time (UTC)'] != '':
            ct = datetime.strptime(row['Date (DD/MM/YYYY)'] + ' ' + row['Time (UTC)'], '%d/%m/%Y %H%M')
            date_times.append(ct.strftime('%Y.%m.%d %H:%M:%S'))
    return date_times
