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
from get_aeronet_master import aod_mean,ang_exp

#################################################################################
# GEOS5 is initialised at 00z available to download from approx 0300-0400z      #
# ready for inclusion in foreacsts initialised in WRF at 00z the next day.      #
#                                                                               #
# +84hrs of GEOS5 data is pulled, all data coming from 00z run                  # 
#################################################################################
# start timer for script
start_time = time.time()
# set upper and lower time limits for script to run
lower_time_limit = 5 * 60   # [seconds] 5 minutes
upper_time_limit = 2 * 3600 # [seconds] 1 hour 

# GEOS or AERONET switch
config = 0
# Which Fx run
fx_run = 0

# find the day and forecast initialisation day
# GEOS5 has ~8 hour latency
time_now = pd.Timestamp.utcnow()
print(time_now)
# testing switch
#time_now = time_now - pd.Timedelta('6h')
year  = time_now.strftime('%Y')
month = time_now.strftime('%m')
day   = time_now.strftime('%d')

####################################################
# download 84hrs of forecast based on current time #
####################################################
# this is for the 06z run  
if 6 <= time_now.hour < 12: 
    print("########################### \n",
          "DOWNLOADING FOR 06z")
    print("###########################")
    forecast_times = [f'{hr:02}' for hr in range(6, 22, 3)] + [f'{hr:02}' for hr in range(0,22, 3)] * 3 + ['00']
    forecast_days  = [time_now] * 6 + [time_now + pd.Timedelta('1d')] * 8 \
                                    + [time_now + pd.Timedelta('2d')] * 8 + [time_now + pd.Timedelta('3d')] * 8 \
                                    + [time_now + pd.Timedelta('4d')]
# this is for the 12z run  
if 12 <= time_now.hour < 18:
    fx_run = 1
    print("########################### \n",
          "DOWNLOADING FOR 12z")
    print("###########################")
    forecast_times = [f'{hr:02}' for hr in range(12, 22, 3)] + [f'{hr:02}' for hr in range(0,22, 3)] * 3 + ['00','06','09']
    forecast_days  = [time_now] * 4 + [time_now + pd.Timedelta('1d')] * 8 \
                   + [time_now + pd.Timedelta('2d')] * 8 + [time_now + pd.Timedelta('3d')] * 8 \
                   + [time_now + pd.Timedelta('4d')] * 3
# this is for the 18z run 
if  18 <= time_now.hour < 24 : 
    fx_run = 2
    print("########################### \n",
          "DOWNLOADING FOR 18z")
    print("###########################")
    forecast_times = ['18','21']    + [f'{hr:02}' for hr in range(0, 22, 3)] * 3 + [f'{hr:02}' for hr in range(0,13, 3)]
    forecast_days  = [time_now] * 2 + [time_now + pd.Timedelta('1d')] * 8 + [time_now + pd.Timedelta('2d')] * 8 \
                   + [time_now + pd.Timedelta('3d')] * 8 + [time_now + pd.Timedelta('4d')] * 5
# this is for the 00z run 
if  0 <= time_now.hour < 6 : 
    fx_run = 3
    print("########################### \n",
          "DOWNLOADING FOR 00z")
    print("###########################")
    forecast_times = [f'{hr:02}' for hr in range(0, 22, 3)] * 3  + [f'{hr:02}' for hr in range(0,19, 3)]
    forecast_days  = [time_now] * 8 + [time_now + pd.Timedelta('1d')] * 8 +  \
                     [time_now + pd.Timedelta('2d')] * 8 + [time_now + pd.Timedelta('3d')] * 7

#################
# download data #
#################
for forecast_day, forecast_time in zip(forecast_days, forecast_times):
    if time.time() - start_time < upper_time_limit:       
        file_name = 'GEOS.fp.fcst.inst1_2d_hwl_Nx.' + year + month + day + '_00+' + forecast_day.strftime('%Y%m%d') + '_' + forecast_time + '00.V01.nc4'
        #print(file_name)
        url = 'https://portal.nccs.nasa.gov/datashare/gmao_ops/pub/fp/forecast/Y'+year+'/M'+month+'/D'+day+'/H00/'+file_name
        try:
            retcode = subprocess.call(" wget --user=gmao_ops --password=''  " + url, shell=True)
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
# if download takes longer than 1 hour, there is a problem with download        #
# in both instances script will populate a dummy 2D GEOS-5 file with AERONET    #
# daily average data from UofA site                                             # 
#################################################################################

if time.time()-start_time < lower_time_limit  or time.time()-start_time >= upper_time_limit: 
    config = 1
    for forecast_day, forecast_time in zip(forecast_days, forecast_times):      
        out_file = 'GEOS.fp.fcst.inst1_2d_hwl_Nx.' + year + month + day + '_00+' + forecast_day.strftime('%Y-%m-%d') + '_' + forecast_time + '00.V01.nc4'
        in_file = 'dummy_geos5_data_file.nc4'

        subprocess.run(["cp",in_file,out_file])
        subprocess.run(["ncatted","-O","-a","units,time,m,c,"+"minutes since "+ forecast_day.strftime('%Y-%m-%d') +" "+forecast_time+":00:00",out_file])
        subprocess.run(["ncatted","-O","-a","begin_date,time,m,l,"+forecast_day.strftime('%Y%m%d'),out_file])
        subprocess.run(["ncatted","-O","-a","begin_time,time,m,l,"+forecast_time+"0000",out_file])

        ncfile       = nc.Dataset(in_file,'r+')
        aod_index    = ncfile.variables['TOTEXTTAU'][:]
        aod_index[:] = aod_mean
        ncfile.variables['TOTEXTTAU'][:] = aod_index
        ang_index    = ncfile.variables['TOTANGSTR'][:]
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
    os.remove(fcstfile)

fx_runs = ['06z','12z','18z','00z']
if config == 0:
    print("########################### \n",
          "GEOS-5 DOWNLOADED FOR "+fx_runs[fx_run]+"   \n",
          "TOTAL TIME: ",round((time.time()-start_time)/60.,2)," mins")
    print("###########################")
if config == 1:
    print("########################### \n",
          "AERONET DOWNLOADED  FOR "+fx_runs[fx_run]+"   \n",
          "TOTAL TIME: ",round((time.time()-start_time)/60.,2)," mins")
    print("###########################")
