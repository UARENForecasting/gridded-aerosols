#!/usr/bin/env python
import os
from io import StringIO
import numpy as np
import netCDF4 as nc
import pandas as pd
import requests 
import glob
import sys

#################################################################################
# GEOS5 is initialised at 1800UTC available to download at approx 1900UTC       #
# ready for inclusion in foreacsts initialised in WRF at 0000UTC the next day.  #
#                                                                               #
# Run after 1900UTC but before 2359UTC                                          # 
#################################################################################

# find the day and forecast initialisation day
# GEOS has ~1 hour latency
time_now = pd.Timestamp.now(tz='UTC')

# testing switch
time_now = time_now - pd.Timedelta('1d')

year  = str(time_now)[:4]
month = str(time_now)[5:7]
day   = str(time_now)[8:10]
init_ymdt = time_now - pd.Timedelta('1d')
init_day = str(init_ymdt)[8:10]

times = ['00','03','06','09','12','15','18','21','00']
forecast_strs = [(time_now + pd.Timedelta('1d')),(time_now + pd.Timedelta('2d'))]

for i in range(len(times)):
    # select correct index for date based on forecast start time 0000UTC
    if      i <  8 :
        d = 0 
    if  7 < i < 16 :
        d = 1 
    if 15 < i < 24 :
        d = 2
    print ('###############')
    print (times[i])
    print (time_now)
    print (forecast_strs[d])
    print ('###############') 
    # download latest forecast file
    file_name = str('GEOS.fp.fcst.inst1_2d_hwl_Nx.'+year+month+day+'_18+'+str(forecast_strs[d])[:4]+str(forecast_strs[d])[5:7]+str(forecast_strs[d])[8:10]+'_'+times[i]+'00.V01.nc4')
    print (file_name)
    url = 'ftp://ftp.nccs.nasa.gov/fp/forecast/Y'+year+'/M'+month+'/D'+day+'/H18/'+file_name
    os.system(' wget --user=gmao_ops --password='' '+url)

for fcstfile in glob.glob('GEOS.fp.fcst.inst1_2d_hwl_Nx.*'):
    os.system('./write_aerosols_for_metgrid.Linux '+fcstfile)
    os.system('rm '+fcstfile)

