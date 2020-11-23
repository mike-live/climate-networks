import numpy as np
import xarray as xr


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


def form_times_file(options, file_name):
    # formation of a times list of the form "yyyy.mm.dd hh:00:00"
    my_file = open(file_name, "w")
    t = ['0' + str(t) + ':00:00' if t < 10 else str(t) + ':00:00' for t in range(options['start_time'], options['end_time'] + 1, options['step_time'])]
    
    times = []

    for year in range(options['start_year'], options['end_year'] + 1):
        str_year = str(year)
    
        for month in range(options['start_month'], options['end_month'] + 1):
            if month < 10:
                srt_month = '0' + str(month)
            else:
                srt_month = str(month)

            if month in np.asarray([1, 3, 5, 7, 8, 10, 12]):
                days = range(1, 32)
            elif month in np.asarray([4, 6, 9, 11]):
                days = range(1, 31)
            elif (month == 2) and (((year % 4 == 0) and (year % 100 != 0)) or (year % 400 == 0)): # високосный год
                days = range(1, 30)
            else:
                days = range(1, 29)
            
            for day in days:
                if day < 10:
                    str_day = '0' + str(day)
                else:
                    str_day = str(day)
            
                for time in t:
                    my_file.write(str_year + '.' + srt_month + '.' + str_day + ' ' + time + '\n')
                    times.append(str_year + '.' + srt_month + '.' + str_day + ' ' + time)
    my_file.close()
    return np.array(times)
 

def form_resulting_data_cube_from_parts_by_time(*parts):
    # concatenate of xarray by time
	# (since a large data set has to be uploaded as multiple netCDF files)
	# resulting_cube - 3D np.ndarray (time, lat, lon)
    resulting_cube = parts[0]
    for k in range(1, len(parts)):
        resulting_cube = np.concatenate((resulting_cube, parts[k]), axis = 0)
    return resulting_cube