#!/usr/bin/env python
import os
import subprocess
import glob
import sys

import requests
import time
import numpy as np
import netCDF4 as nc
import pandas as pd

#################################################################################
# GEOS5 is initialised at 00z available to download from approx 0300-0400z      #
# ready for inclusion in foreacsts initialised in WRF at 00z the next day.      #
#                                                                               #
# +84hrs of GEOS5 data is pulled, all data coming from 00z run                  # 
#################################################################################
time_limit = 2*3600 # [seconds]  2 hours 
start_time = time.time()

# find the day and forecast initialisation day
# GEOS5 has ~8 hour latency
time_now = pd.Timestamp.utcnow()

# testing switch
#time_now = time_now - pd.Timedelta('12h')

year  = time_now.strftime('%Y')
month = time_now.strftime('%m')
day   = time_now.strftime('%d')

####################################################
# download 84hrs of forecast based on current time #
####################################################
# this is for the 06z run  
if 6 <= time_now.hour < 12: 
    forecast_times = [f'{hr:02}' for hr in range(6, 22, 3)] + [f'{hr:02}' for hr in range(0,22, 3)] * 3 + ['00']
    forecast_days  = [time_now] * 6 + [time_now + pd.Timedelta('1d')] * 8 \
                                    + [time_now + pd.Timedelta('2d')] * 8 + [time_now + pd.Timedelta('3d')] * 8 \
                                    + [time_now + pd.Timedelta('4d')]
# this is for the 12z run  
if 12 <= time_now.hour < 18:
    forecast_times = [f'{hr:02}' for hr in range(12, 22, 3)] + [f'{hr:02}' for hr in range(0,22, 3)] * 3 + ['00','06','09']
    forecast_days  = [time_now] * 4 + [time_now + pd.Timedelta('1d')] * 8 \
                                    + [time_now + pd.Timedelta('2d')] * 8 + [time_now + pd.Timedelta('3d')] * 8 \
                                    + [time_now + pd.Timedelta('4d')] * 3
# this is for the 18z run 
if  18 <= time_now.hour < 24 : 
    forecast_times = ['18','21']    + [f'{hr:02}' for hr in range(0, 22, 3)] * 3 + [f'{hr:02}' for hr in range(0,13, 3)]
    forecast_days  = [time_now] * 2 + [time_now + pd.Timedelta('1d')] * 8 + [time_now + pd.Timedelta('2d')] * 8 \
                                    + [time_now + pd.Timedelta('3d')] * 8 + [time_now + pd.Timedelta('4d')] * 5
# this is for the 00z run 
if  0 <= time_now.hour < 6 : 
    forecast_times = [f'{hr:02}' for hr in range(0, 22, 3)] * 3  + [f'{hr:02}' for hr in range(0,19, 3)]
    forecast_days  = [time_now + pd.Timedelta('1d')] * 8 + [time_now + pd.Timedelta('2d')] * 8 \
                   + [time_now + pd.Timedelta('3d')] * 8 + [time_now + pd.Timedelta('4d')] * 7
 
#################
# download data #
#################
for forecast_day, forecast_time in zip(forecast_days, forecast_times):
    # stop download if passed time limit
    if time.time() - start_time < time_limit:       
        file_name = 'GEOS.fp.fcst.inst1_2d_hwl_Nx.' + year + month + day + '_00+' + forecast_day.strftime('%Y%m%d') + '_' + forecast_time + '00.V01.nc4'
        print(file_name)
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
# convert all files to metgrid.exe readable files and clean up downloaded files #
#################################################################################
for fcstfile in glob.glob('GEOS.fp.fcst*'):
    # stop conversion if passed time limit
    if time.time() - start_time < time_limit:
        try:
            retcode = subprocess.call("./write_aerosols_for_metgrid.Linux " + fcstfile, shell=True)
            if retcode < 0:
                print("Child was terminated by signal", -retcode, file=sys.stderr)
            else:
                print("Child returned", retcode, file=sys.stderr)
        except OSError as e:
            print("Execution failed:", e, file=sys.stderr)
    os.remove(fcstfile)

# stop download if passed time limit
if time.time() - start_time < time_limit: 
    print("########################### \n",
          "TOTAL TIME IS ",round((time.time()-start_time)/60.,2)," mins")
    print("###########################")

else: 
    print("########################### \n",
          "DOWNLOAD EXCEEDED TIME LIMIT ",round((time.time() - start_time)/60.,2)," mins")
    print("###########################")
