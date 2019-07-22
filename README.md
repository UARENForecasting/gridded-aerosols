# gridded-aerosols
scripts for getting and analyzing gridded aerosol products


GEOS5 - data from: https://gmao.gsfc.nasa.gov/GMAO_products/NRT_products.php

Instructions for running scripts to download GEOS5 2D aerosol data, partition it into seperate forecast files and finally put it in a format (temporary ungrib files) ready to be used in metgrid.exe: 

1. Compilation of the fortran code needs to be done first

$ ifort -convert big_endian -I/usr/include write_aerosols_for_metgrid.f -L/st1/luong/lib/netcdf-4.3.3.1/lib -lnetcdf -lnetcdff -o write_aerosols_for_metgrid.Linux
{likely will need to change pathways to netcdf library}

2. Run python script to download and process GEOS5 2D aerosol data 

[library requirements] os, subprocess, glob, sys, numpy, netCDF4, pandas, requests, get_aeronet

[create a soft link to get_aeronet.py script from the get_aeronet repo in UARENForecasting]

$ python create_geos5_aod_aux_input.py

{creates GEOS5.FILE:* type ungrib files}



Running the python code at 2015z means it is usually finished by 2030z. After the GEOS5.FILE:* type ungrib files have been made, namelist.wps needs to be told to read them at the metgrid.exe stage. In namelist.wps add something like this;
&metgrid
 fg_name = 'FILE','GEOS5.FILE'

Then, the instructions from David Ovens are applicable from 4.1 onwards on this page https://atmos.washington.edu/~ovens/running_wrf_with_geos5_aerosols/README

Attached is a the namelist.input file being used for real.exe/wrf.exe. The key lines are:
 auxinput15_inname                   = 'wrfaerinput_d<domain>',
 auxinput15_outname                  = 'auxinput15_d<domain>_<date>',
 auxinput15_interval                 = 180,
 io_form_auxinput15                  = 2,   
 force_use_old_data                  = .true.

 &physics
 mp_physics                          = 8,    -1,    -1,
 cu_physics                          = 3,    -1,     0,
 ra_lw_physics                       = 4,    -1,    -1,
 ra_sw_physics                       = 4,    -1,    -1,
 
 aer_opt                             = 2,
 aer_aod550_opt                      = 2,
 aer_angexp_opt                      = 1,
 aer_angexp_val                      = 1.3,
