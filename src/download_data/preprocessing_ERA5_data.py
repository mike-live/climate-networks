import numpy as np
import pandas as pd
from global_land_mask import globe


def get_resulting_cube_with_land_mask(resulting_cube, lat, lon, times):
    # resulting_cube - 3D np.ndarray (time, lat, lon)
    # lat -   1D np.ndarray (latitude)
    # lon -   1D np.ndarray (longitude)
    # times - 1D np.ndarray (with 'yyyy.mm.dd hh:00:00')
    
    n_time, n_lat, n_lon = resulting_cube.shape
    resulting_cube_land_masked = np.zeros((n_time, n_lat, n_lon))
    for k_lat in range(0, n_lat):
        for k_lon in range(0, n_lon):
            if globe.is_land(lat[k_lat], lon[k_lon]):
                resulting_cube_land_masked[:, k_lat, k_lon] = np.asarray([np.nan]*len(times))
            else:
                resulting_cube_land_masked[:, k_lat, k_lon] = resulting_cube[:, k_lat, k_lon]
    return resulting_cube_land_masked


def preprocessing(resulting_cube, times):
    # resulting_cube - 3D np.ndarray (time, lat, lon)
    # times - 1D np.ndarray (with 'yyyy.mm.dd hh:00:00')
    
    # np.nan are not processed separately, since np.nan are on land, 
    # and at each point in time this will be np.nan (in ERA5 only)
    
    n_time, n_lat, n_lon = resulting_cube.shape
    resulting_cube_after_preproc = resulting_cube.copy()
    
    days_reviewed = []
    for k_time in range(0, n_time):
        day = times[k_time][4:11]
        if day not in days_reviewed:
            days_reviewed.append(day)
            arr_mean = np.zeros((n_lat, n_lon))
            inds_for_day = [ind for ind in range(0, len(times)) if day in times[ind]]
            for ind in inds_for_day:
                arr_mean += resulting_cube[ind, :, :]
            arr_mean /= len(inds_for_day)
            
            for ind in inds_for_day:
                resulting_cube_after_preproc[ind, :, :] -= arr_mean
    return resulting_cube_after_preproc
