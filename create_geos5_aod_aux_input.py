#!/usr/bin/env python
import os
import subprocess
import glob
import sys
       
import subprocess
import requests
import time
import numpy as np
import netCDF4 as nc
import pandas as pd
from get_aeronet import mean, ang_exp

#################################################################################
# GEOS5 is initialised at 00z available to download from approx 0300-0400z      #
# ready for inclusion in foreacsts initialised in WRF at 00z the next day.      #
#                                                                               #
# +84hrs of GEOS5 data is pulled, all data coming from 00z run                  # 
#################################################################################
# start timer for script
start_time = time.time()

# set upper and lower time limits for script to run
overwrite_time_limit = 10   # [seconds] 
lower_time_limit = 5 * 60   # [seconds] 5 minutes
upper_time_limit = 3 * 3600 # [seconds] 2 hours

# GEOS-5 or AERONET switch
config = 'geos5'

# find the day and forecast initialisation day
# GEOS5 has ~8 hour latency
time_now = pd.Timestamp.utcnow()

# testing switch
#time_now = time_now + pd.Timedelta('1D')

year  = time_now.strftime('%Y')
month = time_now.strftime('%m')
day   = time_now.strftime('%d')

#####################################################
# download 84 + 18 = 102 hrs of 00Z GEOS-5 forecast #
#####################################################  
all_forecast_times = [f'{hr:02}' for hr in range(0, 22, 3)] * 4  + [f'{hr:02}' for hr in range(0,4, 3)] 
all_forecast_days = [time_now] * 8 + [time_now + pd.Timedelta('1d')] * 8 +  [time_now + pd.Timedelta('2d')] * 8 \
                               + [time_now + pd.Timedelta('3d')] * 7

#################
# download data #
#################
for forecast_day, forecast_time in zip(all_forecast_days, all_forecast_times):
    if time.time() - start_time < upper_time_limit:       
    #if time.time()-start_time > lower_time_limit  or time.time()-start_time >= upper_time_limit: 
        file_name = 'GEOS.fp.fcst.inst1_2d_hwl_Nx.' + year + month + day + '_00+' + forecast_day.strftime('%Y%m%d') + '_' + forecast_time + '00.V01.nc4'
        #print(file_name)
        url = 'https://portal.nccs.nasa.gov/datashare/gmao_ops/pub/fp/forecast/Y'+year+'/M'+month+'/D'+day+'/H00/'+file_name
        try:
            retcode = subprocess.call(" wget -nc --user=gmao_ops --password=''  "+url+" --progress=bar:force 2>&1 | tail -f -n +6 ", shell=True)
            if retcode < 0:
                print("Child was terminated by signal", -retcode, file=sys.stderr)
            else:
                print("Child returned", retcode, file=sys.stderr)
        except OSError as e:
            print("Execution failed:", e, file=sys.stderr)
    print("########################### \n",
          "DOWNLOAD TIME: ",round((time.time()-start_time)/60.,2)," mins")
    print("###########################")

#################################################################################  
# Determine if GEOS-5 has been sucessful based on how long the script is taking #
# if download takes less that 5 minutes, data is not avaiable                   #
# if download takes longer than the limit, there is a problem with download     #
# in both instances script will populate a dummy 2D GEOS-5 file with AERONET    #
# daily average data from UofA site                                             # 
#################################################################################

if overwrite_time_limit <= time.time()-start_time < lower_time_limit  or time.time()-start_time >= upper_time_limit: 
    config = 'aeronet'
    for forecast_day, forecast_time in zip(all_forecast_days, all_forecast_times):      
        out_file = 'GEOS.fp.fcst.inst1_2d_hwl_Nx.' + year + month + day + '_00_' + forecast_day.strftime('%Y%m%d') + '_' + forecast_time + '00.V01.nc4'
        in_file = 'dummy_geos5_data_file.nc4'

        subprocess.run(["cp",in_file,out_file])
        subprocess.run(["ncatted","-O","-a","units,time,m,c,"+"minutes since "+ forecast_day.strftime('%Y%m%d') +" "+forecast_time+":00:00",out_file])
        subprocess.run(["ncatted","-O","-a","begin_date,time,m,l,"+forecast_day.strftime('%Y%m%d'),out_file])
        subprocess.run(["ncatted","-O","-a","begin_time,time,m,l,"+forecast_time+"0000",out_file])

        ncfile = nc.Dataset(in_file,'r+')
        aod_index = ncfile.variables['TOTEXTTAU'][:]
        aod_index[:] = mean
        ncfile.variables['TOTEXTTAU'][:] = aod_index
        ang_index = ncfile.variables['TOTANGSTR'][:]
        ang_index[:] = ang_exp
        ncfile.variables['TOTANGSTR'][:] = ang_index

################################################################################# 
# convert all files to metgrid.exe readable files and clean up downloaded files #
#################################################################################
for fcstfile in glob.glob('GEOS.fp.fcst*'):
    try:
        retcode = subprocess.call("./write_aerosols_for_metgrid.Linux " + fcstfile, shell=True)
        if retcode < 0:
            print("Child was terminated by signal", -retcode, file=sys.stderr)
        else:
            print("Child returned", retcode, file=sys.stderr)
    except OSError as e:
            print("Execution failed:", e, file=sys.stderr)
    if config == 'aeronet':
        os.remove(fcstfile)


if config == 'geos5':
    print("########################### \n",
          "GEOS-5 DOWNLOADED  \n",
          "TOTAL TIME: ",round((time.time()-start_time)/60.,2)," mins")
    print("###########################")
if config == 'aeronet':
    print("########################### \n",
          "AERONET DOWNLOADED \n",
          "TOTAL TIME: ",round((time.time()-start_time)/60.,2)," mins")
    print("###########################")
