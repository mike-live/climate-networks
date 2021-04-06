import numpy as np
import pandas as pd
import cartopy.crs as ccrs
from datetime import timedelta, datetime
from plot_network_metrics.utils import read_cyclones_file, is_float


def get_cyclones_for_special_date(frame, date):
    d = '/'.join(date[0:10].split('.')[::-1])
    row = frame[frame['Date (DD/MM/YYYY)'] == d]
    if row.empty:
        return row
    serial_numbers = list(map(int, set(row['Serial Number of system during year'])))
    sub_frame = frame[frame['Serial Number of system during year'].isin(serial_numbers)]
    sub_frame = sub_frame[~(sub_frame['Date (DD/MM/YYYY)'] == '') & ~(sub_frame['Time (UTC)'] == '')]
    sub_frame.index = range(0, len(sub_frame))
    return sub_frame


def get_only_known_data(frame):
    l1 = list(map(is_float, frame['Longitude (lon.)'].values))
    l2 = list(map(is_float, frame['Latitude (lat.)'].values))
    mask = [a and b for a, b in zip(l1, l2)]
    sub_frame = frame[mask]
    sub_frame.index = range(0, len(sub_frame))
    return sub_frame


def get_current_cyclone_dict(df):
    cyclone = dict()
    cyclone['start'] = datetime.strptime(df['Date (DD/MM/YYYY)'][0] + ' '
                                         + df['Time (UTC)'][0], '%d/%m/%Y %H%M').strftime('%Y.%m.%d %H:%M:%S')
    cyclone['end'] = datetime.strptime(df['Date (DD/MM/YYYY)'][len(df)-1] + ' '
                                       + df['Time (UTC)'][len(df)-1], '%d/%m/%Y %H%M').strftime('%Y.%m.%d %H:%M:%S')
    cyclone['number'] = int(list(set(df['Serial Number of system during year']))[0])
    cyclone['name'] = df['Name'][0]
    return cyclone


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


def get_current_index(df, date):
    d = '/'.join(date[0:10].split('.')[::-1])
    sub_df = df[(df['Date (DD/MM/YYYY)'] == d) & (df['Time (UTC)'] == date[11:13] + date[14:16])]
    if not sub_df.empty:
        current_index = sub_df.index[0]
    else:
        current_index = -1
    return current_index


def plot_cyclone_points(ax, ci, lons, lats, sizes, cyclone, number):
    for i in range(0, len(lons)):
        # cyclone['number'] == number -> means that the point is marked only at the considered cyclone
        if cyclone['number'] == number and i == ci:
            ax.scatter(lons[i], lats[i], color=[1, 0, 0, 0], edgecolors=[1, 0, 0], s=sizes[i],
                       transform=ccrs.PlateCarree(), zorder=20)
        else:
            ax.scatter(lons[i], lats[i], color=[0, 0, 0, 0], edgecolors=[0, 0, 0], s=sizes[i],
                       transform=ccrs.PlateCarree(), zorder=10)


def plot_unknown_point(ax, date, times, lons, lats, cyclone, number):
    if cyclone['number'] == number:
        if date in times:
            ind = times.index(date)
            ax.scatter(lons[ind], lats[ind], c='r', s=70, marker='X', transform=ccrs.PlateCarree(), zorder=10)


def add_cyclone_info(ax, df, lons, lats):
    text = str(list(set(df['Name']))[0]) + ' '
    text += datetime.strptime(df['Date (DD/MM/YYYY)'][0], '%d/%m/%Y').strftime('%d %b') + ' - '
    text += datetime.strptime(df['Date (DD/MM/YYYY)'][len(df)-1], '%d/%m/%Y').strftime('%d %b')
    center = (min(lons) + max(lons)) * 0.5
    h = max(lats) + 3
    props = dict(facecolor='white', edgecolor='none', alpha=0.5)
    ax.text(center, h, text, horizontalalignment='center',
            verticalalignment='top', bbox=props, transform=ccrs.PlateCarree())


def plot_cyclones_on_map(date, ax, config, cyclone):
    sheet_name = date[0:4]
    frame = read_cyclones_file(config.metrics_plot_options['cyclones_file_name'], sheet_name)
    sub_frame = get_cyclones_for_special_date(frame, date)
    if not sub_frame.empty:
        unique_serial_numbers = sorted(list(set(sub_frame['Serial Number of system during year'])))
        for number in unique_serial_numbers:
            df = sub_frame[sub_frame['Serial Number of system during year'] == number]
            df.index = range(0, len(df))
            df = extension_df_for_cyclone(df)
            d1 = datetime.strptime(date, '%Y.%m.%d %H:%M:%S')
            d2 = datetime.strptime(df['Date (DD/MM/YYYY)'][0] + ' ' + df['Time (UTC)'][0], '%d/%m/%Y %H%M')
            d3 = datetime.strptime(df['Date (DD/MM/YYYY)'][len(df)-1] + ' ' + df['Time (UTC)'][len(df)-1],
                                   '%d/%m/%Y %H%M')
            if d2 <= d1 <= d3:
                df_k = get_only_known_data(df)
                if not df_k.empty:
                    time_unk_points, lon_unk_points, lat_unk_points = get_times_and_positions_for_unknown_points(df, df_k)
                    lons, lats = get_lat_lon_for_cyclone(df_k)
                    sizes = get_sizes_for_cyclone(df_k)
                    ci = get_current_index(df_k, date)
                    ax.plot(lons, lats, 'k-', transform=ccrs.PlateCarree())
                    plot_cyclone_points(ax, ci, lons, lats, sizes, cyclone, number)
                    plot_unknown_point(ax, d1, time_unk_points, lon_unk_points, lat_unk_points, cyclone, number)
                    add_cyclone_info(ax, df, lons, lats)
