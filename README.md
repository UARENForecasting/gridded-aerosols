# gridded-aerosols
scripts for getting and analyzing gridded aerosol products

Instructions for running scripts to download NRL ICAP 2D aerosol data, partition it into seperate forecast files and finally have it ready to be used in metgrid.exe: 

- compilation of the fortran code need to be done first
$ ifort -convert big_endian -I/usr/include write_aerosols_for_metgrid_mod.f -L/st1/luong/lib/netcdf-4.3.3.1/lib -lnetcdf -lnetcdff -o write_aerosols_for_metgrid_mod.Linux
{likely will need to change pathways to netcdf library}

- run python script to download and process NRL ICAP 2D aerosol data
$ python create_aod_aux_input.py
{creates ICAP.FILE:* type files}

