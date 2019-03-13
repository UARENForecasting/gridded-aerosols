#!/usr/bin/env python
import os
import subprocess
import glob
import sys

import numpy as np
import netCDF4 as nc
import pandas as pd

#################################################################################
# GEOS5 is initialised at 12z available to download from approx 1900-2000z      #
# ready for inclusion in foreacsts initialised in WRF at 00z     the next day.  #
#                                                                               #
# Only run at ~2015z (should finish about 2030z) ready to run WPS at 2045z.     # 
#                                                                               #
# total simulation time is 84hrs, first 48hrs with 12z GEOS5 AOD forecast last  # 
# 36hrs with 00z forecast data.                                                 # 
#                                                                               # 
#################################################################################

# find the day and forecast initialisation day
# GEOS5 has ~8 hour latency
time_now = pd.Timestamp.utcnow()

# testing switch
#time_now = time_now - pd.Timedelta('1d')

year  = time_now.strftime('%Y')
month = time_now.strftime('%m')
day   = time_now.strftime('%d')

#########################################
# download first +48hrs of 12z forecast #
#########################################
forecast_times = ['18','21'] + [f'{hr:02}' for hr in range(0, 22, 3)] * 2 + ['00']
forecast_days = [time_now]* 2 + [time_now + pd.Timedelta('1d')] * 8 + [time_now + pd.Timedelta('2d')] * 8 + [time_now + pd.Timedelta('3d')]

# download 12z forecast files for first +48 hrs
for forecast_day, forecast_time in zip(forecast_days, forecast_times):
    file_name = 'GEOS.fp.fcst.inst1_2d_hwl_Nx.' + year + month + day + '_00+' + forecast_day.strftime('%Y%m%d') + '_' + forecast_time + '00.V01.nc4'
    print(file_name)
    url = 'ftp://ftp.nccs.nasa.gov/fp/forecast/Y'+year+'/M'+month+'/D'+day+'/H00/'+file_name
    try:
        retcode = subprocess.call(" wget --user=gmao_ops --password=''  " + url, shell=True)
        if retcode < 0:
            print("Child was terminated by signal", -retcode, file=sys.stderr)
        else:
            print("Child returned", retcode, file=sys.stderr)
    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)

########################################
# fill in last 36hrs with 00z forecast #
########################################
constant_times =  [f'{hr:02}' for hr in range(3,22, 3)] + [f'{hr:02}' for hr in range(0,13, 3)]
constant_days  =  [time_now + pd.Timedelta('3d')] * 7 + [time_now + pd.Timedelta('4d')] * 5

# download 00z forecast files for +48-84hrs
for constant_day, constant_time in zip(constant_days, constant_times):
    z00_file_name = 'GEOS.fp.fcst.inst1_2d_hwl_Nx.' + year + month + day + '_00+' + constant_day.strftime('%Y%m%d') + '_' + constant_time + '00.V01.nc4'
    print(z00_file_name)
    url = 'ftp://ftp.nccs.nasa.gov/fp/forecast/Y'+year+'/M'+month+'/D'+day+'/H00/'+z00_file_name
    try:
        retcode = subprocess.call(" wget --user=gmao_ops --password=''  " + url, shell=True)
        if retcode < 0:
            print("Child was terminated by signal", -retcode, file=sys.stderr)
        else:
            print("Child returned", retcode, file=sys.stderr)
    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)
   
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
