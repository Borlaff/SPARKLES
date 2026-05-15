import os
import healpy as hp
import numpy as np
import datetime
import healpy as hp
from tqdm import tqdm

from astropy.time import TimezoneInfo  # Specifies a timezone

from skyfield.positionlib import ICRF, Geocentric
from skyfield.constants import (AU_M, ERAD, DEG2RAD,
                                IERS_2010_INVERSE_EARTH_FLATTENING, tau)

import skyfield.api as sf_api
import skyfield as sf
import matplotlib.pyplot as plt

from astropy.time import Time
import astropy.units as u

# import cartopy.crs as ccrs
from datetime import datetime, timedelta, timezone
import rosalia as rs
import sparkles as sp

##################################

def reverse_terra(xyz_au, gast, iterations=3):
    """Convert a geocentric (x,y,z) at time `t` to latitude and longitude.
    Returns a tuple of latitude, longitude, and elevation whose units
    are radians and meters.  Based on Dr. T.S. Kelso's quite helpful
    article "Orbital Coordinate Systems, Part III":
    https://www.celestrak.com/columns/v02n03/
    """
    x, y, z = xyz_au
    R = np.sqrt(x*x + y*y)

    lon = (np.arctan2(y, x) - 15 * DEG2RAD * gast - pi) % tau - pi
    lat = np.arctan2(z, R)

    a = ERAD / AU_M
    f = 1.0 / IERS_2010_INVERSE_EARTH_FLATTENING
    e2 = 2.0*f - f*f
    i = 0
    C = 1.0
    while i < iterations:
        i += 1
        C = 1.0 / np.sqrt(1.0 - e2 * (np.sin(lat) ** 2.0))
        lat = np.arctan2(z + a * C * e2 * np.sin(lat), R)
    elevation_m = ((R / np.cos(lat)) - a * C) * AU_M
    earth_R = (a*C)*AU_M
    return lat, lon, elevation_m, earth_R

def subpoint(self, iterations):
    """Return the latitude an longitude directly beneath this position.

    Returns a :class:`~skyfield.toposlib.Topos` whose ``longitude``
    and ``latitude`` are those of the point on the Earth's surface
    directly beneath this position (according to the center of the
    earth), and whose ``elevation`` is the height of this position
    above the Earth's center.
    """
    if self.center != 399:  # TODO: should an __init__() check this?
        raise ValueError("you can only ask for the geographic subpoint"
                            " of a position measured from Earth's center")
    t = self.t
    xyz_au = np.einsum('ij...,j...->i...', t.M, self.position.au)
    lat, lon, elevation_m, self.earth_R = reverse_terra(xyz_au, t.gast, iterations)

    from skyfield.toposlib import Topos
    return Topos(latitude=sf.units.Angle(radians=lat),
                    longitude=sf.units.Angle(radians=lon),
                    elevation_m=elevation_m)

def earth_radius(self):
    return self.earth_R

def satellite_visible_area(earth_radius, satellite_elevation):
    """Returns the visible area from a satellite in square meters.

    Formula is in the form is 2piR^2h/R+h where:
        R = earth radius
        h = satellite elevation from center of earth
    """
    return ((2 * pi * ( earth_radius ** 2 ) *
            ( earth_radius + satellite_elevation)) /
            (earth_radius + earth_radius + satellite_elevation))




def los_to_earth(position, pointing):
    """Find the intersection of a pointing vector with the Earth
    Finds the intersection of a pointing vector u and starting point s with the WGS-84 geoid
    Args:
        position (np.array): length 3 array defining the starting point location(s) in meters
        pointing (np.array): length 3 array defining the pointing vector(s) (must be a unit vector)
    Returns:
        np.array: length 3 defining the point(s) of intersection with the surface of the Earth in meters
    """

    a = 6378137.0
    b = 6378137.0
    c = 6356752.314245
    x = position[0]
    y = position[1]
    z = position[2]
    u = pointing[0]
    v = pointing[1]
    w = pointing[2]

    value = -a**2*b**2*w*z - a**2*c**2*v*y - b**2*c**2*u*x
    radical = a**2*b**2*w**2 + a**2*c**2*v**2 - a**2*v**2*z**2 + 2*a**2*v*w*y*z - a**2*w**2*y**2 + b**2*c**2*u**2 - b**2*u**2*z**2 + 2*b**2*u*w*x*z - b**2*w**2*x**2 - c**2*u**2*y**2 + 2*c**2*u*v*x*y - c**2*v**2*x**2
    magnitude = a**2*b**2*w**2 + a**2*c**2*v**2 + b**2*c**2*u**2

    if radical < 0:
        raise ValueError("The Line-of-Sight vector does not point toward the Earth")
    d = (value - a*b*c*np.sqrt(radical)) / magnitude

    if d < 0:
        raise ValueError("The Line-of-Sight vector does not point toward the Earth")

    return np.array([
        x + d * u,
        y + d * v,
        z + d * w,
    ])


def get_earthshine(mjd, nside, healpix_map_name):
    # First define a healpix map
    npix = hp.nside2npix(nside)
    longitude_map, latitude_map = hp.pix2ang(nside=nside, ipix=range(npix), nest=True, lonlat=True)

    # Get the albedo map
    albedo_map = rs.albedo.find_albedo(lat=latitude_map, lon=longitude_map,
                                       healpix_map_name=healpix_map_name)

    # Get the date object in Pysolar.
    import pysolar
    astropy_t = Time(mjd, format='mjd')
    datetime_at_t = astropy_t.to_datetime(timezone=TimezoneInfo())
    altitude_deg = pysolar.solar.get_altitude(latitude_map, longitude_map, datetime_at_t)
    solar_radiation_at_t = pysolar.radiation.get_radiation_direct(datetime_at_t, altitude_deg)

    earthshine_at_t = albedo_map*solar_radiation_at_t
    return(earthshine_at_t)


def vXYZxv3(vXYZ, v3):
  """
  Given one or more vectors in `vXYZ` and single vector `v3`, return their
  component scalar products.

  Equivalent to 'for vec in vXYZ: v = vec*v3'

  This works whether `vXYZ` has the shape ``(3,)``, or whether it is a whole
  array of corresponding x, y, and z coordinates and has shape ``(3, N)``.
  `v3` must be shape ``(3,)``.
  """
  vX = vXYZ[0]*v3[0]
  vY = vXYZ[1]*v3[1]
  vZ = vXYZ[2]*v3[2]
  v = np.array([vX, vY, vZ])
  return v

def unitize(v):
  """
  Given a vector, return its unit vector.

  This works whether `v` has the shape ``(3,)``, or whether it is a whole
  array of corresponding x, y, and z coordinates and has shape ``(3, N)``.
  """
  return v/sf.functions.length_of(v)

def vproj(a, b):
  """
  Given 2 vectors, return the projection of the first onto the second.

  This works whether `a` and `b` each have the shape ``(3,)``, or
  whether they are each whole arrays of corresponding x, y, and z
  coordinates and have shape ``(3, N)``.
  """
  bhat = unitize(b)
  proj = sf.functions.dots(a, bhat)*bhat
  return proj

def vperp(a, b):
  """
  Given 2 vectors, return the component of the first that is perpendicular
  to the second.

  This works whether `a` and `b` each have the shape ``(3,)``, or
  whether they are each whole arrays of corresponding x, y, and z
  coordinates and have shape ``(3, N)``.
  """
  proj = vproj(a, b)
  perp = a - proj
  return perp

def ray_intersect_ellipsoid(positn, u, a, b, c):
  """
  Based on SPICE surfpt
  https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/surfpt_c.html

  NOTE: Unlike surfpt, `positn` is assumed to be outside of the ellipsoid.
  For cases where `positn` is on or in the ellipsoid, results are invalid.

  Parameters:
    `positn` is the position of an observer with respect to the center of an
    ellipsoid. The vector is expressed in a body-fixed reference frame.
    The semi-axes of the ellipsoid are aligned with the x, y, and z-axes
    of the body-fixed frame.

    `u` is the pointing vector emanating from the observer. `u` does not need
    to be a unit vector.

    `a`, `b`, and `c` are the ellipsoid semi-axes along the X, Y, and Z axes,
    respectively.

  Returns:
    `point` is the point on the ellipsoid pointed to by `u`

    `found` is a boolean indicating if `u` is pointing at the ellipsoid

  This function works whether `positn` and `u` each have the shape ``(3,)``,
  or whether they are each whole arrays of corresponding x, y, and z
  coordinates and have shape ``(3, N)``. `a`, `b`, and `c` are scalars.
  """
  elshape = np.array([a,b,c])
  invelshape = 1/elshape

  '''
  General procedure:
  1. Apply a linear transformation to the observer position,
     direction vector, and ellipsoid so that the problem is reduced to
     finding the intersection of the vector and the unit sphere.
     The ellipsoid itself doesn't need to be transformed since it
     will be a unit sphere.
  2. Find the intersection of the direction vector and the unit sphere.
  3. Reverse the transformation.
  '''

  x = vXYZxv3(u, invelshape) #u/elshape
  y = vXYZxv3(positn, invelshape) #positn/elshape

  yproj = vproj(y,x)
  p = y - yproj #same as vperp(y,x)

  ymag = sf.functions.length_of(y)
  pmag = sf.functions.length_of(p)

  ux = unitize(x)

  # TODO handle ymag<=1 cases (positn is on/inside ellipsoid)
  '''
  SPICE surfpt checks for two no interesect conditions to return immediately.
  But we will continue with the calculations anyway so this function can
  handle an array of vectors.
  '''
  # no intersection if p is outside of sphere
  found = np.where(pmag>1, False, True)
  # no intersection if direction vector is pointing away from sphere
  found = np.where(sf.functions.dots(yproj, x)>0, False, found)

  # before sqrt, clip negative values of d to 0 so that the calculations
  # can be done even for invalid values
  d = 1-pmag**2
  dclip = np.array([d, d*0]).max(axis=0) # clip negative values
  scale = np.sqrt(dclip)
  point = p - scale*ux

  # reverse the transformation
  point = vXYZxv3(point, elshape) # point*elshape

  # set point to zero if no intersection to match behavior of SPICE surfpt
  mask = np.where(found, 1, 0)
  point *= mask

  return point, found


def find_earth_intersect_from_satellite(tle, epoch, ra, dec):
    """
    Find the intersect between the line of sight of a satellite and a fixed position in the sky with the surface of the Earth.

    Input: tle: TLE of the satellite (observer)
           epoch: MJD
           ra = Right ascension of the target, in degrees.
           dec = Declination of the target, in degrees.

    Output:
           A dictionary with the following attributes:
           geopos = GeographicPosition WGS84
           found = An array with True of False if the location is found
    """
    # Preparing RA and DEC if the input is not an array.
    if not isinstance(ra, np.ndarray):
        ra = np.array(ra)
        dec = np.array(dec)
    n_positions = len(ra)

    # Defining the observer
    sat = tle

    # Defining the Earth
    planets = sf_api.load("de440.bsp")

    earth = planets['EARTH']
    earth_shape = [6378.1366, 6378.1366, 6356.7519] # from pck00010.tpc

    # Loading the timescale. This is needed for time operation with skyfield
    ts = sf_api.load.timescale()

    # ---- the good stuff starts here ----
    # build a `Time` object from a datetime arange array
    t = ts.from_astropy(Time(epoch, format='mjd'))


    # `from_datetimes()` requires tzinfo to be set
    #for i in range(t_range.shape[0]):
    #    t_range[i] = t_range[i].replace(tzinfo=timezone.utc)
    #t = ts.from_datetimes(t_range)

    # need to use Earth body-fixed coordinates (ITRS) so that the axes
    # match the `earth_shape` model
    gc = sf_api.Star(ra=sf.units.Angle(degrees=ra), dec=sf.units.Angle(degrees=dec))
    earth_target = earth.at(t).observe(gc).frame_xyz(sf.framelib.itrs).km
    earth_sat = sat.at(t).frame_xyz(sf.framelib.itrs).km

    geopos_list = []
    found = np.zeros(n_positions)
    latitude = np.zeros(n_positions)
    longitude = np.zeros(n_positions)

    for i in range(n_positions):
        target_sat = earth_target[:,i] - earth_sat
        # draw a ray from `earth_sat` in the direction of `target_sat` and find
        # were it intersects the ellipsoid defined by `earth_shape`
        point, found[i] = ray_intersect_ellipsoid(earth_sat, target_sat, *earth_shape)

        # convert the intersection point back to ICRF
        point_pos = sf.units.Distance(km=point)
        point_vel = sf.units.Velocity(km_per_s=point*0) # dummy velocity to build position
        point_icrf = sf.positionlib.ICRF.from_time_and_frame_vectors(t, sf.framelib.itrs, point_pos, point_vel)
        point_icrf.center = 399

        # get the geographic coordinates of the intersection point
        geopos = sf_api.wgs84.geographic_position_of(point_icrf)
        geopos_list.append(geopos)
        latitude[i] = geopos.latitude.degrees
        longitude[i] = geopos.longitude.degrees

    return({"GEOPOS": geopos_list, "FOUND": found, "latitude": latitude, "longitude": longitude})



def find_earthshadow_from_satellite(TLE, epoch, nside=64, shadow_healpix=True, limb_angle=0):
    """
    Input: TLE
           epoch (MJD)
           nside (healpix sphere resolution)

    Output: Healpix map: 1 is earth, 0 is space

    """
    # Get the location of the observer, the earth, sun, and Moon
    orbit_snapshot = sp.satellites.get_orbit_snapshot(epoch_mjd=epoch, TLE=TLE)

    # Find the altitude of the telescope
    #t = ts.from_astropy(Time(epoch_i, format='mjd'))
    #geocentric = TLE_epoch.at(t)

    altitude_telescope = np.sqrt(orbit_snapshot["xs"]**2 +
                                 orbit_snapshot["ys"]**2 +
                                 orbit_snapshot["zs"]**2)*u.km - rs.constants.r_earth


    angular_radius_earth = np.arcsin(rs.constants.r_earth/(altitude_telescope + rs.constants.r_earth)) + np.radians(limb_angle*u.degree)

    if shadow_healpix:
        vector_pointing_to_center_earth = hp.ang2vec(orbit_snapshot["ra_earth"],
                                                     orbit_snapshot["dec_earth"],
                                                     lonlat=True)
        npix = hp.nside2npix(nside)


        earthshadow_for_all_epochs = np.zeros((npix, len(epoch)))
        for i in range(len(epoch)):
            ipix_disc = hp.query_disc(nside=nside,
                                      vec=vector_pointing_to_center_earth[i,:],
                                      radius=np.radians(angular_radius_earth[i]).value,
                                      nest=True)


            earthshadow = np.zeros(npix)

            # If it is inside the radial horizon of the visible earth, then set it to 1.
            earthshadow[ipix_disc] = 1
            earthshadow_for_all_epochs[:, i] = earthshadow

    else:
        earthshadow_for_all_epochs = False

    return({"hp_map_earthshadow": earthshadow_for_all_epochs,
            "altitude_telescope": altitude_telescope,
            "angular_radius_earth": angular_radius_earth,
            "ra_earth": orbit_snapshot["ra_earth"],
            "dec_earth": orbit_snapshot["dec_earth"],
            "ra_moon": orbit_snapshot["ra_moon"],
            "dec_moon": orbit_snapshot["dec_moon"],
            "ra_sun": orbit_snapshot["ra_sun"],
            "dec_sun": orbit_snapshot["dec_sun"]})



def get_orbital_POV(epochs, TLE, healpix_map_name, nside=64, albedo = True, albedo_value=0.3, earthshine = True):
    """
    Given an observer (a space telescope) at an epoch with a certain TLE, how the 360 FOV looks like?

    input: epoch (MJD)
           TLE (Skyfield object)

    output:
           Healpix full sky map
    ################ Based on a problem posted in Github/Skyfield for ISS astrophotography #################
    ################ https://github.com/skyfielders/python-skyfield/discussions/642        #################
    """

    if not isinstance(epochs, np.ndarray):
        epochs = np.array(epochs)

    print("Approximate resolution at NSIDE {} is {:.2} deg".format(
        nside, hp.nside2resol(nside, arcmin=True) / 60))

    npix = hp.nside2npix(nside)
    print(npix)

    orbital_POV_snapshots = []


    """
    For every epoch, we calculate:
    1 - The location of the Earth and the projected surface geolocations (lon, lat)
    2 - Estimate their albedo
    3 - Find the satellites in LEO.

    """

    for epoch_i in tqdm(epochs):
        # Get the location of the observer, the earth, sun, and Moon

        # !!! - This function is already able to compute the earthshadow for an array of epochs.
        # It might not be necesary to run this inside the for loop.
        earthshadow = find_earthshadow_from_satellite(TLE=TLE, epoch=[epoch_i], nside=nside)

        orbital_pov_db = {}
        orbital_pov_db["TLE"] = TLE
        orbital_pov_db["epoch"] = epoch_i
        orbital_pov_db["earthshadow"] = earthshadow

        if albedo:
            # For each healpix covered by Earth, plot the albedo.
            ## First, get the latitude and longitude on each healpix cell.
            ra, dec = hp.pix2ang(nside, range(npix), lonlat=True, nest=True)
            #print("RA: " + str(ra) + " DEC:" + str(dec))
            intersect = sp.earth.find_earth_intersect_from_satellite(tle=TLE, epoch=epoch_i, ra=ra, dec=dec)
            orbital_pov_db.update(intersect)
            # Then get the albedo
            albedo_map = rs.albedo.find_albedo(lon=orbital_pov_db["longitude"], lat=orbital_pov_db["latitude"],
                                               healpix_map_name=healpix_map_name)

            albedo_map[orbital_pov_db["FOUND"] == False] = np.nan
            orbital_pov_db["albedo_map"] = albedo_map

        else:
            albedo_map = np.zeros((npix)) + albedo_value
            ## First, get the latitude and longitude on each healpix cell.
            ra, dec = hp.pix2ang(nside, range(npix), lonlat=True, nest=True)
            #print("RA: " + str(ra) + " DEC:" + str(dec))
            intersect = sp.earth.find_earth_intersect_from_satellite(tle=TLE, epoch=epoch_i, ra=ra, dec=dec)
            orbital_pov_db.update(intersect)


        if earthshine:
            # Get the earthshine using Pysolar.
            import pysolar
            astropy_t = Time(epoch_i, format='mjd')
            datetime_at_t = astropy_t.to_datetime(timezone=TimezoneInfo())
            # latitude_deg, longitude_deg, when
            altitude_deg = pysolar.solar.get_altitude(latitude_deg=orbital_pov_db["latitude"], longitude_deg=orbital_pov_db["longitude"], when=datetime_at_t)
            solar_radiation_at_t = pysolar.radiation.get_radiation_direct(datetime_at_t, altitude_deg)
            earthshine_map = albedo_map*solar_radiation_at_t

            # Combine all the results into intersect before sending it to the next program
            orbital_pov_db["earthshine_map"] = earthshine_map

        orbital_POV_snapshots.append(orbital_pov_db)

    return(orbital_POV_snapshots)



def earthshine_illumination(epoch, TLE, nside=32):

    import astropy.units as u
    from astropy.time import Time
    from astropy.time import TimezoneInfo  # Specifies a timezone

    orbit_snapshot = sp.satellites.get_orbit_snapshot(epoch_mjd=epoch, TLE=TLE)

    altitude_telescope = np.sqrt(orbit_snapshot["xs"]**2 +
                                 orbit_snapshot["ys"]**2 +
                                 orbit_snapshot["zs"]**2)*u.km - rs.constants.r_earth


    angular_radius_earth = np.degrees(np.arcsin(rs.constants.r_earth/(altitude_telescope + rs.constants.r_earth)))#  + np.radians(limb_angle*u.degree)
    angular_cone_earthcentric = 90 - angular_radius_earth.to("degree").value

    vector_pointing_to_center_earth = hp.ang2vec(theta=orbit_snapshot["longitude"],
                                                 phi=orbit_snapshot["latitude"],
                                                 lonlat=1)
    npix = hp.nside2npix(nside)

    earth_healpix_in_horizon = hp.query_disc(nside=nside,
                                             vec=vector_pointing_to_center_earth,
                                             radius=np.radians(angular_cone_earthcentric).value,
                                             nest=False)

    in_horizon = np.zeros(npix)
    # If it is inside the radial horizon of the visible earth, then set it to 1.
    in_horizon[earth_healpix_in_horizon] = 1


    import pysolar
    astropy_t = Time(epoch, format='mjd')
    datetime_at_t = astropy_t.to_datetime(timezone=TimezoneInfo())
    # print(datetime_at_t)
    lon_pixelized_earth, lat_pixelized_earth = hp.pix2ang(nside=nside, ipix=np.linspace(0, npix, npix, dtype="int"), lonlat=True, nest=False)
    altitude_deg = pysolar.solar.get_altitude(latitude_deg=lat_pixelized_earth, longitude_deg=lon_pixelized_earth, when=datetime_at_t)
    solar_radiation_at_t = pysolar.radiation.get_radiation_direct(datetime_at_t, altitude_deg)

    # How many pixels inside the horizon are receiving more than 1% of the max radiation?
    import bottleneck as bn
    max_solar_radiation = bn.nanmax(solar_radiation_at_t)
    bool_pixels_with_critical_solar_radiation = (solar_radiation_at_t[earth_healpix_in_horizon] > 0.5*max_solar_radiation)
    number_of_pixels_inside_horizon = len(earth_healpix_in_horizon)

    number_of_pixels_inside_horizon_and_in_daylight = bn.nansum(bool_pixels_with_critical_solar_radiation)

    fraction_of_illumination = number_of_pixels_inside_horizon_and_in_daylight/number_of_pixels_inside_horizon

    # Magnitude of sun-illuminated earth
    magarcsec2_sun_illum_earth = 1.960 # mag/arcsec2
    flux_sun_illum_earth = 10**(-0.4*(magarcsec2_sun_illum_earth - 8.9))

    area_per_pixel = hp.nside2pixarea(nside=nside, degrees=True)
    total_flux_earthshine =  flux_sun_illum_earth*area_per_pixel*(60**4)*number_of_pixels_inside_horizon_and_in_daylight
    equivalent_magnitude_earthshine = -2.5*np.log10(total_flux_earthshine) + 8.9
    return(equivalent_magnitude_earthshine)


################


def moon_phase(epoch):
    import ephem
    from datetime import date, datetime, timezone
    from astropy.time import Time
    from astropy.time import TimezoneInfo  # Specifies a timezone
    astropy_t = Time(epoch, format='mjd')
    datetime_at_t = astropy_t.to_datetime(timezone=TimezoneInfo())
    ephem_date = ephem.Date(datetime_at_t)
    astropy_t = Time(epoch, format='mjd')
    return(ephem.Moon(ephem_date).phase)
