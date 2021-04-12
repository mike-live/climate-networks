import cartopy.crs as ccrs
from datetime import timedelta, datetime
from cyclones_info.cyclones_info import get_cyclones_info, get_cyclones_for_special_date, extension_df_for_cyclone, \
    get_only_known_data, get_times_and_positions_for_unknown_points, get_lat_lon_for_cyclone, get_sizes_for_cyclone


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
    frame = get_cyclones_info(config.metrics_plot_options['cyclones_file_name'], sheet_name)
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
