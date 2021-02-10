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
    sub_frame = sub_frame[~(sub_frame['Date (DD/MM/YYYY)'] == '') & ~(sub_frame['Time (UTC)'] == '')
                          & ~(sub_frame['Latitude (lat.)'] == '') & ~(sub_frame['Longitude (lon.)'] == '')]
    return sub_frame


def get_lat_lon_for_cyclone(sub_frame):
    lons = list(map(float, sub_frame['Longitude (lon.)']))
    lats = list(map(float, sub_frame['Latitude (lat.)']))
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


def eliminate_point_overlap(colors, edgecolors, ci, sizes, lons, lats):
    colors_new = colors.copy()
    edgecolors_new = edgecolors.copy()
    for k in range(ci+1, len(sizes)):
        if lons[k] == lons[ci] and lats[k] == lats[ci] and sizes[k] == sizes[ci]:
            colors_new[k] = colors[ci]
            edgecolors_new[k] = edgecolors[ci]
    return colors_new, edgecolors_new


def get_colors_for_cyclone(df, cyclone, date, number, sizes, lons, lats):
    alpha = 0
    colors = [[0, 0, 0, alpha]] * len(df)   # black
    edgecolors = [[0, 0, 0]] * len(df)
    if cyclone != '':
        if cyclone['number'] == number:
            current_index = get_current_index(df, date)
            if current_index != -1:
                colors[current_index] = [1, 0, 0, alpha]   # red
                edgecolors[current_index] = [1, 0, 0]
                colors, edgecolors = eliminate_point_overlap(colors, edgecolors, current_index, sizes, lons, lats)
    return colors, edgecolors


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
            d1 = datetime.strptime(date, '%Y.%m.%d %H:%M:%S')
            d2 = datetime.strptime(df['Date (DD/MM/YYYY)'][0] + ' ' + df['Time (UTC)'][0], '%d/%m/%Y %H%M')
            d3 = datetime.strptime(df['Date (DD/MM/YYYY)'][len(df)-1] + ' ' + df['Time (UTC)'][len(df)-1],
                                   '%d/%m/%Y %H%M')
            if d2 <= d1 <= d3:
                lons, lats = get_lat_lon_for_cyclone(df)
                sizes = get_sizes_for_cyclone(df)
                colors, edgecolors = get_colors_for_cyclone(df, cyclone, date, number, sizes, lons, lats)
                ax.plot(lons, lats, 'k-', transform=ccrs.PlateCarree())
                ax.scatter(lons, lats, c=colors, edgecolors=edgecolors, s=sizes, transform=ccrs.PlateCarree())
                add_cyclone_info(ax, df, lons, lats)


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


def update_config_for_plot_cyclone(config, cyclone):
    config.metrics_plot_options['start_time'] = cyclone['start']
    config.metrics_plot_options['end_time'] = cyclone['end']
    config.metrics_plot_options['time_split'] = None
    config.metrics_plot_options['plot_cyclones'] = True
