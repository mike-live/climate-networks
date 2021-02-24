import numpy as np
import pandas as pd
import cv2
import matplotlib
from matplotlib import pyplot as plt, rcParams
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
from . import utils
from . import plot_cyclones


def get_cmap():
    cmap_im = cv2.imread('cmap.png')
    cmap_im = cv2.cvtColor(cmap_im, cv2.COLOR_BGR2RGB)
    cmap_im = np.flipud(cmap_im)

    colors = []
    for i in range(2, len(cmap_im), 18):
        c = cmap_im[i, 2, :]
        c = (c[0] / 255, c[1] / 255, c[2] / 255)
        colors += [c]

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("my_colormap", colors)
    
    return cmap


def plot_map_area(ax, coordinates):
    ax.set_extent(coordinates)
    ax.stock_img()
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, alpha=0.5)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS)


def get_vmin_vmax(config, metric, considered_times, times):
    if config.metrics_plot_options['scaling_by_selected_data'] == False:
        vmin, vmax = np.nanpercentile(metric, [0.1, 99.9])
    else:
        data = metric[:, :, np.in1d(times, considered_times)]
        vmin = np.nanmin(data)
        vmax = np.nanmax(data)
    return vmin, vmax


def set_vmin_vmax(metric, vmin, vmax):
    data = metric.copy()
    data[np.where(data < vmin)] = vmin
    data[np.where(data > vmax)] = vmax
    return data


def get_boundary_coordinates(config):
    west = config.download_ERA5_options['west']
    east = config.download_ERA5_options['east']
    south = config.download_ERA5_options['south']
    north = config.download_ERA5_options['north']
    return west, east, south, north


def plot_2d_metric_on_map(metric, considered_times, config, directory, cyclone=''):
    # metric - 3D np.ndarray (lat, lon, time)

    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['times_file_name']
    times = np.loadtxt(file_name, dtype='str', delimiter='\n')
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['lat_file_name']
    lat = np.loadtxt(file_name, dtype='float', delimiter='\n')
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['lon_file_name']
    lon = np.loadtxt(file_name, dtype='float', delimiter='\n')

    vmin, vmax = get_vmin_vmax(config, metric, considered_times, times)
    metric = set_vmin_vmax(metric, vmin, vmax)

    west, east, south, north = get_boundary_coordinates(config)
    central_longitude = (east + west) / 2
    
    cmap = get_cmap()
    
    for t in tqdm(considered_times):
        fig = plt.figure(figsize=(10, 10))
        ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=central_longitude))
        plot_map_area(ax, [west, east, south, north])

        num_levels = 50
        levels = np.linspace(vmin, vmax, num_levels + 1)
        cf = ax.contourf(lon, lat, metric[:, :, np.where(times == t)[0][0]], cmap=cmap,
                         levels=levels, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
        cb = fig.colorbar(cf, shrink=0.46)
        cb.ax.set_title(config.metrics_plot_options['metric_name'])

        ax.set_title(datetime.strptime(t, '%Y.%m.%d %H:%M:%S').strftime('%d %b %Y %H:%M:%S'))
        gl = ax.gridlines(draw_labels=True)
        gl.top_labels = gl.right_labels = gl.xlines = gl.ylines = False

        ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=True))
        ax.yaxis.set_major_formatter(LatitudeFormatter())
        
        if config.metrics_plot_options['plot_cyclones']:
            plot_cyclones.plot_cyclones_on_map(t, ax, config, cyclone)
        
        t_form = datetime.strptime(t, '%Y.%m.%d %H:%M:%S').strftime('%d-%b-%Y-%H-%M-%S')
        ind = str(considered_times.index(t) + 1)
        file_name = directory / (config.metrics_plot_options['metric_name'].replace('/', '_') + '_#' + ind + '_' + t_form + '.png')
        #file_name.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(file_name, dpi=config.metrics_plot_options['dpi'], bbox_inches='tight')
        plt.close()


def get_ymin_ymax(metric):
    ymin = round(float(np.nanmin(metric)), 2)
    ymax = round(float(np.nanmax(metric)), 2)
    return ymin, ymax


def plot_1d_metric_for_entire_time_interval(config, frame, considered_times, directory):
    ymin, ymax = get_ymin_ymax(frame['metric'].values)
    step = round((ymax - ymin) / 3, 2)

    date_frame = frame[frame['time'].isin(considered_times)]
    date_frame.index = range(0, len(date_frame))
    dates = [mdates.date2num(datetime.strptime(d, '%Y.%m.%d %H:%M:%S')) for d in date_frame['time']]

    fig = plt.figure(figsize=(20, 4))
    ax = plt.gca()

    ax.plot(dates, date_frame['metric'], 'b')
    start_t = datetime.strptime(config.metrics_plot_options['start_time'],
                                '%Y.%m.%d %H:%M:%S').strftime('%d %b %Y %H:%M')
    end_t = datetime.strptime(config.metrics_plot_options['end_time'],
                              '%Y.%m.%d %H:%M:%S').strftime('%d %b %Y %H:%M')
    ax.set_title(start_t + ' - ' + end_t)

    ax.set_xlabel('date')
    if config.plotting_mode['cyclones'] and config.plotting_mode['metrics'] == False:
        ax.axvline(mdates.date2num(datetime.strptime(start_t, '%d %b %Y %H:%M')), linestyle='--', color='gray')
        ax.axvline(mdates.date2num(datetime.strptime(end_t, '%d %b %Y %H:%M')), linestyle='--', color='gray')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %H:%M'))
        if len(dates) <= 20:
            ax.xaxis.set_major_locator(mtick.FixedLocator(dates))
        else:
            ax.xaxis.set_major_locator(mtick.AutoLocator())
        fig.autofmt_xdate()
    else:
        if (mdates.num2date(dates[-1]) - mdates.num2date(dates[0])).days <= 31:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
        elif (mdates.num2date(dates[-1]) - mdates.num2date(dates[0])).days <= 366:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.set_xlim(dates[0], dates[-1])

    ax.set_ylabel(config.metrics_plot_options['metric_name'])
    ax.set_yticks(np.arange(ymin, ymax, step))
    ax.set_ylim(ymin - step * 0.1, ymax)

    file_name = directory / (config.metrics_plot_options['metric_name'].replace('/', '_') + '.png')
    #file_name.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(file_name, dpi=config.metrics_plot_options['dpi'], bbox_inches='tight')
    plt.close()


def plot_1d_metric_for_years(config, frame, directory):
    ymin, ymax = get_ymin_ymax(frame['metric'].values)
    step = round((ymax - ymin) / 3, 2)

    years = utils.get_considered_years(config)
    for year in years:
        year_frame = frame[frame['time'].str.contains(str(year))]
        year_frame.index = range(0, len(year_frame))
        dates = [mdates.date2num(datetime.strptime(d, '%Y.%m.%d %H:%M:%S')) for d in year_frame['time']]

        fig = plt.figure(figsize=(20, 4))
        ax = plt.gca()

        ax.plot(dates, year_frame['metric'], 'b')
        ax.set_title(str(year))

        ax.set_xlabel('date')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.set_xlim(dates[0], dates[-1])

        ax.set_ylabel(config.metrics_plot_options['metric_name'])
        ax.set_yticks(np.arange(ymin, ymax, step))
        ax.set_ylim(ymin - step * 0.1, ymax)

        file_name = directory / (config.metrics_plot_options['metric_name'].replace('/', '_') + '_' + str(year) + '.png')
        #file_name.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(file_name, dpi=config.metrics_plot_options['dpi'], bbox_inches='tight')
        plt.close()


def plot_1d_metric_for_months(config, frame, directory):
    ymin, ymax = get_ymin_ymax(frame['metric'].values)
    step = round((ymax - ymin) / 3, 2)

    start_date = datetime.strptime(config.metrics_plot_options['start_time'], '%Y.%m.%d %H:%M:%S')
    end_date = datetime.strptime(config.metrics_plot_options['end_time'], '%Y.%m.%d %H:%M:%S')

    d = start_date
    while d <= end_date:
        month_frame = frame[frame['time'].str.contains(d.strftime("%Y.%m."))]
        month_frame.index = range(0, len(month_frame))
        dates = [mdates.date2num(datetime.strptime(d, '%Y.%m.%d %H:%M:%S')) for d in month_frame['time']]

        fig = plt.figure(figsize=(20, 4))
        ax = plt.gca()

        ax.plot(dates, month_frame['metric'], 'b')
        ax.set_title(d.strftime("%b %Y"))

        ax.set_xlabel('date')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.set_xlim(dates[0], dates[-1])

        ax.set_ylabel(config.metrics_plot_options['metric_name'])
        ax.set_yticks(np.arange(ymin, ymax, step))
        ax.set_ylim(ymin - step * 0.1, ymax)

        file_name = directory / (config.metrics_plot_options['metric_name'].replace('/', '_') + '_' + d.strftime("%b-%Y") + '.png')
        #file_name.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(file_name, dpi=config.metrics_plot_options['dpi'], bbox_inches='tight')
        plt.close()

        d += relativedelta(months=1)


def plot_1d_metric_from_time(metric, considered_times, config, directory):
    rcParams['font.size'] = 18
    rcParams['axes.titlesize'] = 'medium'

    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['times_file_name']
    times = np.loadtxt(file_name, dtype='str', delimiter='\n')
    frame = pd.DataFrame({'time': times, 'metric': metric})
    
    if config.metrics_plot_options['time_split'] == None:
        plot_1d_metric_for_entire_time_interval(config, frame, considered_times, directory)
    elif config.metrics_plot_options['time_split'] == 'years':
        plot_1d_metric_for_years(config, frame, directory)
    elif config.metrics_plot_options['time_split'] == 'months':
        plot_1d_metric_for_months(config, frame, directory)

    rcParams.update(matplotlib.rcParamsDefault)
