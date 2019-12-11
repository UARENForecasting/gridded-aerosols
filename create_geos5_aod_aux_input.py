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
# need soft link to get_aeronet.py
from get_aeronet import mean, ang_exp

#################################################################################
# GEOS5 is initialised at 00Z available to download from approx 0600-0700Z      #
# ready for inclusion in foreacsts initialised in WRF at 06Z and 12Z WRF        #
#                                                                               # 
# 12Z GEOS5 is available to download from approx 2100-2200Z                     #
# ready for inclusion in foreacsts initialised in WRF at 18Z and 00Z            #
#                                                                               #
# 120 + 6hrs of GEOS5 data is pulled, 120 for WRF and 6 for initialization diff.# 
#################################################################################

# start timer for script
start_time = time.time()

# set upper and lower time limits for script to run
overwrite_time_limit = 10   # [seconds] 
lower_time_limit = 5 * 60   # [seconds] 5 minutes
upper_time_limit = 4 * 3600 # [seconds] 4 hours

# GEOS-5 or AERONET switch
config = 'geos5'

# find the day and forecast initialisation day
# GEOS5 has ~8 hour latency
time_now = pd.Timestamp.utcnow()

# testing switch
time_now = time_now - pd.Timedelta('1D') - pd.Timedelta('12h')
#print(time_now)

# select GEOS-5 run to download data from (default is 00Z)
geos = '00'
# this switches to 12Z, for WRF 18Z and 00Z
if 21 <= time_now.hour or time_now.hour < 6: 
    geos = '12'

year  = time_now.strftime('%Y')
month = time_now.strftime('%m')
day   = time_now.strftime('%d')

#################################################
# download 84 + 6 = 90 hrs of GEOS-5 forecast   #
#################################################  
if geos == '00':
    forecast_times = [f'{hr:02}' for hr in range(6, 22, 3)] + [f'{hr:02}' for hr in range(0, 22, 3)] * 4 + [f'{hr:02}' for hr in range(0, 10, 3)]    
    forecast_days  = [time_now] * 6 + [time_now + pd.Timedelta('1d')] * 8 + [time_now + pd.Timedelta('2d')] * 8 \
                                    + [time_now + pd.Timedelta('3d')] * 8 + [time_now + pd.Timedelta('4d')] * 8 \
                                    + [time_now + pd.Timedelta('5d')] * 4
if geos == '12':
    forecast_times = [f'{hr:02}' for hr in range(18, 22, 3)] + [f'{hr:02}' for hr in range(0, 22, 3)] * 4 + [f'{hr:02}' for hr in range(0, 22, 3)]    
    forecast_days  = [time_now] * 3 + [time_now + pd.Timedelta('1d')] * 8 + [time_now + pd.Timedelta('2d')] * 8 \
                                    + [time_now + pd.Timedelta('3d')] * 8 + [time_now + pd.Timedelta('4d')] * 8 \
                                    + [time_now + pd.Timedelta('5d')] * 7
#print(forecast_times,len(forecast_times))
#print(forecast_days,len(forecast_days))

#################
# download data #
#################
for forecast_day, forecast_time in zip(forecast_days, forecast_times):
    if time.time() - start_time < upper_time_limit:         
        file_name = 'GEOS.fp.fcst.inst1_2d_hwl_Nx.'+year+month+day+'_'+geos+'+' + forecast_day.strftime('%Y%m%d') + '_' + forecast_time + '00.V01.nc4'
        url = 'https://portal.nccs.nasa.gov/datashare/gmao_ops/pub/fp/forecast/Y'+year+'/M'+month+'/D'+day+'/H'+geos+'/'+file_name
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
    for forecast_day, forecast_time in zip(forecast_days, forecast_times):      
        out_file = 'GEOS.fp.fcst.inst1_2d_hwl_Nx.' + year + month + day + '_'+geos+'_' + forecast_day.strftime('%Y%m%d') + '_' + forecast_time + '00.V01.nc4'
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
for fcstfile in glob.glob('GEOS.fp.fcst.inst1_2d_hwl_Nx.'+year+month+day+'_'+geos+'*'  ):
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
          "GEOS-5 DOWNLOADED FROM "+geos+"Z  \n",
          "TOTAL TIME: ",round((time.time()-start_time)/60.,2)," mins")
    print("###########################")
if config == 'aeronet':
    print("########################### \n",
          "AERONET DOWNLOADED \n",
          "TOTAL TIME: ",round((time.time()-start_time)/60.,2)," mins")
    print("###########################")
