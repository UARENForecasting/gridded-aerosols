#!/usr/bin/env python
import os
from io import StringIO
import numpy as np
import netCDF4 as nc
import pandas as pd
import requests 
import glob
import sys

# find the day and forecast initialisation day
# ICAP day has ~1day latency, simulations start at 12UTC
time_now = pd.Timestamp.now(tz='UTC')
year  = str(time_now)[:4]
month = str(time_now)[5:7]
day   = str(time_now)[8:10]
init_ymdt = time_now - pd.Timedelta('1d')
init_day = str(init_ymdt)[8:10]

# download latest forecast file
file_name = str('icap_'+year+month+init_day+'00_MME_totaldustaod550.nc')
url = 'https://usgodae.org/pub/outgoing/nrl/ICAP-MME/'+year+'/'+year+month+'/'+file_name
os.system(' wget -c --no-check-certificate '+url)

times = ['12','18','00','06','12','18','00','06','12','18','00','06']
forecast_strs = [time_now,(time_now + pd.Timedelta('1d')),(time_now + pd.Timedelta('2d')),(time_now + pd.Timedelta('3d'))]

for i in range(len(times)):
    # select correct index for date based on forecast time
    if i < 2 :
        d = 0 
    if 1 < i < 6 :
        d = 1 
    if 5 < i < 10 :
        d = 2
    if 9 < i < 12 :
        d = 3 
 
    # get data from ICAP file
    ncfile = nc.Dataset(file_name,'r+')
    aod = ncfile.variables['dust_aod_mean'][6+i,:,:]
    aod[aod<0] = 10e-8

    stdev  = ncfile.variables['dust_aod_stdv'][6+i,:,:]
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

os.system('rm '+file_name)

