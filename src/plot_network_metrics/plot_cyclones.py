import pandas as pd
import numpy as np
import cartopy.crs as ccrs


def delete_empty_rows(frame):
    new_frame = frame.copy()
    for ind, row in frame.iterrows():
        if new_frame.loc[ind].isna().values.all():
            new_frame.drop([ind], inplace = True)
    new_frame.index = range(0, len(new_frame))
    return new_frame


def convert_time_in_cyclone_frame(frame):
    new_frame = frame.copy()
    new_frame['Time (UTC)'] = new_frame['Time (UTC)'].apply(lambda x: '' if x == '' else (x.zfill(4) if type(x) is str \
                                                    else ('' if np.isnan(x) else '{:04d}'.format(int(x)))))
    return new_frame


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


def plot_cyclones_on_map(date, ax, options):
    sheet_name = date[0:4]
    frame = pd.read_excel(options['cyclones_file_name'], sheet_name = sheet_name)
    frame = delete_empty_rows(frame)
    frame = convert_time_in_cyclone_frame(frame)
    frame.fillna('', inplace = True)
    sub_frame = get_cyclones_for_special_date(frame, date)
    if not sub_frame.empty:
        unique_serial_numbers = list(sub_frame['Serial Number of system during year'])
        for number in unique_serial_numbers:
            df = sub_frame[sub_frame['Serial Number of system during year'] == number]
            lons, lats = get_lat_lon_for_cyclone(df)
            ax.scatter(lons, lats, c = 'k', s = 50, alpha = 0.2, transform = ccrs.PlateCarree())


