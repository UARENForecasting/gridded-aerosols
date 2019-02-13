#!/usr/bin/env python
import os
from io import StringIO
import numpy as np
import netCDF4 as nc
import pandas as pd
import requests 
import glob
import sys
##################################################################################
# ICAP is initialised at 0000UTC available to download at approx 2350UTC         # 
# ready for inclusion in foreacsts initialised in WRF at 0000UTC the next day.   #
#                                                                                #
# Run after 2350UTC but before 2359UTC                                           #    
##################################################################################

# find the day and forecast initialisation day
# ICAP data has ~1day latency, simulations start at 12UTC
time_now = pd.Timestamp.now(tz='UTC')

# testing switch
time_now = time_now - pd.Timedelta('1d')


year  = str(time_now)[:4]
month = str(time_now)[5:7]
day   = str(time_now)[8:10]
init_ymdt = time_now - pd.Timedelta('1d')
init_day = str(init_ymdt)[8:10]

# download latest forecast file
file_name = str('icap_'+year+month+day+'00_MME_totaldustaod550.nc')
url = 'https://usgodae.org/pub/outgoing/nrl/ICAP-MME/'+year+'/'+year+month+'/'+file_name
os.system(' wget -c --no-check-certificate '+url)

times = ['00','06','12','18','00','06','12','18','00','06','12','18','00']
forecast_strs = [(time_now + pd.Timedelta('1d')),(time_now + pd.Timedelta('2d')),(time_now + pd.Timedelta('3d')),(time_now + pd.Timedelta('4d'))]

for i in range(len(times)):
    # select correct index for date based on forecast start time 0000UTC
    if     i  <  4 :
        d = 0 
    if  3 < i <  8 :
        d = 1 
    if  7 < i < 12 :
        d = 2
    if 11 < i < 15 :
        d = 3 
 
    # get data from ICAP file
    ncfile = nc.Dataset(file_name,'r+')
    aod = ncfile.variables['dust_aod_mean'][4+i,:,:]
    aod[aod<0] = 10e-8

    stdev  = ncfile.variables['dust_aod_stdv'][4+i,:,:]
    inlat  = ncfile.variables['lat']
    inlon  = ncfile.variables['lon']
    intime = ncfile.variables['time'][0]

    # output cut data with correct timedate stamp 
    # prep variables
    outfile = 'icap_'+str(forecast_strs[d])[:4]+str(forecast_strs[d])[5:7]+str(forecast_strs[d])[8:10]+times[i]+'_forecast_MME_totaldustaod550.nc'
    ncoutfile =  nc.Dataset(outfile,"w",format="NETCDF4")
    time = ncoutfile.createDimension("time", 1)
    lat = ncoutfile.createDimension("lat", 180)
    lon = ncoutfile.createDimension("lon", 360)
     
    outtime = ncoutfile.createVariable("time","i4",("time",)) 
    outlat = ncoutfile.createVariable("lat","f4",("lat",))
    outlon = ncoutfile.createVariable("lon","f4",("lon",))
    totextau = ncoutfile.createVariable("TOTEXTAU","f4",("time","lat","lon",))
    taustdev = ncoutfile.createVariable("TAUSTDEV","f4",("time","lat","lon",))

    # write data
    ncoutfile.variables['time'].begin_time = int(str(times[i])+'00'+'00')
    ncoutfile.variables['time'].begin_date = int(str(forecast_strs[d])[:4]+str(forecast_strs[d])[5:7]+str(forecast_strs[d])[8:10])
      
    ncoutfile.variables['lat'][:] = inlat[:]
    ncoutfile.variables['lon'][:] = inlon[:]
    ncoutfile.variables['TOTEXTAU'][:] = aod
    ncoutfile.variables['TAUSTDEV'][:] = stdev

    ncoutfile.close()
    print ('conversion complete '+outfile)


for fcstfile in glob.glob('*forecast_MME_totaldustaod550.nc'):
    os.system('./write_aerosols_for_metgrid_mod.Linux '+fcstfile)

    os.system('rm '+fcstfile)

os.system('rm '+file_name)
