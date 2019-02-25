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
# GEOS5 is initialised at 1200z available to download from approx 1900-2000z    #
# ready for inclusion in foreacsts initialised in WRF at 0000UTC the next day.  #
#                                                                               #
# Only run at 2015UTC (should finish about 2030z) ready to run WPS at 2045z.    # 
#                                                                               #
# total simulation time is 84hrs, first 48hrs with GEOS5 AOD forecast last      # 
# 36hrs with constant AOD field.                                                # 
#                                                                               # 
#################################################################################

# find the day and forecast initialisation day
# GEOS has ~8 hour latency
time_now = pd.Timestamp.now(tz='UTC')

# testing switch
#time_now = time_now - pd.Timedelta('1d')

year  = str(time_now)[:4]
month = str(time_now)[5:7]
day   = str(time_now)[8:10]

#####################################
# download first +48hrs of forecast #
#####################################
forecast_times = ['00','03','06','09','12','15','18','21','00','03','06','09','12','15','18','21','00']
forecast_strs = [(time_now + pd.Timedelta('1d')),(time_now + pd.Timedelta('2d')),(time_now + pd.Timedelta('3d'))]
for i in range(len(forecast_times)):
    # select correct index for date based on forecast start time initialization 0000UTC(+1day)
    if      i <  8 :
        d = 0 
    if  7 < i < 16 :
        d = 1
    if 15 < i      :
        d = 2

    # download latest forecast file
    file_name = str('GEOS.fp.fcst.inst1_2d_hwl_Nx.'+year+month+day+'_12+'+str(forecast_strs[d])[:4]+str(forecast_strs[d])[5:7]+str(forecast_strs[d])[8:10]+'_'+forecast_times[i]+'00.V01.nc4')
    print (file_name)
    url = 'ftp://ftp.nccs.nasa.gov/fp/forecast/Y'+year+'/M'+month+'/D'+day+'/H12/'+file_name
    os.system(' wget --user=gmao_ops --password='' '+url)

##########################################
# fill in last 36hrs with constant value #
##########################################
constant_times = ['03','06','09','12','15','18','21','00','03','06','09','12']
constant_strs = [(time_now + pd.Timedelta('3d')),(time_now + pd.Timedelta('4d'))]
for j in range(len(constant_times)):
    # select correct index for date based on forecast start time initialization 0000UTC(+1day)
    if      j <  7 :
        e = 0 
    if  6 < j < 12 :
        e = 1

    constant_file_name  = str('GEOS.fp.fcst.inst1_2d_hwl_Nx.'+year+month+day+'_12+'+str(constant_strs[e])[:4]+str(constant_strs[e])[5:7]+str(constant_strs[e])[8:10]+'_'+constant_times[j]+'00.V01.nc4')
    os.system('cp '+file_name+' '+constant_file_name)
      
################################################################################# 
# convert all files to metgrid.exe readable files and clean up downloaded files #
#################################################################################
for fcstfile in glob.glob('GEOS.fp.fcst.inst1_2d_hwl_Nx.*'):
    os.system('./write_aerosols_for_metgrid.Linux '+fcstfile)
    os.system('rm '+fcstfile)

