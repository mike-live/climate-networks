import numpy as np
import cartopy.crs as ccrs
from datetime import timedelta, datetime
from plot_network_metrics.utils import read_cyclones_file


def get_cyclones_for_special_date(frame, date):
    d = '/'.join(date[0:10].split('.')[::-1])
    row = frame[frame['Date (DD/MM/YYYY)'] == d]
    if row.empty:
        return row
    serial_numbers = list(map(int, set(row['Serial Number of system during year'])))
    sub_frame = frame[frame['Serial Number of system during year'].isin(serial_numbers)]
    sub_frame = sub_frame[~(sub_frame['Date (DD/MM/YYYY)'] == '') & ~(sub_frame['Time (UTC)'] == '') \
                      & ~(sub_frame['Latitude (lat.)'] == '') & ~(sub_frame['Longitude (lon.)'] == '')]
    return sub_frame


def get_lat_lon_for_cyclone(sub_frame):
    lons = list(map(float, sub_frame['Longitude (lon.)']))
    lats = list(map(float, sub_frame['Latitude (lat.)']))
    return lons, lats


def get_current_index(df, date):
    d = '/'.join(date[0:10].split('.')[::-1])
    df = df[(df['Date (DD/MM/YYYY)'] == d) & (df['Time (UTC)'] == date[11:13] + date[14:16])]
    if not df.empty:
        current_index = df.index[0]
    else:
        current_index = -1
    return current_index


def get_colors_for_cyclone(df, cyclone, date, number):
    alpha = 0
    colors = [[0, 0, 0, alpha]] * len(df)   # black
    edgecolors = [[0, 0, 0]] * len(df)
    if cyclone != '':
        if cyclone['number'] == number:
            current_index = get_current_index(df, date)
            colors[current_index] = [1, 0, 0, 0]   # red
            edgecolors[current_index] = [1, 0, 0]
    return colors, edgecolors


def get_sizes_for_cyclone(df):
    s = 20
    sizes_dict = {'L': s, '-': s, 'D over': s, np.nan: s, '': s, 'D': s*2, 'DD': s*3, 'CS': s*4, 'SCS': s*5, 'VSCS': s*5, 'ESCS': s*6, 'SUCS': s*7}
    sizes = [sizes_dict[key] for key in list(df['Grade (text)'])]
    return sizes


def add_cyclone_info(ax, df, lons, lats, south):
    text = str(list(set(df['Name']))[0]) + ' '
    text += datetime.strptime(np.array(df['Date (DD/MM/YYYY)'])[0], '%d/%m/%Y').strftime('%d %b') + ' - '
    text += datetime.strptime(np.array(df['Date (DD/MM/YYYY)'])[-1], '%d/%m/%Y').strftime('%d %b')
    center = (min(lons) + max(lons)) * 0.5
    h = min(lats) - 1
    if h - south < 2:
        h = max(lats) + 1
    ax.text(center, h, text, horizontalalignment='center',
            verticalalignment='top', transform=ccrs.PlateCarree())


def plot_cyclones_on_map(date, ax, options, cyclone, south):
    sheet_name = date[0:4]
    frame = read_cyclones_file(options, sheet_name)
    sub_frame = get_cyclones_for_special_date(frame, date)
    if not sub_frame.empty:
        unique_serial_numbers = sorted(list(set(sub_frame['Serial Number of system during year'])))
        for number in unique_serial_numbers:
            df = sub_frame[sub_frame['Serial Number of system during year'] == number]
            df.index = range(0, len(df))
            lons, lats = get_lat_lon_for_cyclone(df)
            colors, edgecolors = get_colors_for_cyclone(df, cyclone, date, number)
            sizes = get_sizes_for_cyclone(df)
            ax.plot(lons, lats, 'k-', transform=ccrs.PlateCarree())
            ax.scatter(lons, lats, c=colors, edgecolors=edgecolors, s=sizes, transform=ccrs.PlateCarree())
            add_cyclone_info(ax, df, lons, lats, south)


def get_current_cyclone_dict(frame):
    cyclone = dict()
    cyclone['start'] = datetime.strptime(np.array(frame['Date (DD/MM/YYYY)'])[0] + ' ' + np.array(frame['Time (UTC)'])[0], '%d/%m/%Y %H%M').strftime('%Y.%m.%d %H:%M:%S')
    cyclone['end'] = datetime.strptime(np.array(frame['Date (DD/MM/YYYY)'])[-1] + ' ' + np.array(frame['Time (UTC)'])[-1], '%d/%m/%Y %H%M').strftime('%Y.%m.%d %H:%M:%S')
    cyclone['number'] = int(list(set(frame['Serial Number of system during year']))[0])
    cyclone['name'] = np.array(frame['Name'])[0]
    return cyclone


def get_cyclones(config):
    start_date = datetime.strptime(config.cyclones_plot_options['start_time'], '%Y.%m.%d %H:%M:%S')
    end_date = datetime.strptime(config.cyclones_plot_options['end_time'], '%Y.%m.%d %H:%M:%S')

    cyclones = []
    current_date = start_date
    for year in range(int(start_date.strftime('%Y')), int(end_date.strftime('%Y')) + 1):
        frame = read_cyclones_file(config.cyclones_plot_options, str(year))
        while current_date <= end_date:
            sub_frame = get_cyclones_for_special_date(frame, current_date.strftime('%Y.%m.%d  %H:%M:%S'))
            if not sub_frame.empty:
                unique_serial_numbers = sorted(list(set(sub_frame['Serial Number of system during year'])))
                for number in unique_serial_numbers:
                    df = sub_frame[sub_frame['Serial Number of system during year'] == number]
                    cyclone = get_current_cyclone_dict(df)
                    if cyclone not in cyclones:
                        cyclones.append(cyclone)
                if number + 1 in np.array(frame['Serial Number of system during year']):
                    df = frame[frame['Serial Number of system during year'] == number + 1]
                    current_date = datetime.strptime(np.array(df['Date (DD/MM/YYYY)'])[0], '%d/%m/%Y')
                else:
                    current_date = datetime.strptime('01/01/' + str(year + 1), '%d/%m/%Y')
                    break
            else:
                current_date += timedelta(days=1)
    return cyclones


def update_config_for_plot_cyclone(config, cyclone):
    config.metrics_plot_options['start_time'] = cyclone['start']
    config.metrics_plot_options['end_time'] = cyclone['end']
    config.metrics_plot_options['time_split'] = None
    config.metrics_plot_options['plot_cyclones'] = True
