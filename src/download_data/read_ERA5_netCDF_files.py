import numpy as np
import xarray as xr
from datetime import timedelta, datetime


def get_longitude(xarray_dset, name_coord):
    # getting longitude values from xarray
    longitude = np.asarray(xarray_dset[name_coord])
    return longitude


def get_latitude(xarray_dset, name_coord):
    # getting latitude values from xarray
    latitude = np.asarray(xarray_dset[name_coord])
    return latitude


def get_times(xarray_dset, name_coord):
    # getting time values from xarray
    times = np.asarray(xarray_dset[name_coord])
    return times


def get_data_cube(xarray_dset, name_data_var):
    # getting data values from xarray
    data_cube = xarray_dset[name_data_var]
    return data_cube


def form_times(options):
    # formation of a times list of the form "yyyy.mm.dd hh:00:00"
    times = []
    
    start_date = datetime(options['start_year'], options['start_month'], options['start_day'], options['start_time'], 0, 0)
    end_date = datetime(options['end_year'], options['end_month'], options['end_day'], options['end_time'], 0, 0)
    
    d = start_date
    delta = timedelta(hours = options['step_time'])
    while d <= end_date:
        times.append(d.strftime("%Y.%m.%d %H:%M:%S"))
        d += delta
    
    return np.array(times)
 

def form_resulting_data_cube_from_parts_by_time(*parts):
    # concatenate of xarray by time
    # (since a large data set has to be uploaded as multiple netCDF files)
    # resulting_cube - 3D np.ndarray (time, lat, lon)
    resulting_cube = parts[0]
    for k in range(1, len(parts)):
        resulting_cube = np.concatenate((resulting_cube, parts[k]), axis = 0)
    return resulting_cube
