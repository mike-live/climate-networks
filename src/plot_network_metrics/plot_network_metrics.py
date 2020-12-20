import numpy as np
import pandas as pd
import xarray as xr
import cv2
import matplotlib
from matplotlib import pyplot as plt, rcParams
import matplotlib.dates as mdates
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
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
    
    vmin = float(data.min(dim = ['lat', 'lon', 'time'], skipna = True))
    vmax = float(data.max(dim = ['lat', 'lon', 'time'], skipna = True))
    
    west = config.download_ERA5_options['west']
    east = config.download_ERA5_options['east']
    south = config.download_ERA5_options['south']
    north = config.download_ERA5_options['north']
    central_longitude = (east + west) / 2
    
    xticks, yticks = utils.get_xyticks_for_map(west, east, south, north)
    
    cmap = get_cmap()
    
    for t in considered_times:
        fig = plt.figure(figsize = (10, 10))
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
        plt.close()


def plot_1d_metric_from_time(metric, config, folder):
    
    rcParams['font.size'] = 18
    rcParams['axes.titlesize'] = 'medium'
    
    file_name = config.download_ERA5_options['work_dir'] / config.download_ERA5_options['times_file_name']
    times = list(pd.read_csv(file_name, sep = '\n', header = None)[0])
    frame = pd.DataFrame({'time': times, 'metric': metric})
    ymin = round(float(np.nanmin(metric)), 2)
    ymax = round(float(np.nanmax(metric)), 2)
    step = round((ymax - ymin) / 3, 2)
    
    if config.map_plot_options['time_split'] == None:
        considered_times = utils.get_considered_times(config.map_plot_options)
        date_frame = frame[frame['time'].isin(considered_times)]
        date_frame.index = range(0, len(date_frame))
        dates = [datetime.strptime(d,'%Y.%m.%d %H:%M:%S').date() for d in date_frame['time']]
        
        plt.figure(figsize = (20, 4))
        
        plt.plot(dates, date_frame['metric'], 'b')
        plt.title(config.map_plot_options['start_time_plot'] + ' - ' + config.map_plot_options['end_time_plot'])
        
        plt.xlabel('date')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%b'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gca().set_xlim(dates[0], dates[-1])
        
        plt.ylabel(config.map_plot_options['metric_name'])
        plt.gca().set_yticks(np.arange(ymin, ymax, step))
        plt.gca().set_ylim(ymin - step*0.1, ymax)
    
        file_name = folder / (config.map_plot_options['metric_name'] + '.png')
        plt.savefig(file_name, dpi = config.map_plot_options['dpi'], bbox_inches = 'tight')
        plt.close()
    
    elif config.map_plot_options['time_split'] == 'years':
        years = utils.get_considered_years(config.map_plot_options)
        for year in years:
            year_frame = frame[frame['time'].str.contains(str(year))]
            year_frame.index = range(0, len(year_frame))
            dates = [datetime.strptime(d,'%Y.%m.%d %H:%M:%S').date() for d in year_frame['time']]

            plt.figure(figsize = (20, 4))
            
            plt.plot(dates, year_frame['metric'], 'b')
            plt.title(str(year))
            
            plt.xlabel('date')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))
            plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.gca().set_xlim(dates[0], dates[-1])
            
            plt.ylabel(config.map_plot_options['metric_name'])
            plt.gca().set_yticks(np.arange(ymin, ymax, step))
            plt.gca().set_ylim(ymin - step*0.1, ymax)
            
            file_name = folder / (config.map_plot_options['metric_name'] + '_' + str(year) + '.png')
            plt.savefig(file_name, dpi = config.map_plot_options['dpi'], bbox_inches = 'tight')
            plt.close()
            
    elif config.map_plot_options['time_split'] == 'months':
        start_date = datetime.strptime(config.map_plot_options['start_time_plot'], '%Y.%m.%d %H:%M:%S')
        end_date = datetime.strptime(config.map_plot_options['end_time_plot'], '%Y.%m.%d %H:%M:%S')
        
        d = start_date
        while d <= end_date:
            month_frame = frame[frame['time'].str.contains(d.strftime("%Y.%m."))]
            month_frame.index = range(0, len(month_frame))
            dates = [datetime.strptime(d,'%Y.%m.%d %H:%M:%S').date() for d in month_frame['time']]
            
            plt.figure(figsize = (20, 4))
            
            plt.plot(dates, month_frame['metric'], 'b')
            plt.title(d.strftime("%Y-%b"))

            plt.xlabel('date')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d'))
            plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.gca().set_xlim(dates[0], dates[-1])
            
            plt.ylabel(config.map_plot_options['metric_name'])
            plt.gca().set_yticks(np.arange(ymin, ymax, step))
            plt.gca().set_ylim(ymin - step*0.1, ymax)
            
            file_name = folder / (config.map_plot_options['metric_name'] + '_' + d.strftime("%Y-%m") + '.png')
            plt.savefig(file_name, dpi = config.map_plot_options['dpi'], bbox_inches = 'tight')
            plt.close()
            
            d += relativedelta(months = 1)
