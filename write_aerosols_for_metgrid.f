      program write_aerosols_for_metgrid
c     compile with:
c     compiled static version on frosty with:
c     ifort -convert big_endian -I$ms/GRIB/include write_aerosols_for_metgrid.f -L$ms/GRIB/lib -lnetcdff -lnetcdf -lhdf5_hl -lhdf5 -lz -static -o write_aerosols_for_metgrid.Linux 
c     using ifort:/opt/intel/composer_xe_2013_sp1.4.211/bin/intel64/ifort
c
c     also was able to successfully compile a static version on sage-new using:
c      source /opt/intel/composer_xe_2015.0.090/bin/compilervars.csh intel64
c      ifort -convert big_endian -I$ms/GRIB/include write_aerosols_for_metgrid.f -L$ms/GRIB/lib -lnetcdff -lnetcdf -lhdf5_hl -lhdf5 -lz -static -o write_aerosols_for_metgrid.Linux
c
c     old compilation:
c     ifort -convert big_endian -I/usr/include write_aerosols_for_metgrid.f -lnetcdf -lnetcdff -o write_aerosols_for_metgrid.Linux
      INCLUDE 'netcdf.inc'
      integer, parameter :: ydim = 721
      integer, parameter :: xdim = 1152
      integer, parameter :: missvar = -1
      integer :: year,month,day,hour,begin_date,begin_time,timeid
      real, parameter :: rmissvar = -1.E30
      real, parameter :: rdiff = 0.001

      INTEGER  STATUS, NCID, TIMES
      PARAMETER (TIMES=1, NLAT=ydim, NLON=xdim) ! dimension lengths
      INTEGER  aodid, angid, latsid, lonsid             ! variable ID
      INTEGER LATID, RECID, ivarid
      INTEGER  LATDIM, LONDIM, TIMDIM ! dimension IDs
      INTEGER  AODDIMS(3),start(3),count(3)        ! variable shape
      real*8 latd(ydim), lond(xdim)
      real aod(nlon,nlat),ang(nlon,nlat)
     $     ,lats(nlon,nlat),lons(nlon,nlat)
      real llxmap, llymap, latloninc

      integer*2 iarr1(xdim,ydim),iarr2(xdim,ydim)
      character*256  arg,filename,outfilename

      integer, parameter :: version=5        ! Format version (must =5 for WPS format)
      integer :: nx, ny         ! x- and y-dimensions of 2-d array
      integer :: iproj          ! Code for projection of data in array:
c                               !       0 = cylindrical equidistant
c                               !       1 = Mercator
c                               !       3 = Lambert conformal conic
c                               !       4 = Gaussian (global only!)
c                               !       5 = Polar stereographic

      real :: nlats             ! Number of latitudes north of equator
c                               !       (for Gaussian grids)

      real :: xfcst             ! Forecast hour of data
      real :: xlvl              ! Vertical level of data in 2-d array
      real :: startlat, startlon ! Lat/lon of point in array indicated by
c                               !       startloc string
      real :: deltalat, deltalon ! Grid spacing, degrees
      real :: dx, dy            ! Grid spacing, km
      real :: xlonc             ! Standard longitude of projection
      real :: truelat1, truelat2 ! True latitudes of projection
      real :: earth_radius      ! Earth radius, km

      logical :: is_wind_grid_rel ! Flag indicating whether winds are  
c                              !       relative to source grid (TRUE) or
c                              !       relative to earth (FALSE)
      character (len=8)  :: startloc ! Which point in array is given by
c                              !       startlat/startlon; set either 
c                              !       to 'SWCORNER' or 'CENTER  '
      character (len=9)  :: field ! Name of the field
      character (len=24) :: hdate ! Valid date for data YYYY:MM:DD_HH:00:00
      character (len=25) :: units ! Units of data
      character (len=32) :: map_source !  Source model / originating center
      character (len=46) :: desc ! Short description of data

      call getarg(1,arg)
      if (arg(1:2).eq.'-h' .or. iargc().lt.1) then
         print *,'version 1.0'
         print *,'usage:  program aodfile'
         print *,' example: '
         print *,
     $        '  test2 f516_fp.inst1_2d_hwl_Nx.20170806_2300z.nc4'
         print *,' or '
         print *,' test2 '//
     $'GEOS.fp.fcst.inst1_2d_hwl_Nx.20180604_00+20180613_0600.V01.nc4'
         call exit(1)
      else
         filename = trim(arg)
      endif

      llxmap = -180.
      llymap = -90.
      deltax = 0.3125  ! 360 / 0.3125 =  1152, lon = -180 to 179.6875
      deltay = 0.25    ! 180 / 0.25 + 1 = 721, lat = -90 to 90.

      ncid = 1
      STATUS = NF_OPEN(filename, NF_CLOBBER, NCID)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)

      STATUS = NF_INQ_DIMID(NCID, 'lat', LATDIM)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
      STATUS = NF_INQ_DIMID(NCID, 'lon', LONDIM)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
      STATUS = NF_INQ_DIMID(NCID, 'time', TIMDIM)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
      
      AODDIMS(1) = LONDIM
      AODDIMS(2) = LATDIM
      AODDIMS(3) = TIMDIM

      STATUS = NF_INQ_VARID (NCID, 'TOTEXTTAU', AODID)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
      STATUS = NF_INQ_VARID (NCID, 'TOTANGSTR', ANGID)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
      STATUS = NF_INQ_VARID (NCID, 'lat', LATSID)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
      STATUS = NF_INQ_VARID (NCID, 'lon', LONSID)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
      STATUS = NF_INQ_VARID (NCID, 'time', timeid)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
c     begin_date is in the form: YYYYMMDD
      STATUS = NF_GET_ATT_INT (NCID, timeid, 'begin_date', begin_date)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
c     begin_time is in the form: HHNNSS, 
      STATUS = NF_GET_ATT_INT (NCID, timeid, 'begin_time', begin_time)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)

      aod  = rmissvar
      ang  = rmissvar
      start = 1
      count(2) = 1
      count(3) = 1

      count(1) = nlat
      STATUS = NF_GET_VARA_DOUBLE(NCID, LATSID, start, count, latd)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
      count(1) = nlon
      STATUS = NF_GET_VARA_DOUBLE(NCID, LONSID, start, count, lond)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
      count(1) = nlon
      count(2) = nlat
      STATUS = NF_GET_VARA_REAL(NCID, AODID, start, count, aod)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)
      STATUS = NF_GET_VARA_REAL(NCID, ANGID, start, count, ang)
      IF (STATUS .NE. NF_NOERR) CALL HANDLE_ERR(STATUS)

      DO 20 ILAT = 1, NLAT
         DO 30 ILON = 1, NLON
c            DO 10 ITIME = 1, TIMES
            lats(ILON, ILAT) = llymap + deltay*(ilat-1)
            lons(ILON, ILAT) = llxmap + deltax*(ilon-1)
            if (abs(lats(ilon,ilat)-latd(ilat)).gt.rdiff) then
               print *,'error lats mismatch: '
     $              ,lats(ilon,ilat),latd(ilat)
     $              ,ilon,ilat
            endif
            if (abs(lons(ilon,ilat)-lond(ilon)).gt.rdiff) then
               print *,'error lons mismatch: '
     $              ,lons(ilon,ilat),lond(ilon)
     $              ,ilon,ilat
            endif
 10         CONTINUE
 30      continue
 20   continue
      print *,' got lats(1,1) lons(1,1) = ',lats(1,1),lons(1,1)
      print *,' got lats(nlon,nlat) lons(nlon,nlat) = '
     $     ,lats(nlon,nlat),lons(nlon,nlat)

      print *,'max aod = ',maxval(aod)
      print *,'min aod = ',minval(aod)
      print *,'max ang = ',maxval(ang)
      print *,'min ang = ',minval(ang)

      
      status = nf_close(ncid)

c see metgrid/src/read_met_module.F90

c     When writing data to the WPS intermediate format, 2-dimensional
c     fields are written as a rectangular array of real
c     values. 3-dimensional arrays must be split across the vertical
c     dimension into 2-dimensional arrays, which are written
c     independently. It should also be noted that, for global data sets,
c     either a Gaussian or cylindrical equidistant projection must be
c     used, and for regional data sets, either a Mercator, Lambert
c     conformal, polar stereographic, or cylindrical equidistant may be
c     used. The sequence of writes used to write a single 2-dimensional
c     array in the WPS intermediate format is as follows (note that not
c     all of the variables declared below are used for a given
c     projection of the data).

      nx = xdim
      ny = ydim
      iproj = 0
      deltalat = deltay
      deltalon = deltax
      earth_radius = 6371.
c                          10        20        30        40
c                  1234567890123456789012345678901234567890
c      filename = 'f516_fp.inst1_2d_hwl_Nx.20170806_2300z.nc4'
c     ! Valid date for data YYYY:MM:DD_HH:00:00
c     begin_date is in the form: YYYYMMDD
c     begin_time is in the form: HHNNSS, 
      year = begin_date / 10000
      month = (begin_date - year*10000) / 100
      day = (begin_date - year*10000 - month*100)
c      read(filename(29:30),'(i2.2)') month
c      read(filename(31:32),'(i2.2)') day
c     read(filename(34:35),'(i2.2)') hour
      hour = begin_time / 10000

      write(hdate,'(i4.4,"-",i2.2,"-",i2.2,"_",i2.2,":00:00")')
     $     year,month,day,hour
      print *,' created hdate = ',hdate,' year = ',year,' mon = ',mon
     $     ,' day = ',day,' hour = ',hour

c     1) WRITE FORMAT VERSION
      ounit = 11
      outfilename = 'GEOS5.FILE:'//hdate(1:13)
      open(ounit,file=outfilename,form='unformatted')

c     2) WRITE METADATA
c     Cylindrical equidistant

c     need:
c     xfcst

      startlat = lats(1,1)
      startlon = lons(1,1)
      startloc = 'SWCORNER'
      xlvl = 200100.

c     start of repeating section for other fields or levels
      write(unit=ounit) version
      desc = 'Aerosol optical depth'
      units = ''
      field = 'AOD5502D'
      map_source = 'GEOS5'
      xfcst = 0.
      
c     ! Cylindrical equidistant
      if (iproj .eq. 0) then
         write(unit=ounit) hdate, xfcst, map_source, field,
     $        units, desc, xlvl, nx, ny, iproj

         write(unit=ounit) startloc, startlat, startlon,
     $        deltalat, deltalon, earth_radius

c     ! Mercator
      else if (iproj .eq. 1) then

         write(unit=ounit) hdate, xfcst, map_source, field,
     $        units, desc, xlvl, nx, ny, iproj

         write(unit=ounit) startloc, startlat, startlon, dx, dy,
     $        truelat1, earth_radius

c     ! Lambert conformal
      else if (iproj .eq. 3) then
         write(unit=ounit) hdate, xfcst, map_source, field,
     $        units, desc, xlvl, nx, ny, iproj
         write(unit=ounit) startloc, startlat, startlon, dx, dy,
     $        xlonc, truelat1, truelat2, earth_radius

c     ! Gaussian
      else if (iproj .eq. 4) then
         write(unit=ounit) hdate, xfcst, map_source, field,
     $        units, desc, xlvl, nx, ny, iproj

         write(unit=ounit) startloc, startlat, startlon,
     $        nlats, deltalon, earth_radius

c ! Polar stereographic
      else if (iproj .eq. 5) then
         write(unit=ounit) hdate, xfcst, map_source, field,
     $        units, desc, xlvl, nx, ny, iproj

         write(unit=ounit) startloc, startlat, startlon, dx, dy,
     $        xlonc, truelat1, earth_radius

      end if

 

c     !  3) WRITE WIND ROTATION FLAG
      is_wind_grid_rel = .false.
      write(unit=ounit) is_wind_grid_rel

c     !  4) WRITE 2-D ARRAY OF DATA

      write(unit=ounit) aod
c     end of repeating section for other fields or levels

c     start of repeating section for other fields or levels
      write(unit=ounit) version
      desc = 'Aerosol Angstrom Exponent'
      units = ''
      field = 'ANGEXP2D'
      map_source = 'GEOS5'
      xfcst = 0.
      
c     ! Cylindrical equidistant
      if (iproj .eq. 0) then
         write(unit=ounit) hdate, xfcst, map_source, field,
     $        units, desc, xlvl, nx, ny, iproj

         write(unit=ounit) startloc, startlat, startlon,
     $        deltalat, deltalon, earth_radius

c     ! Mercator
      else if (iproj .eq. 1) then

         write(unit=ounit) hdate, xfcst, map_source, field,
     $        units, desc, xlvl, nx, ny, iproj

         write(unit=ounit) startloc, startlat, startlon, dx, dy,
     $        truelat1, earth_radius

c     ! Lambert conformal
      else if (iproj .eq. 3) then
         write(unit=ounit) hdate, xfcst, map_source, field,
     $        units, desc, xlvl, nx, ny, iproj
         write(unit=ounit) startloc, startlat, startlon, dx, dy,
     $        xlonc, truelat1, truelat2, earth_radius

c     ! Gaussian
      else if (iproj .eq. 4) then
         write(unit=ounit) hdate, xfcst, map_source, field,
     $        units, desc, xlvl, nx, ny, iproj

         write(unit=ounit) startloc, startlat, startlon,
     $        nlats, deltalon, earth_radius

c ! Polar stereographic
      else if (iproj .eq. 5) then
         write(unit=ounit) hdate, xfcst, map_source, field,
     $        units, desc, xlvl, nx, ny, iproj

         write(unit=ounit) startloc, startlat, startlon, dx, dy,
     $        xlonc, truelat1, earth_radius

      end if

 

c     !  3) WRITE WIND ROTATION FLAG
      is_wind_grid_rel = .false.
      write(unit=ounit) is_wind_grid_rel

c     !  4) WRITE 2-D ARRAY OF DATA

      write(unit=ounit) ang
c     end of repeating section for other fields or levels

      close(ounit)



      stop
      end

      subroutine handle_err(iret)
      integer iret
      include 'netcdf.inc'
      if (iret .ne. NF_NOERR) then
      print *, nf_strerror(iret)
      stop
      endif
      end

      
      
