# gridded-aerosols
scripts for getting and analyzing gridded aerosol products


NRL ICAP ENSEMBLE
Some instructions for running scripts to download NRL ICAP 2D aerosol data, partition it into seperate forecast files and finally put it in a format (temporary ungrib files) ready to be used in metgrid.exe: 

- compilation of the fortran code needs to be done first

$ ifort -convert big_endian -I/usr/include write_aerosols_for_metgrid_mod.f -L/st1/luong/lib/netcdf-4.3.3.1/lib -lnetcdf -lnetcdff -o write_aerosols_for_metgrid_mod.Linux

{likely will need to change pathways to netcdf library}

- run python script to download and process NRL ICAP 2D aerosol data

$ python create_icap_aod_aux_input.py

{creates ICAP.FILE:* type ungrib files}


GEOS5
Similar instructions for running scripts to download GEOS5 2D aerosol forecast data files and put in a format (temporary ungrib files) ready to be used in metgrid.exe: 

- compilation of the a slightly different version of the same fortran code needs to be done first

$ ifort -convert big_endian -I/usr/include write_aerosols_for_metgrid.f -L/st1/luong/lib/netcdf-4.3.3.1/lib -lnetcdf -lnetcdff -o write_aerosols_for_metgrid.Linux
{likely will need to change pathways to netcdf library}

- run python script to download and process GEOS5 2D aerosol data

$ python create_geso5_aod_aux_input.py

{creates GEOS5.FILE:* type ungrib files}







NRL data from: https://usgodae.org/cgi-bin/datalist.pl?Data_Type=aerosol&Parameter=aod&Provider=ALL&meta=Go
GOES5 data from: https://gmao.gsfc.nasa.gov/GMAO_products/NRT_products.php
