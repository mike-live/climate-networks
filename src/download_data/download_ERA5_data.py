import cdsapi
import numpy as np
import xarray as xr
from . import read_ERA5_netCDF_files as read_nc
from . import preprocessing_ERA5_data as preproc


def download_raw_data(options, file_name):
    c = cdsapi.Client()
    
    download_ERA5_structure = {
        'product_type': 'reanalysis',
        'variable': options['variable'],
        'year': [str(y) for y in range(options['start_year'], options['end_year'] + 1)],
        'month': ['0' + str(m) if m < 10 else str(m) for m in range(options['start_month'], options['end_month'] + 1)],
        'day': ['0' + str(d) if d < 10 else str(d) for d in range(options['start_day'], options['end_day'] + 1)],
        'time': ['0' + str(t) + ':00' if t < 10 else str(t) + ':00' for t in range(options['start_time'], options['end_time'] + 1, options['step_time'])],
        'area': [options['north'], options['west'], options['south'], options['east']],
        'format': 'netcdf',
        'grid': str(options['resolution']) + '/' + str(options['resolution']),  
    }
    
    c.retrieve(
        'reanalysis-era5-single-levels',
        download_ERA5_structure,
        file_name)


def preprocessing_data(download_ERA5_options, resulting_cube, latitude, longitude, times):
    if download_ERA5_options['land_mask'] == True:
        print('Getting points on the sea only...', end = ' ')
        resulting_cube = preproc.get_resulting_cube_with_land_mask(resulting_cube, latitude, longitude, times)
        file_name = download_ERA5_options['work_dir'] / download_ERA5_options['res_cube_land_masked_file_name']
        np.savez(file_name, resulting_cube)
        print('Done\n')
    
    if download_ERA5_options['preprocessing'] == True:
        print('Data preprocessing...', end = ' ')
        resulting_cube = preproc.preprocessing(resulting_cube, times)
        if download_ERA5_options['land_mask'] == True:
            file_name = download_ERA5_options['work_dir'] / download_ERA5_options['res_cube_land_masked_and_preproc_file_name']
        else:
            file_name = download_ERA5_options['work_dir'] / download_ERA5_options['res_cube_preproc_file_name']
        np.savez(file_name, resulting_cube)
        print('Done\n')
    

def download_and_preprocessing_ERA5_data(download_ERA5_options):
    start_year = download_ERA5_options['start_year']
    end_year = download_ERA5_options['end_year']
    middle_year = (start_year + end_year) // 2
    
    print('Downloading data from cds.climate.copernicus.eu...')
    # download the first part
    download_ERA5_options['end_year'] = middle_year
    file_name_1st = download_ERA5_options['work_dir'] / (download_ERA5_options['name_var'] + '_' + \
                                                         str(start_year) + '_' + str(middle_year) + '.nc')
    download_raw_data(download_ERA5_options, file_name_1st)
    
    # download the second part
    download_ERA5_options['start_year'] = middle_year + 1
    download_ERA5_options['end_year'] = end_year
    file_name_2nd = download_ERA5_options['work_dir'] / (download_ERA5_options['name_var'] + '_' + \
                                                         str(middle_year + 1) + '_' + str(end_year) + '.nc')
    download_raw_data(download_ERA5_options, file_name_2nd)
    download_ERA5_options['start_year'] = start_year
    print('Done\n')
    
    # npz cube formation
    print('Forming the resulting data cube...')
    dset_1 = xr.open_dataset(str(file_name_1st))
    data_cube_1 = read_nc.get_data_cube(dset_1, download_ERA5_options['name_var'])
    dset_2 = xr.open_dataset(str(file_name_2nd))
    data_cube_2 = read_nc.get_data_cube(dset_2, download_ERA5_options['name_var'])

    longitude = read_nc.get_longitude(dset_1, 'longitude')
    print("n_longitude = ", len(longitude))
    latitude = read_nc.get_latitude(dset_1, 'latitude')
    print("n_latitude = ", len(latitude))
    np.savetxt(download_ERA5_options['work_dir'] / download_ERA5_options['lon_file_name'], longitude, fmt = '%.2f')
    np.savetxt(download_ERA5_options['work_dir'] / download_ERA5_options['lat_file_name'], latitude, fmt = '%.2f')
    
    times = read_nc.form_times(download_ERA5_options)
    print("n_times = ", len(times))
    np.savetxt(download_ERA5_options['work_dir'] / download_ERA5_options['times_file_name'], times, fmt = '%s')
    
    resulting_cube = read_nc.form_resulting_data_cube_from_parts_by_time(data_cube_1, data_cube_2)
    print('resulting_cube.shape = ', resulting_cube.shape)
    np.savez(download_ERA5_options['work_dir'] / download_ERA5_options['res_cube_file_name'], resulting_cube)
    print('Done\n')
    
    preprocessing_data(download_ERA5_options, resulting_cube, latitude, longitude, times)
