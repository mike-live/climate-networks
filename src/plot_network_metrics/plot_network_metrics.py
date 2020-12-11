import numpy as np
import pandas as pd
import xarray as xr
import cv2
import matplotlib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter, LatitudeLocator
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from . import utils


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
    ax.add_feature(cfeature.BORDERS, alpha = 0.5)
    ax.add_feature(cfeature.LAKES, alpha = 0.5)
    ax.add_feature(cfeature.RIVERS)


def plot_2d_metric_on_map(metric, config, folder):
    
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['times_file_name']
    times = np.asarray(pd.read_csv(file_name, sep = '\n', header = None)[0])
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['lat_file_name']
    lat = np.asarray(pd.read_csv(file_name, header = None)[0])
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['lon_file_name']
    lon = np.asarray(pd.read_csv(file_name, header = None)[0])
    
    data = xr.DataArray(metric, dims=('lat', 'lon', 'time'), coords = {'lat': lat, 'lon': lon, 'time': times})
    
    considered_times = utils.get_considered_times(config.map_plot_options)
    
    if config.map_plot_options['scaling_by_selected_data'] == True:
        data = data.sel(time = considered_times)
    
    vmin = float(data.min(skipna = True))
    vmax = float(data.max(skipna = True))
    
    west = config.download_ERA5_options['west']
    east = config.download_ERA5_options['east']
    south = config.download_ERA5_options['south']
    north = config.download_ERA5_options['north']
    central_longitude = (east + west) / 2
    
    xticks, yticks = utils.get_xyticks_for_map(west, east, south, north)
    
    cmap = get_cmap()
    
    for t in considered_times:
        fig = plt.figure(figsize = [10,10])
        ax = plt.axes(projection = ccrs.PlateCarree(central_longitude = central_longitude))
        plot_map_area(ax, [west, east, south, north])

        num_levels = 50
        levels = np.linspace(vmin, vmax, num_levels + 1)

        cf = ax.contourf(lon, lat, np.asarray(data.sel(time = t)), cmap = cmap, \
                     levels = levels, vmin = vmin, vmax = vmax, transform = ccrs.PlateCarree())
        cb = fig.colorbar(cf, shrink = 0.46)
        cb.ax.set_title(config.map_plot_options['metric_name'])

        ax.set_title(t)
        ax.set_xticks(xticks, crs=ccrs.PlateCarree())
        ax.set_yticks(yticks, crs=ccrs.PlateCarree())
        lon_formatter = LongitudeFormatter(zero_direction_label = True)
        lat_formatter = LatitudeFormatter()
        ax.xaxis.set_major_formatter(lon_formatter)
        ax.yaxis.set_major_formatter(lat_formatter)
        
        t_form = datetime.strptime(t, '%Y.%m.%d %H:%M:%S').strftime('%Y-%m-%d-%H-%M-%S')
        file_name = folder / (config.map_plot_options['metric_name'] + '_' + t_form + '.png')
        plt.savefig(file_name, dpi = config.map_plot_options['dpi'], bbox_inches = 'tight')
        plt.clf()


def plot_1d_metric_from_time(metric, config, folder):
    
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['times_file_name']
    times = list(pd.read_csv(file_name, sep = '\n', header = None)[0])
    
    ymin = round(float(np.nanmin(metric)), 2)
    ymax = round(float(np.nanmax(metric)), 2)
    step = round((ymax - ymin) / 3, 2)
    
    frame = pd.DataFrame({'time': times, 'metric': metric})
    
    if config.map_plot_options['time_split'] is None:
        plt.figure(figsize = (20, 4))
        plt.plot(frame['metric'])
        plt.title(config.map_plot_options['metric_name'], size = 20)
        inds, inds_label = utils.get_xticks_for_GCC(times, 'none')
        plt.xticks(inds, inds_label, size = 20)
        plt.yticks(np.arange(ymin, ymax, step), size = 20)
        
        file_name = folder / (config.map_plot_options['metric_name'] + '.png')
        plt.savefig(file_name, dpi = config.map_plot_options['dpi'], bbox_inches = 'tight')
        plt.clf()
    
    elif config.map_plot_options['time_split'] == 'years':
        years = utils.get_considered_years(config.map_plot_options)
        for year in years:
            year_frame = frame[frame['time'].str.contains(str(year))]
            year_frame.index = range(0, len(year_frame))
            plt.figure(figsize = (20, 4))
            plt.plot(year_frame['metric'])
            plt.title(config.map_plot_options['metric_name'] + ', ' + str(year), size = 20)
            inds, inds_label = utils.get_xticks_for_GCC(list(year_frame['time']), 'years')
            plt.xticks(inds, inds_label, size = 20)
            plt.yticks(np.arange(ymin, ymax, step), size = 20)
            
            file_name = folder / (config.map_plot_options['metric_name'] + '_' + str(year) + '.png')
            plt.savefig(file_name, dpi = config.map_plot_options['dpi'], bbox_inches = 'tight')
            plt.clf()
            
    elif config.map_plot_options['time_split'] == 'months':
        start_date = datetime.strptime(config.map_plot_options['start_time_plot'], '%Y.%m.%d %H:%M:%S')
        end_date = datetime.strptime(config.map_plot_options['end_time_plot'], '%Y.%m.%d %H:%M:%S')
        d = start_date
        while d <= end_date:
            month_frame = frame[frame['time'].str.contains(d.strftime("%Y.%m."))]
            month_frame.index = range(0, len(month_frame))
            plt.figure(figsize = (20, 4))
            plt.plot(month_frame['metric'])
            plt.title(config.map_plot_options['metric_name'] + ', ' + d.strftime("%b %Y"), size = 20)
            inds, inds_label = utils.get_xticks_for_GCC(list(month_frame['time']), 'months')
            plt.xticks(inds, inds_label, size = 20)
            plt.yticks(np.arange(ymin, ymax, step), size = 20)
            
            file_name = folder / (config.map_plot_options['metric_name'] + '_' + d.strftime("%b_%Y") + '.png')
            plt.savefig(file_name, dpi = config.map_plot_options['dpi'], bbox_inches = 'tight')
            plt.clf()
            
            d += relativedelta(months = 1)
