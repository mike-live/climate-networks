# climate-networks

## Installation

You need install Python version 3.8 or higher.  

Dependencies:  
1. cartopy  
2. cdsapi  
3. cv2  
4. dateutil  
5. global_land_mask  
6. matplotlib  
7. numba  
8. numpy  
9. pathlib2  
10. pandas  
11. scipy  
12. tqdm  
13. xarray


## Getting started

**Step 1.** Register to download the required climate data from the Copernicus Climate Data Store (CDS). To do this, follow the next [step-by-step guide](https://confluence.ecmwf.int/display/CKB/How+to+install+and+use+CDS+API+on+Windows):
1. [Register on CDS](https://cds.climate.copernicus.eu/user/register)
2. [Login to CDS](https://cds.climate.copernicus.eu/user/login)
3. Go to [this page](https://cds.climate.copernicus.eu/api-how-to) and copy the 2 line code displayed in the black box in the "Install the CDS API key" section
4. Paste the 2 line code into a  %USERPROFILE%\.cdsapirc file, where in your windows environment, %USERPROFILE% is usually located at C:\Users\Username folder.
5. Install the CDS API client by running the following command in a Command Prompt window:  
	`pip3 install cdsapi`  
	or  
	`pip3 install --user cdsapi`
6. Once the CDS API client is installed, you can use it to query data from datasets listed in the CDS catalogs. You should agree to the Terms of Use for all datasets you intend to download.

**Step 2.** With our program you can download [ERA5 hourly data](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels?tab=overview) (mean sea level pressure or sea surface temperature) on single levels from 1979 to present from the CDS. ERA5 is the fifth generation ECMWF reanalysis for the global climate and weather. To download the required climate data, follow these steps:
1. Update structure *download_ERA5_options* in *config.py* file as per your requirements.
2. Run the program with parameter *--download*. To run from the command line use:  
	`python -m main --download`


## Available options

1. *--download*  
2. *--compute_correlations*  
3. *--compute_correlations_and_metrics*  
4. *--compute_metrics*  
5. *--compute_diff_metrics*  
6. *--plot_metrics*  
	There are two plotting modes available:  
		a. plotting calculated 1D and 2D metrics  
		b. plotting tropical cyclones (*best_track_ecscsuc_2020_m.xls* file collected Regional Specialised Meteorological Centre) over metrics  
7. *--compute_cyclone_metrics*  
	Computation all-time local mean and std of metrics for each spatial grid cyclone point over time. It is necessary to plot the metric, mean metric and mean plus minus std versus time along the cyclone track. 
	