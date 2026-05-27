import skyfield as sf
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import numpy as np
import bottleneck as bn
import rosalia as rs
from astropy.time import Time
import astropy.units as u
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import healpy as hp
from skyfield import api as sf_api
from astropy.coordinates import SkyCoord  # High-level coordinates
from tqdm import tqdm
import astropy.wcs as wcs
from astropy.io import fits
import numexpr
import sparkles as sp

max_n_sats = 1823200+19884

planets = sf_api.load("de440.bsp")
ts = sf.api.load.timescale()
#megaconstellations_names = ["STARLINK", "ONEWEB", "KUIPER", "STARSHIELD", "XINGWANG", "QIANFAN", "GUANGWANG", "YINHE",
#                        "HANWHA", "LYNK", "ASTRA", "TELESAT", "HVNET", "SPINLAUNCH", "GLOBALSTAR3", "HONGHU-3", "SEMAPHORE",
#                        "E-SPACE"]

#large_constellations_names = ["BLUEWALKER", "HONGYUN", "HONGYAN", "KLEO", "NINGXIA", "SFERACON", "RASSVET"]
constellations_dir = os.path.dirname(sp.__file__) + "/CORE/CONSTELLATIONS/"
# active_tle_filename = constellations_dir + "ACTIVE_SPACE_TRACK_9_Mar_26.tle"

###########################################

def generate_valid_satellite_database():
    import pandas as pd
    import os
    # Eventually, we will need to add the rest of the satellites.
    # And a new class with some fake starlinks.
    print("Loading active satellite TLEs...")
    print(active_tle_filename)
    satellites = load_tle_list(active_tle_filename)

    from tqdm import tqdm
    import numpy as np
    constellation_names = sp.satellites.large_constellations_names + sp.satellites.megaconstellations_names

    stable = np.zeros(len(satellites))
    debris = np.zeros(len(satellites))
    part_of_constellation = np.zeros(len(satellites))
    for i in tqdm(range(len(satellites))):
        satellite = satellites[i]
        stable[i] = is_the_satellite_stable(satellite)
        debris[i] = is_the_satellite_debris(satellite)
        part_of_constellation[i] = is_the_satellite_part_of_constellation(satellite=satellite,
                                                                          constellation_names=constellation_names)
    cubesats = is_a_known_cubesat(satellites)

    not_debris = ~debris.astype("bool")
    stable = stable.astype("bool")
    not_part_of_constellation = ~part_of_constellation.astype("bool")
    not_a_cubesat = ~cubesats.astype("bool")
    valid_satellites_filter = not_debris & stable & not_part_of_constellation & not_a_cubesat
    import pandas as pd

    names_sats = []
    for satellite in satellites:
        names_sats.append(satellite.name)
    filter_satellites = pd.DataFrame({"satellites": names_sats,
                                      "valid": valid_satellites_filter,
                                      "stable": stable,
                                      "not_debris": not_debris,
                                      "not_part_of_constellation": not_part_of_constellation,
                                      "not_a_cubesat": not_a_cubesat})
    filter_satellites.to_csv(constellations_dir + "valid_satellites.csv")

###########################################

def is_the_satellite_part_of_constellation(satellite, constellation_names):
    import bottleneck as bn
    from skyfield.api import EarthSatellite

    found = 0
    for constellation_name in constellation_names:
        if constellation_name in satellite.name:
            found = 1

    if found == 0:
        return(False)
    else:
        return(True)

###########################################

#def is_the_satellite_debris(satellite):
#    if ("DEB" in satellite.name) or ("WESTFORD" in satellite.name):
#        return(True)
#    else:
#        return(False)

###########################################



def is_the_satellite_stable(satellite, min_mjd=None, max_mjd=None, min_altitude=150, steps=100, plot=False):
    import bottleneck as bn
    from astropy.time import Time
    t = satellite.epoch
    mjd = t.to_astropy().mjd

    if min_mjd is None:
        min_mjd = mjd
        
    if max_mjd is None:
        max_mjd = mjd + 365
    epoch = np.linspace(min_mjd, max_mjd, steps)
    #print(epoch)
    # Set the timescale from skyfield (this line is needed for Skyfield)
    
    t = ts.from_astropy(Time(epoch, format='mjd'))

    #print(t)
    geocentric = satellite.at(t)
    altitude_array = np.sqrt(geocentric.position.km[0]**2 + geocentric.position.km[1]**2 + geocentric.position.km[2]**2) - rs.constants.r_earth.to("km").value
    #plt.plot(epoch, altitude_array)
    #plt.yscale("log")

    min_altitude_sat = np.min(altitude_array)

    if min_altitude_sat < min_altitude or np.isnan(min_altitude_sat):
        if plot:
            plt.plot(epoch, altitude_array)
            plt.yscale("log")
            plt.show()
        print(np.nanmin(altitude_array))
        
        return(False)
        
    else:
        return(True)

###########################################
""""
def is_a_known_cubesat(satellites):
    cubesats = load_cubesats()
    names_cubesats = []
    for cubesat in cubesats:
        names_cubesats.append(cubesat.name)

    found_array = np.zeros(len(satellites))
    for i in range(len(satellites)):
        satellite = satellites[i]
        found = 0
        for name_cubesat in names_cubesats:
            if name_cubesat in satellite.name:
                found = 1

        found_array[i] = found

    return(found_array)
"""
###########################################

def load_tle_list(tle_list_filename, verbose=False):
    # Eventually, we will need to add the rest of the satellites.
    # And a new class with some fake starlinks.
    if verbose: print("Loading active satellite TLEs...")
    # ts = sf.api.load.timescale()
    active_tle_filename = tle_list_filename
    with sf.api.load.open(active_tle_filename) as f:
        satellites = list(sf.iokit.parse_tle_file(f, ts))
    if verbose: print('Loaded ', len(satellites), ' satellites')
    return(np.array(satellites))

###########################################

def DEPRECATED_load_active_satellites(verbose=False, remove_unstable=True, remove_debris=True, remove_constellation=True, remove_cubesats=True):
    import pandas as pd
    import os
    constellations_dir = os.path.dirname(sp.__file__) + "/CORE/CONSTELLATIONS/"
    # Eventually, we will need to add the rest of the satellites.
    # And a new class with some fake starlinks.
    if verbose: print("Loading active satellite TLEs...")
    print(active_tle_filename)
    satellites = load_tle_list(active_tle_filename)

    filter_satellite = pd.read_csv(constellations_dir + "valid_satellites.csv")

    if remove_unstable:
        satellites = satellites[filter_satellite["stable"] == True]
        filter_satellite = filter_satellite[filter_satellite["stable"] == True]
    if remove_debris:
        satellites = satellites[filter_satellite["not_debris"] == True]
        filter_satellite = filter_satellite[filter_satellite["not_debris"] == True]
    if remove_constellation:
        satellites = satellites[filter_satellite["not_part_of_constellation"] == True]
        filter_satellite = filter_satellite[filter_satellite["not_part_of_constellation"] == True]
    if remove_cubesats:
        satellites = satellites[filter_satellite["not_a_cubesat"] == True]
        filter_satellite = filter_satellite[filter_satellite["not_a_cubesat"] == True]

    return(np.array(satellites))

###########################################

#def load_cubesats(verbose=False):
#    import os
#    constellations_dir = os.path.dirname(sp.__file__) + "/CORE/CONSTELLATIONS/"
#    # Eventually, we will need to add the rest of the satellites.
#    # And a new class with some fake starlinks.
#    if verbose: print("Loading active satellite TLEs...")
#    cubesat_tle_filename = constellations_dir + "ACTIVE_CUBESATS.tle"
#    satellites = load_tle_list(cubesat_tle_filename)
#    return(np.array(satellites))

###########################################
def load_constellation(nsats, verbose=False):
    # Eventually, we will need to add the rest of the satellites.
    # And a new class with some fake starlinks.
    import glob
    import os
    import skyfield as sf

    constellations_dir = os.path.dirname(sp.__file__) + "/CORE/CONSTELLATIONS/"

    if verbose: print("Loading active satellite TLEs...")
    # ts = sf.api.load.timescale()

    all_tle_filename = constellations_dir + "SPACETRACK_FULL_TLE_9March2026.tle"
    print("Loading active satellite TLEs...")
    print(all_tle_filename)
    launched_satellites = sp.satellites.load_tle_list(all_tle_filename) # https://www.space-track.org/#queryBuilder
    valid_satellite_db = pd.read_csv(all_tle_filename.replace(".tle","_filter.csv"))
    launched_satellites = launched_satellites[np.array(valid_satellite_db["valid"], dtype="bool")]

    
    if verbose: print("Baseline (2025 - without megaconstellations) satellite pool: N = " + str(len(launched_satellites)))

    if nsats <= len(launched_satellites):
        return(launched_satellites[0:nsats])

    if nsats > len(launched_satellites):
        satellite_pool = launched_satellites


    ############ Now use the simulated satellites ###############
    megaconstellation_sats_random = []
    if nsats != 0:
        megaconstellation_satellites_pool = []

        import random
        from tqdm import tqdm
        for active_tle_filename in tqdm(glob.glob(constellations_dir + "SIMUL_*.tle")):
            if verbose: print(active_tle_filename)
            with sf.api.load.open(active_tle_filename) as f:
                megaconstellation_sats = list(sf.iokit.parse_tle_file(f, ts))
                if verbose: print(len(list(megaconstellation_sats)))
                megaconstellation_satellites_pool = megaconstellation_satellites_pool + list(megaconstellation_sats)

        if verbose: print("Megaconstellation satellite pool: N = " + str(len(megaconstellation_satellites_pool)))

        megaconstellation_sats_random = np.random.choice(np.array(megaconstellation_satellites_pool), nsats-len(satellite_pool), replace=False)

    all_constellation = np.array(list(satellite_pool) + list(megaconstellation_sats_random))


    # Now scan the all_constellation list 
    """
    blacklist_db = pd.read_csv(constellations_dir + "blacklist.csv")
    blacklisted = []
    for i in tqdm(range(len(all_constellation))):    
        satellite_i = all_constellation[i]
        satellite_i_target_name = satellite_i.target_name 
        where_is_blacklisted = np.where(blacklist_db["target_name"] == satellite_i_target_name)
        if len(where_is_blacklisted[0]) > 0:
            blacklisted.append(True)
            print("Blacklisted sat removed: " + satellite_i_target_name)
        else:
            blacklisted.append(False)
    clean_constellation = all_constellation[~np.array(blacklisted)]
    """
    if verbose: print('Loaded ', len(all_constellation), ' satellites')
    return(np.array(all_constellation))

###########################################
"""
def DEPRECATED_load_constellation(nsats, active_baseline=True, verbose=False, replace=False):
    # Eventually, we will need to add the rest of the satellites.
    # And a new class with some fake starlinks.
    import glob
    import os

    constellations_dir = os.path.dirname(sp.__file__) + "/CORE/CONSTELLATIONS/"

    if verbose: print("Loading active satellite TLEs...")
    ts = sf.api.load.timescale()

    active_satellites_db = load_active_satellites(verbose=verbose)
    if verbose: print("Baseline (2025 - without megaconstellations) satellite pool: N = " + str(len(active_satellites_db)))


    if active_baseline:
        if nsats == len(active_satellites_db):
            satellites = active_satellites_db
            return(satellites)

        if nsats < len(active_satellites_db):
            satellites = np.random.choice(np.array(active_satellites_db), nsats, replace=replace)
            return(satellites)

        if nsats > len(active_satellites_db):
            satellites = active_satellites_db

    else:
        satellites = []

    ############ Now use the simulated satellites ###############
    megaconstellation_sats_random = []
    if nsats != 0:
        megaconstellation_satellites_pool = []

        import random
        from tqdm import tqdm
        for active_tle_filename in tqdm(glob.glob(constellations_dir + "SIMUL_*.tle")):
            if verbose: print(active_tle_filename)
            with sf.api.load.open(active_tle_filename) as f:
                megaconstellation_sats = list(sf.iokit.parse_tle_file(f, ts))
                if verbose: print(len(list(megaconstellation_sats)))
                megaconstellation_satellites_pool = megaconstellation_satellites_pool + list(megaconstellation_sats)

        if verbose: print("Megaconstellation satellite pool: N = " + str(len(megaconstellation_satellites_pool)))


        if nsats == 557794:
            megaconstellation_sats_random = np.array(megaconstellation_satellites_pool)

        else:
            megaconstellation_sats_random = np.random.choice(np.array(megaconstellation_satellites_pool), nsats-len(satellites), replace=replace)


    sats_random = np.array(list(satellites) + list(megaconstellation_sats_random))

    if verbose: print('Loaded ', len(satellites), ' satellites')
    return(np.array(sats_random))
"""
###########################################

def load_starlinks(verbose=False):
    # Eventually, we will need to add the rest of the satellites.
    # And a new class with some fake starlinks.
    if verbose: print("Loading Starlink TLEs...")
    # ts = sf_api.load.timescale()
    tle_filename = rs.utils.download_file('https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle')
    with sf_api.load.open(tle_filename) as f:
        satellites = list(sf.iokit.parse_tle_file(f, ts))
    if verbose: print('Loaded ', len(satellites), ' starlinks')
    return(np.array(satellites))

########################

def find_radec_targets_from_TLE(observer_TLE, targets_TLE, epoch):


    # Identify the number of targets
    number_of_targets = len(targets_TLE)

    # If only one epoch is provided (likely a float) turn it into an array.
    if not isinstance(epoch, (list, pd.core.series.Series, np.ndarray)):
        epoch = np.array(epoch)

    n_epochs = len(epoch)

    # Set the timescale from skyfield (this line is needed for Skyfield)
    #######################################
    # Load the ephemeris database from SkyField
    # This takes a few seconds, but it only loads once.
    #######################################
    # ts = sf.api.load.timescale()
    t = ts.from_astropy(Time(epoch, format='mjd'))
    distance_from_observer_to_satelite = np.zeros((number_of_targets, n_epochs), dtype="float32")
    observer_at_t = observer_TLE.at(t)

    ra_targets    = np.zeros((number_of_targets, n_epochs), dtype="float32")
    dec_targets   = np.zeros((number_of_targets, n_epochs), dtype="float32")
    # delta_angular = np.zeros((number_of_targets, n_epochs))
    is_sunlit     = np.zeros((number_of_targets, n_epochs), dtype="bool")
    is_moonlit    = np.zeros((number_of_targets, n_epochs), dtype="bool")

    target_name = []

    #print("Assembling timelines for constellations...")
    #epoch_with_delta_t = np.zeros((number_of_targets, len(epoch)))
    #for j in tqdm(range(len(epoch))):
    #    if delta_t is not None:
    #        epoch_with_delta_t[:,j] = epoch[j] + delta_t # It is faster to iterate on the shorter axis
    #    else:
    #        epoch_with_delta_t[:,j] = epoch[j]
    #t_with_delta_t = ts.tt_jd(epoch_with_delta_t + 2400000.5, fraction=None) #
    #print("Done.")

    #for i in tqdm(range(number_of_targets)):
    #    target_i = targets_TLE[i]
    #    if delta_t is not None:
    #        target_at_t_list.append(target_i.at(ts.from_astropy(Time(epoch + delta_t[i], format='mjd')))) # target_i.at(t_with_delta_t[i])
    #        #t_with_delta_t.append(ts.from_astropy(Time(epoch + delta_t[i], format='mjd'))) #t
    #    else:
    #        target_at_t_list.append(target_i.at(ts.from_astropy(Time(epoch, format='mjd'))))
    #    target_name.append(target_i.name)


    # https://github.com/skyfielders/python-skyfield/pull/281
    for i in tqdm(range(number_of_targets), position=0, leave=True):

        target_i = targets_TLE[i]
        target_name.append(target_i.name)
        #if delta_t is None:
        target_at_t = target_i.at(t) #target_i.at(t_with_delta_t[i,:])
        #else:
        #    target_at_t = target_i.at(t + delta_t[i])

        is_sunlit[i, :]  = target_at_t.is_sunlit(planets)
        is_moonlit[i, :] = target_at_t.is_moonlit(planets)

        #difference_vector     = target_i - observer_TLE
        difference_vector_at_t = target_at_t - observer_at_t #difference_vector.at(t)

        vector_from_observer_to_satellite = difference_vector_at_t.position.m
        coords_satellite_i_from_LEO_observer = difference_vector_at_t.radec()

        ra_targets[i, :]  = coords_satellite_i_from_LEO_observer[0]._degrees
        dec_targets[i, :] = coords_satellite_i_from_LEO_observer[1].degrees
        # delta_angular[i, :] = rs.utils.delta_angular_separation(ra_targets[i, :] , dec_targets[i, :]) This is too slow!

        x = vector_from_observer_to_satellite[0]
        y = vector_from_observer_to_satellite[1]
        z = vector_from_observer_to_satellite[2]
        distance_from_observer_to_satelite_i = np.sqrt(x**2 + y**2 + z**2) #numexpr.evaluate("sqrt(x**2 + y**2 + z**2)") # #
        distance_from_observer_to_satelite[i, :] = distance_from_observer_to_satelite_i


    #return({"ra": ra_targets, "dec":dec_targets, "delta_angular":delta_angular, "sat_name": np.array(target_name),
    #        "distance_to_sat":distance_from_observer_to_satelite, "is_sunlit": is_sunlit.astype("bool")})
    return({"ra": ra_targets, "dec":dec_targets, 
            # "delta_angular":delta_angular, 
            "sat_name": np.array(target_name),
            "distance_to_sat":distance_from_observer_to_satelite,
            "is_sunlit": is_sunlit.astype("bool"),
            "is_moonlit": is_moonlit.astype("bool")})

##############

def visibility_satellites_POV(observer_TLE, targets_TLE, epoch, nside=512, verbose=True, delta_t=None):

    if isinstance(epoch, (str)):
        if epoch == "live":
            # ts = sf.api.load.timescale()
            t = ts.now()
            epoch = t.to_astropy().mjd

    # Lets find the earth from orbit.
    n_satellites = len(targets_TLE)

    # Find the location of the earth, moon, and sun, and latitude, longitude over earth.
    if verbose: print("Finding the trail of Earth...")
    orbit_snapshot = get_orbit_snapshot(epoch, observer_TLE)

    # Find the areas of the sky covered by the Earth
    if verbose: print("Finding the shadow of the Earth...")
    earthshadow_db = sp.earth.find_earthshadow_from_satellite(TLE=observer_TLE, epoch=epoch, nside=nside, shadow_healpix=False)
    altitude_telescope = earthshadow_db["altitude_telescope"]
    angular_radius_earth = earthshadow_db["angular_radius_earth"]
    ra_earth = earthshadow_db["ra_earth"]
    dec_earth = earthshadow_db["dec_earth"]

    earth_coords = SkyCoord(ra_earth, dec_earth, frame="icrs", unit="deg")

    if verbose: print("Determining RA DEC of the sats...")
    radec_targets = find_radec_targets_from_TLE(observer_TLE=observer_TLE, targets_TLE=targets_TLE, epoch=epoch)
    bool_are_shadowed = ~radec_targets["is_sunlit"]

    # Find the satellites that are shadowed by Earth
    sat_coords = SkyCoord(radec_targets["ra"], radec_targets["dec"], frame="icrs", unit="deg")
    sat_distance_to_earth = earth_coords.separation(sat_coords)
    is_sat_behind_or_on_top_earth = np.array(angular_radius_earth > sat_distance_to_earth)

    #marker = np.array(["o"]*n_satellites)
    #marker[is_sat_behind_or_on_top_earth] = "+"
    #print(radec_targets["is_sunlit"])

    is_visible = ~is_sat_behind_or_on_top_earth
    is_sunlit = radec_targets["is_sunlit"]
    is_moonlit = radec_targets["is_moonlit"]

    #visible_and_sunlit     = np.logical_and(~is_sat_behind_or_on_top_earth,  radec_targets["is_sunlit"])
    #visible_not_sunlit     = np.logical_and(~is_sat_behind_or_on_top_earth,  bool_are_shadowed)
    #visible_not_sunlit_but_moonlit     = np.logical_and(visible_not_sunlit,  radec_targets["is_moonlit"])
    #not_visible_and_sunlit = np.logical_and(is_sat_behind_or_on_top_earth, radec_targets["is_sunlit"])
    #not_visible_not_sunlit = np.logical_and(is_sat_behind_or_on_top_earth, bool_are_shadowed)

    #print(bn.nansum(visible_and_sunlit))
    #print(bn.nansum(visible_not_sunlit))
    #print(bn.nansum(not_visible_and_sunlit))
    #print(bn.nansum(not_visible_not_sunlit))
    output = {"n_satellites": n_satellites,
              "ra":radec_targets["ra"].astype("float32"),
              "dec":radec_targets["dec"].astype("float32"),
              #"delta_angular":radec_targets["delta_angular"], # This is too slow!
              "angular_radius_earth": angular_radius_earth,
              "distance_to_sat": radec_targets["distance_to_sat"],
              "sat_name": radec_targets["sat_name"],
              "epoch": epoch,
              "is_visible": is_visible,
              "is_sunlit": is_sunlit,
              "is_moonlit": is_moonlit,
              "sat_distance_to_earth": sat_distance_to_earth.astype("float32"),
              "is_sat_behind_or_on_top_earth": is_sat_behind_or_on_top_earth}

    del orbit_snapshot["sf_observer"]
    del orbit_snapshot["sf_barycentric_sat_position"]
    output.update(orbit_snapshot)

    return(output)

####################

def get_orbit_snapshot(epoch_mjd, TLE):
    # Get ready the elements from skyfield
    # ts = sf_api.load.timescale()
    #######################################
    # Load the ephemeris database from SkyField
    # This takes a few seconds, but it only loads once.
    #######################################

    #planets = sf_api.load("de440.bsp")

    sf_t_sample_i = ts.from_astropy(Time(epoch_mjd, format='mjd'))

    # Get position of the satellite in cartesian geocentric xyz coordinates.
    xs, ys, zs =  TLE.at(sf_t_sample_i).xyz.km

    # Get ground track of the satellite in geographic lon, lat coordinates.
    latitude  =  TLE.at(sf_t_sample_i).subpoint().latitude.degrees
    longitude  =  TLE.at(sf_t_sample_i).subpoint().longitude.degrees

    # Get the position of the center of the Earth in RA, DEC Equatorial Coordinates
    # This is not immediate. Skyfield takes into account aberration effects
    # Light travel time effects. Etc.
    # Must follow this example
    # https://github.com/skyfielders/python-skyfield/discussions/604
    earth_barycentric = planets["earth"].at(sf_t_sample_i)
    barycentric_sat_position = sf.positionlib.Barycentric(
        earth_barycentric.position.au + TLE.at(sf_t_sample_i).position.au,
         earth_barycentric.velocity.au_per_d + TLE.at(sf_t_sample_i).velocity.au_per_d,
         t=sf_t_sample_i,
        )
    barycentric_sat_position._ephemeris = planets
    earth_apparent = barycentric_sat_position.observe(planets["earth"]).apparent()
    moon_apparent = barycentric_sat_position.observe(planets["moon"]).apparent()
    sun_apparent = barycentric_sat_position.observe(planets["sun"]).apparent()

    ra_earth = earth_apparent.radec()[0]._degrees
    dec_earth = earth_apparent.radec()[1]._degrees

    ra_moon = moon_apparent.radec()[0]._degrees
    dec_moon = moon_apparent.radec()[1]._degrees

    ra_sun = sun_apparent.radec()[0]._degrees
    dec_sun = sun_apparent.radec()[1]._degrees


    return({"xs": xs, "ys": ys, "zs": zs,
            "latitude": latitude, "longitude":longitude,
            "ra_earth": ra_earth, "dec_earth":dec_earth,
            "ra_moon": ra_moon, "dec_moon": dec_moon, "ra_sun":ra_sun, "dec_sun":dec_sun,
            "sf_observer": TLE.at(sf_t_sample_i),
            "sf_barycentric_sat_position": barycentric_sat_position})

########################

def find_closest_TLE(epoch, TLE_history):
    # This has to go under class telescopes. Same function but different list of TLEs
    # ts = sf_api.load.timescale()


    TLE_mjd_list = np.zeros((len(TLE_history),))
    for i in range(len(TLE_history)):
        TLE_mjd_list[i] = TLE_history[i].epoch.to_astropy().mjd
    #print(TLE_mjd_list)
    #print(exposure_epoch)

    closest_TLE_index = rs.utils.find_nearest_index(array=TLE_mjd_list, value=epoch)
    # print(exposure_epoch)
    closest_TLE = TLE_history[closest_TLE_index]

    return(closest_TLE)

########################s

def get_orbit_track(mjd_start, mjd_end, TLE_history, healpix_map_name, n_orbit_sample=20, nside=64, plot=True, verbose=False):
    """ Input:
         - expstart_astropy_time
         - expend_astropy_time
         - closest_TLE

         Optional:
         n_orbit_sample = Number of sampling points during orbit. Default = 20

         Output:
         pandas db = Columns [t [mjd], xs, ys, zs, latitude, longitude]

    """

    # Find the closest TLE in the history.
    exposure_epoch = (mjd_start + mjd_end)/2.
    closest_TLE = sp.satellites.find_closest_TLE(epoch=exposure_epoch, TLE_history=TLE_history)
    #print(closest_TLE)

    expstart_astropy_time = Time(mjd_start, format='mjd')
    expend_astropy_time   = Time(mjd_end,   format='mjd')

    # Get ready the elements from skyfield
    # ts = sf_api.load.timescale()

    sf_t_expstart = ts.from_astropy(expstart_astropy_time)
    sf_t_expend   = ts.from_astropy(expend_astropy_time)

    orbit_sample_mjd = np.linspace(expstart_astropy_time.mjd, expend_astropy_time.mjd, n_orbit_sample)


    # Get the orbit track and ground track on a dataframe
    # Information required:
    # Cartesian geocentric coordinates: xs, ys, zs
    # Ground track Geophaphic coordinates: latitude, longitude
    # Earth center RA, DEC
    # Sun center RA, DEC
    # Moon center RA, DEC
    orbit_track = []
    for i, orbit_sample_mjd_i in zip(range(n_orbit_sample), orbit_sample_mjd):
        orbit_snapshot = get_orbit_snapshot(orbit_sample_mjd_i, closest_TLE)
        orbit_track.append(orbit_snapshot)

    orbit_track = pd.DataFrame(orbit_track)
    orbit_track["epoch"] = orbit_sample_mjd
    if verbose: print(orbit_track)
    ############ ESTIMATE EARTHSHINE ######################
    # Use pysolar to calculate radiation on a surface grid
    # https://earthscience.stackexchange.com/questions/14491/how-to-calculate-the-solar-radiation-at-any-place-any-time
    earthshine_at_t = sp.earth.get_earthshine(mjd=exposure_epoch, nside=nside, healpix_map_name=healpix_map_name)
    #######################################################



    # Plot ground track
    if plot:

        ########## PLOT 1 - GROUND TRACK #############
        fig = plt.figure(figsize=(12,24))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.stock_img()

        plt.plot(orbit_track["longitude"], orbit_track["latitude"],
             color='black', linewidth=2,
             transform=ccrs.Geodetic())

        plt.scatter(orbit_track["longitude"][0], orbit_track["latitude"][0], color='red', marker="o", s=100, transform=ccrs.Geodetic())
        plt.scatter(np.array(orbit_track["longitude"])[-1], np.array(orbit_track["latitude"])[-1], color='red', marker="o", s=100, transform=ccrs.Geodetic())
        plt.savefig("satellite_ground_track.png", dpi=300)
        plt.show()

        ########## PLOT 2 - EARTHSHINE ##############
        hp.cartview(earthshine_at_t, nest=True, title="Ground track", flip="geo")
        plt.scatter(orbit_track["longitude"], orbit_track["latitude"], color='black', marker=".", alpha=0.5)
        plt.scatter(orbit_track["longitude"][0], orbit_track["latitude"][0], color='red', marker="o", s=100)
        plt.scatter(np.array(orbit_track["longitude"])[-1], np.array(orbit_track["latitude"])[-1], color='red', marker="o", s=100)
        plt.savefig("satellite_on_earthshine.png", dpi=300)
        plt.show()

        ########## PLOT 3 - SPHERE #############
        fig = plt.figure(figsize=(8,8))
        ax = fig.add_subplot(projection='3d')

        # Plot  Earth Sphere as reference
        # draw sphere
        u_grid, v_grid = np.mgrid[0:2*np.pi:200j, 0:np.pi:100j]
        x = rs.constants.r_earth.to(u.km)*np.cos(u_grid)*np.sin(v_grid)
        y = rs.constants.r_earth.to(u.km)*np.sin(u_grid)*np.sin(v_grid)
        z = rs.constants.r_earth.to(u.km)*np.cos(v_grid)
        ax.plot_wireframe(x, y, z, color="blue", alpha=0.1)

        ax.scatter(orbit_track["xs"][0], orbit_track["ys"][0], orbit_track["zs"][0], marker=".", s=1000, color="red", alpha=0.9)
        ax.scatter(np.array(orbit_track["xs"])[-1], np.array(orbit_track["ys"])[-1], np.array(orbit_track["zs"])[-1], marker=".", s=1000, color="red", alpha=0.9)
        ax.scatter(orbit_track["xs"], orbit_track["ys"], orbit_track["zs"], marker=".", color="black", alpha=0.9)

        ax.set_xlim(-7000,7000)
        ax.set_ylim(-7000,7000)
        ax.set_zlim(-7000,7000)
        plt.savefig("satellite_orbit_3d.png", dpi=300)
        plt.show()


    return({"orbit_track": orbit_track, "closest_TLE": closest_TLE})


#######################################################################################
#######################################################################################

def does_the_track_intersect_with_FOV(ra_track, dec_track, ra_FOV, dec_FOV, verbose=False):
    from shapely import intersection
    # TO DO: We will need to find a way to deal with the 360 - 0 discontinuity.
    # Most likely it will be a false positive generator, to be re-analyzed later.
    # Once we know which satellites have a high posibility to cross,
    # we can do a careful inspection with a finer delta-t
    from shapely.geometry import Polygon, LineString
    from shapely import points
    import bottleneck as bn
    # Make sure all right ascensions are between 0, 360. 3 October 2024.
    ra_track = ra_track % 360
    ra_FOV = ra_FOV % 360
    # --------------------------------------------------- #

    FOV_polygon = Polygon(np.vstack((ra_FOV, dec_FOV)).T)
    track_line  = LineString(np.vstack((ra_track, dec_track)).T)
    track_points  = points(np.vstack((ra_track, dec_track)).T)
    bool_does_it_intersect = track_line.intersects(FOV_polygon)
    bool_is_the_sat_in_FOV = FOV_polygon.contains(track_points)
    index = np.linspace(0, len(ra_track)-1, len(ra_track)).astype("int")

    high_change_in_ra = False
    no_presence_in_FOV = False

    if bool_does_it_intersect:
        intersection_with_polygon = intersection(track_line, FOV_polygon, grid_size=None)

        # Evaluate if they cross the 360 RA discontinuity.
        ra_abs_gradient = np.abs(np.gradient(ra_track))
        max_change_in_ra =  bn.nanmax(ra_abs_gradient)

        if max_change_in_ra > 150:
            # If the satellite moved more than 150 degrees in a single time resolution
            # element, then the satellite is very likely that it is an artifact.
            # The problem is that Shapely does not know that 0, and 360 degrees are the same
            # So it creates an artificial trail between these two that crosses the whole sky.
            # To avoid this generating fake trails, we need to make sure that the satellites
            # are actually close to the FOV when the trail intersects.
            if verbose: print("High change in ra. The satellite crossed the 0-360 discontinuity.")
            # bool_does_it_intersect = False
            high_change_in_ra = True

            if verbose:
                print("ra_abs_gradient")
                print(ra_abs_gradient)
                print("index")
                print(index)
                print("Check ==")
                print(ra_abs_gradient == bn.nanmax(ra_abs_gradient))
                print("index")
                print(index[ra_abs_gradient == bn.nanmax(ra_abs_gradient)])
            index_high_change_in_ra = int(index[ra_abs_gradient == bn.nanmax(ra_abs_gradient)][0])
            dec_high_change = bn.nanmedian(dec_track[index_high_change_in_ra-1:index_high_change_in_ra+1])
            if verbose: print("RA high_change:" + str(ra_track[index_high_change_in_ra-1]) + " - " + str(ra_track[index_high_change_in_ra+1]))
            if verbose: print("DEC high_change:" + str(dec_high_change))

        if bn.nansum(bool_is_the_sat_in_FOV) == 0:
            if verbose: print("No points inside FOV. Could be a fast satellite or artifact")
            no_presence_in_FOV = True

        if high_change_in_ra and no_presence_in_FOV:
            # Check if the declination at the 0-360 crossing is compatible with that of the FOV.
            if (dec_high_change > bn.nanmin(dec_FOV)) & (dec_high_change < bn.nanmax(dec_FOV)):
                bool_does_it_intersect = False

    else:
        intersection_with_polygon = np.nan #np.array([[np.nan, np.nan],[np.nan, np.nan]])

    return({"bool_intersect": bool_does_it_intersect,
            "intersect_coordinates": intersection_with_polygon,
            "bool_is_the_sat_in_FOV": bool_is_the_sat_in_FOV})

#######################################################################################
#######################################################################################

def which_satellites_cross_FOV(visibility_satellites_db, ra_FOV, dec_FOV, verbose=True):
    # Zero: Get the number of initial satellites
    n_initial_satellites = len(visibility_satellites_db["is_visible"])

    # First - Remove all satellites that are never visible.
    zero_if_never_visible = np.nansum(visibility_satellites_db["is_visible"], axis=1) # zero_if_never_visible_and_sunlit + zero_if_never_visible_and_notsunlit

    bool_trails_to_analyze = zero_if_never_visible != 0
    index_trails_to_analyze = np.linspace(0, n_initial_satellites-1, n_initial_satellites, dtype="int32")
    index_trails_to_analyze = index_trails_to_analyze[bool_trails_to_analyze]
    how_many_trails_to_analyze = bn.nansum(bool_trails_to_analyze)

    if verbose: print("How many satellites are visible at some point? : " + str(how_many_trails_to_analyze))

    # Second - do a for loop that runs does_the_track_intersect_with_FOV for all remaining tracks.
    bool_does_the_track_intersect_with_FOV = np.zeros(n_initial_satellites, dtype="bool")
    bool_is_the_sat_in_FOV = np.zeros(visibility_satellites_db["ra"].shape, dtype="bool")

    intersect_coordinates = [] #np.zeros((n_initial_satellites,2,2), dtype="bool")*np.nan

    for i in index_trails_to_analyze:
        ra_track = visibility_satellites_db["ra"][i,:]
        dec_track = visibility_satellites_db["dec"][i,:]
        track_intersection_with_FOV = does_the_track_intersect_with_FOV(ra_track, dec_track, ra_FOV, dec_FOV)
        bool_does_the_track_intersect_with_FOV[i] = track_intersection_with_FOV["bool_intersect"]
        bool_is_the_sat_in_FOV[i,:] = track_intersection_with_FOV["bool_is_the_sat_in_FOV"]
        intersect_coordinates.append(track_intersection_with_FOV["intersect_coordinates"])
        how_many_tracks_get_into_the_FOV = np.sum(bool_does_the_track_intersect_with_FOV)

    intersect_coordinates = np.array(intersect_coordinates)
    # Plot the results if required
    if verbose: print("How many trails potentially get into the FOV? : " + str(how_many_tracks_get_into_the_FOV))

    if verbose:
        fig, ax = plt.subplots(figsize=(15,7))
        # Plot FOV

        for i in index_trails_to_analyze:
            if bool_does_the_track_intersect_with_FOV[i]:
                ra_track = visibility_satellites_db["ra"][i,:]
                dec_track = visibility_satellites_db["dec"][i,:]
                ax.plot(ra_track, dec_track, alpha=0.5)
                #ax.scatter(ra_track, dec_track)
        ax.set_xlim(0,360)
        ax.set_ylim(-90,90)
        ax.set_xlabel("RA (ICRS)")
        ax.set_ylabel("DEC (ICRS)")
        ax.plot(ra_FOV, dec_FOV, color="firebrick")
        plt.show()

    return({"bool_does_the_track_intersect_with_FOV": bool_does_the_track_intersect_with_FOV,
           "intersect_coordinates": intersect_coordinates, "bool_is_the_sat_in_FOV": bool_is_the_sat_in_FOV})

################################

def get_orbital_altitude_velocity_of_satellites(TLE_satellites, epoch, delta_t=None):

    import skyfield as sf
    from astropy.time import Time
    import numpy as np

    # Set the timescale from skyfield (this line is needed for Skyfield)
    # ts = sf.api.load.timescale()

    t_astropy = Time(epoch, format='mjd')
    t = ts.from_astropy(t_astropy)
    on_flight_t = (t_astropy - t_astropy[0]).to("s")
    dt = np.gradient(on_flight_t.value)

    number_of_targets = len(TLE_satellites)
    n_epochs = len(epoch)


    # This is the storing variable.
    altitude_array = np.zeros((number_of_targets, n_epochs))
    velocity_array = np.zeros((number_of_targets, n_epochs))

    for i in range(len(TLE_satellites)):

        geocentric = TLE_satellites[i].at(t)
        x = geocentric.position.km[0]
        y = geocentric.position.km[1]
        z = geocentric.position.km[2]
        dx = np.gradient(x)
        dy = np.gradient(y)
        dz = np.gradient(z)

        altitude_array[i,:] = np.sqrt(x**2 + y**2 + z**2) - rs.constants.r_earth.to("km").value
        velocity_array[i,:] = np.sqrt((dx/dt)**2 + (dy/dt)**2 + (dz/dt)**2)

    return({"altitude": altitude_array.astype("float32"), 
            "velocity": velocity_array.astype("float32")})

################################

def reconstruct_sparkles_sim(sparkles_db, output_name, render_movie=True, verbose=False, save_mode="full", print_names=True):

    telescope = sparkles_db["basic_configuration"]["telescope"]
    instrument = sparkles_db["basic_configuration"]["instrument"]
    detector = sparkles_db["basic_configuration"]["detector"]
    exposure_params = sparkles_db["basic_configuration"]["exposure_params"]
    binning = sparkles_db["basic_configuration"]["binning"]

    if save_mode == "full":
        save_to_file = True
        save_to_file_lite = False

    if save_mode == "lite":
        save_to_file = False
        save_to_file_lite = True


    # Reconstruct the constellation
    valid_trails = sparkles_db["highres_in_FOV_trails"]["bool_trails_highres"]
    delta_t = sparkles_db["highres_in_FOV_trails"]["delta_t"]
    satellites_list = sparkles_db["highres_in_FOV_trails"]["sat_name"]
    # constellations_all = sp.satellites.load_constellation(nsats=557794, active_baseline=True, verbose=False)
    constellations_all = sp.satellites.load_constellation(nsats=sp.satellites.max_n_sats)

    print("Finding TLEs of satellites...")
    constellation_to_simulate = []
    all_constellation_names = []

    # First we map all the names of the satellites
    for satellite_i_constellation in constellations_all:
        satellite_i_constellation_name = satellite_i_constellation.name
        all_constellation_names.append(satellite_i_constellation_name)

    all_constellation_names = np.array(all_constellation_names)
    satellites_list = np.array(satellites_list)
    # Then we find the TLEs of our target satellites in the right order
    for i in range(len(satellites_list)):
        constellation_to_simulate.append(constellations_all[all_constellation_names == satellites_list[i]][0])

    constellation_to_simulate = np.array(constellation_to_simulate)


    trails = sp.satellites.find_satellite_trails(telescope=telescope,
                               instrument=instrument, detector=detector,
                               exposure_params=exposure_params,
                               constellation=constellation_to_simulate, binning=100, output=output_name,
                               custom_TLE=False, render_movie=render_movie, verbose=verbose,
                               save_to_file=save_to_file, save_to_file_lite=save_to_file_lite,
                               print_names=print_names, delta_t=delta_t)
    return(trails)


###################################


def SPARKLES_simul_survey_single_trail(i, survey_db, telescope, instrument, detector, constellation,
                                       constellation_label, version, save_folder, render_movie=False,
                                        verbose=False, save_mode="full", binning=100, delta_t=None):
    name = save_folder + "/" + telescope.TELESCOP + "_"+ version +"_" + str(np.array(survey_db.iloc[:,0])[i][0]).zfill(10) + "_" + constellation_label + "_NSATS"+ str(len(constellation)).zfill(8) +".fits"
    print(name)
    ra_obs = np.float64(survey_db["ra"].iloc[i])[0] % 360
    dec_obs = np.float64(survey_db["dec"].iloc[i])[0] # [200.0705125, -21.82757777778] #  [exposure_to_analyze["s_ra"],exposure_to_analyze["s_dec"]]
    pa = 0
    mjd_start = np.float64(survey_db["expstart"].iloc[i])[0] #58993.5564069097 # exposure_to_analyze["t_min"] # 5.785922944290E+04
    mjd_end   = (Time(mjd_start, format='mjd') + np.float64(survey_db["exptime"].iloc[i])[0]*u.s).mjd #58993.5600695255 # exposure_to_analyze["t_max"] # 5.785923855244E+04


    if save_mode == "full":
        save_to_file = True
        save_to_file_lite = False

    if save_mode == "lite":
        save_to_file = False
        save_to_file_lite = True

    if True:
        trails = sp.satellites.find_satellite_trails(telescope=telescope,
                               instrument=instrument, detector=detector,
                               exposure_params={"ra": ra_obs,
                                                "dec": dec_obs,
                                                "pa": pa,
                                                "mjd_start": mjd_start,
                                                "mjd_end": mjd_end},
                               constellation=constellation, binning=binning, output=name,
                               custom_TLE=False, render_movie=render_movie, verbose=verbose,
                               save_to_file=save_to_file, save_to_file_lite=save_to_file_lite,
                               delta_t=delta_t)

        return(True)
    else:
        print("WARNING: Something went wrong with this exposure")
        return(False)


def _test_if_it_is_multistring_and_return_the_valid_one(shapely_line):
    import shapely
    if isinstance(shapely_line, shapely.geometry.multilinestring.MultiLineString):
        #print("Is multistring")
        strings = []
        len_strings = []
        for line in shapely_line.geoms:
            strings.append(line)
            len_strings.append(len(line.xy[0]))
        strings = np.array(strings)
        #longest_string = strings[]
        #print(len_strings)
        return(strings[len_strings == np.max(len_strings)][0])
    else:
        return(shapely_line)

def find_mjd_entrance_and_exit_FOV(trail_db, verbose=False):
    valid_trails = trail_db["highres_in_FOV_trails"]["bool_trails_highres"]
    sat_name =  trail_db["highres_in_FOV_trails"]["sat_name"]
    ra_valid = trail_db["highres_in_FOV_trails"]["ra"]
    dec_valid = trail_db["highres_in_FOV_trails"]["dec"]
    epoch = trail_db["highres_in_FOV_trails"]["epoch"]

    intersect_coordinates_valid = np.array(trail_db["highres_in_FOV_trails"]["intersect_coordinates"])[valid_trails]
    epoch_inbound = np.zeros(ra_valid.shape[0])
    epoch_outbound = np.zeros(ra_valid.shape[0])
    trail_time = np.zeros(ra_valid.shape[0])
    omega_sat  = np.zeros(ra_valid.shape)

    delta_angular = np.zeros(ra_valid.shape)
    epoch_in_FOV = np.zeros(ra_valid.shape).astype("bool")
    trail_epoch = np.zeros(ra_valid.shape[0])
    pa = np.zeros(ra_valid.shape[0])

    delta_t = np.zeros(ra_valid.shape[1])
    sunlit_in_FOV = np.zeros(ra_valid.shape[0]).astype("bool")
    moonlit_in_FOV = np.zeros(ra_valid.shape[0]).astype("bool")

    from astropy.time import Time
    import astropy.units as u
    from astropy.coordinates import ICRS, SkyCoord

    t_since_start = (Time(epoch, format='mjd')-Time(epoch[0], format='mjd')).to("second").value
    delta_t = np.median(np.gradient(t_since_start))
    if verbose: print(intersect_coordinates_valid)

    for i in range(ra_valid.shape[0]):
        """
        Not to brag, but the following lines are a very clever way to calculate fast the angular speed.
        trail_radec is the array with the sky positions of the satellite trail.
        trail_radec_2 is the same array, but phased 1 position. When calculating the separation one-on-one
        between the arrays, we obtain the separation between epochs of the satellite.

        Alex S. Borlaff, Madrid, January 10th, 2025.
        """
        trail_radec = SkyCoord(ra_valid[i,:]*u.deg, dec_valid[i,:]*u.deg, frame="icrs")
        trail_radec_2 = SkyCoord(np.concatenate([ra_valid[i,0:1], ra_valid[i,:-1]])*u.deg,
                                 np.concatenate([dec_valid[i,0:1],dec_valid[i,:-1]])*u.deg, frame="icrs")
        delta_angular[i,:] = trail_radec.separation(trail_radec_2).to("arcsec").value

        intersect_coordinates_valid[i] = _test_if_it_is_multistring_and_return_the_valid_one(intersect_coordinates_valid[i])
        ra_cross_1  =  intersect_coordinates_valid[i].xy[0][0]
        dec_cross_1 =  intersect_coordinates_valid[i].xy[1][0]
        ra_cross_2  =  intersect_coordinates_valid[i].xy[0][-1]
        dec_cross_2 =  intersect_coordinates_valid[i].xy[1][-1]


        epoch_ra_cross_1  = epoch[np.where(np.abs(ra_valid[i,:]  - ra_cross_1)   == np.nanmin(np.abs(ra_valid[i,:]  - ra_cross_1)))[0][0]]
        epoch_ra_cross_2  = epoch[np.where(np.abs(ra_valid[i,:]  - ra_cross_2)   == np.nanmin(np.abs(ra_valid[i,:]  - ra_cross_2)))[0][0]]
        epoch_dec_cross_1 = epoch[np.where(np.abs(dec_valid[i,:] - dec_cross_1)  == np.nanmin(np.abs(dec_valid[i,:] - dec_cross_1)))[0][0]]
        epoch_dec_cross_2 = epoch[np.where(np.abs(dec_valid[i,:] - dec_cross_2)  == np.nanmin(np.abs(dec_valid[i,:] - dec_cross_2)))[0][0]]

        epoch_cross_1 = (epoch_ra_cross_1 + epoch_dec_cross_1)/2.
        epoch_cross_2 = (epoch_ra_cross_2 + epoch_dec_cross_2)/2.

        if epoch_cross_2 > epoch_cross_1:
            epoch_inbound[i] = epoch_cross_1
            epoch_outbound[i] = epoch_cross_2

        else:
            epoch_inbound[i] = epoch_cross_2
            epoch_outbound[i] = epoch_cross_1

        pa[i] = rs.utils.position_angle(ra1=[ra_cross_1], dec1 =[dec_cross_1], ra2 = [ra_cross_2], dec2 = [dec_cross_2])[0][0]

        if verbose: print("epoch in " + str(epoch_inbound[i]) + " - "  + str(epoch_outbound[i]) + "")
        trail_start = Time(epoch_inbound[i], format='mjd')
        trail_end = Time(epoch_outbound[i], format='mjd')
        trail_time[i] = (trail_end-trail_start).to("second").value

        #### ADD A NEW RETURN WITH A MASK BOOL ARRAY SHOWING WHICH POINTS ARE INSIDE THE FOV
        epoch_in_FOV[i,:] = (epoch >= epoch_inbound[i]) & (epoch <= epoch_outbound[i])
        sunlit_in_FOV[i]  = np.any(trail_db["highres_in_FOV_trails"]["is_sunlit"][i,:][epoch_in_FOV[i,:]])
        moonlit_in_FOV[i] = np.any(trail_db["highres_in_FOV_trails"]["is_moonlit"][i,:][epoch_in_FOV[i,:]])

        trail_epoch[i] = (epoch_inbound[i] + epoch_outbound[i])/2#np.median(epoch[epoch_in_FOV[i,:]])





    omega_sat = delta_angular/delta_t

    return({"sat_name": sat_name, "epoch_inbound": epoch_inbound,
            "ra_valid": ra_valid, "dec_valid": dec_valid, "pa": pa,
            "epoch_outbound": epoch_outbound, "trail_time": trail_time, "trail_epoch": trail_epoch,
            "delta_separation": delta_angular, "delta_t": delta_t, "omega_sat": omega_sat,
            "epoch_in_FOV": epoch_in_FOV,  "sunlit_in_FOV": sunlit_in_FOV,  "moonlit_in_FOV": moonlit_in_FOV})


################################

def find_satellite_trails(telescope, instrument, detector, exposure_params, constellation,
                          binning=1, output="default_trails.fits", custom_TLE=False, render_movie=False, verbose=True,
                          manual_detector_corners=False, save_to_file=True, save_to_file_lite=False, print_names=False, delta_t=None):

    # Input:
    # Telescope: One of the telescope classes from STAYCOR - Currently:
    #            rs.telescopes.Hubble
    #            rs.telescopes.Roman
    #            rs.telescope.CSST

    # Instrument: Name of the instrument in the telescope. Currently only Hubble ACS / WFPC1/2, Roman/WFI.

    # Detector: For instruments with multiple detectors. Right now, the only one is Hubble ACS/WFC


    # Constellation: An array with the skyfield loaded TLEs of a constellation of satellites to be observed.
    #                Example: constellation = sp.satellites.load_starlinks(verbose=False)

    # exposure_params: A dictionary with the following fields {"ra": ra, "dec":dec, "PA": PA, "mjd_start": mjd_start, "mjd_end": mjd_end}
    #                  Where: RA and DEC are the right ascension and declination of the pointing
    #                  PA is the position angle of the camera, North = 0 and PA increases positive counterclockwise (to the sky East).
    #                  mjd_start, mjd_end are the Modified Julian Date of the exposure start and end respectively.

    basic_configuration_db = {"telescope": telescope, "instrument": instrument, "detector": detector,
                              "exposure_params": exposure_params,
                              "binning": binning, "manual_detector_corners": manual_detector_corners}

    ########################################################
    # Making a dummy image to store the results            #
    ########################################################

    if isinstance(telescope, (str,)):
        telescope_class = rs.telescopes.telescope_class_finder(telescope)

    elif isinstance(telescope, type):
        telescope_class = telescope

    else:
        print("ERROR: Please introduce a valid telescope class or name. Try HST or Roman")

    if verbose: print("exposure_params")
    if verbose: print(exposure_params)
    dummy_name = rs.utils.create_dummy_exposure(telescope=telescope.TELESCOP,
                                                instrument=instrument,
                                                detector=detector,
                                                exposure_params=exposure_params,
                                                binning=binning,
                                                dummy_name=output)
    input_fits = fits.open(dummy_name)

    w = wcs.WCS(header=input_fits[0].header, fobj=input_fits, naxis=2)
    data = input_fits[0].data
    if manual_detector_corners == False:
        detector_corners = rs.detectors.get_detector_corners(wcs=w)
        ra_FOV = np.concatenate((detector_corners["corners_world"][:,0], [detector_corners["corners_world"][0,0]])) % 360
        dec_FOV = np.concatenate((detector_corners["corners_world"][:,1], [detector_corners["corners_world"][0,1]]))
        if np.nanmax(ra_FOV) - np.nanmin(ra_FOV) > 180:
            print("WARNING! This exposure has a FOV too close to the 0 - 360 discontinuity")
            print("Analyzing exposures in this region is currently not supported. Skipping.")
            return("Error!")

    else:
        ra_FOV = manual_detector_corners[0] % 360
        dec_FOV = manual_detector_corners[1]

    basic_configuration_db["ra_FOV"] = ra_FOV
    basic_configuration_db["dec_FOV"] = dec_FOV
    basic_configuration_db["nsats"] = len(constellation)

    ########################################################
    # Load satellites, observers, and exposure parameters  #
    ########################################################

    mjd_start = exposure_params["mjd_start"]
    mjd_end = exposure_params["mjd_end"]

    TLE_epoch = telescope.TLE_exposure(epoch=(mjd_end + mjd_start)/2)


    #######################################################
    # Find out which satellites are sunlit and visible    #
    #######################################################
    visibility_satellites_from_observer = sp.satellites.visibility_satellites_POV(observer_TLE=TLE_epoch,
                                                                                  targets_TLE=constellation,
                                                                                  epoch=np.linspace(mjd_start, mjd_end, 200),
                                                                                  nside=512, verbose=verbose, delta_t=None)


    #######################################################
    # Find out which satellites may cross the FOV         #
    #######################################################
    db_which_satellites_cross_FOV = sp.satellites.which_satellites_cross_FOV(visibility_satellites_db=visibility_satellites_from_observer,
                                                                               ra_FOV=ra_FOV, dec_FOV=dec_FOV, verbose=False)

    #
    #    return("bool_does_the_track_intersect_with_FOV": bool_does_the_track_intersect_with_FOV,
    #            "intersect_coordinates": intersect_coordinates)
    bool_which_satellites_cross_FOV_1 = db_which_satellites_cross_FOV["bool_does_the_track_intersect_with_FOV"]

    ######################################################################################
    # Recalculate the trail trajectory from observer with higher time resolution         #
    ######################################################################################
    print("Number of potential satellite trails: " + str(bn.nansum(bool_which_satellites_cross_FOV_1)))
    print("Refining... ")


    highres_trails = sp.satellites.visibility_satellites_POV(observer_TLE=TLE_epoch,
                                                             targets_TLE=constellation[bool_which_satellites_cross_FOV_1],
                                                             epoch=np.linspace(mjd_start, mjd_end, 10000),
                                                             nside=512, verbose=verbose, delta_t=None)

    db_which_satellites_cross_FOV = sp.satellites.which_satellites_cross_FOV(visibility_satellites_db=highres_trails,
                                                                             ra_FOV=ra_FOV, dec_FOV=dec_FOV, verbose=False)
    bool_which_satellites_cross_FOV = db_which_satellites_cross_FOV["bool_does_the_track_intersect_with_FOV"]

    # Filter the result of highres_trails to remove the trails not needed.
    highres_trails = {"n_satellites": highres_trails["n_satellites"],
                      "ra": highres_trails["ra"][bool_which_satellites_cross_FOV],
                      "dec": highres_trails["dec"][bool_which_satellites_cross_FOV],
                      "angular_radius_earth": highres_trails["angular_radius_earth"],
                      "distance_to_sat": highres_trails["distance_to_sat"][bool_which_satellites_cross_FOV],
                      "sat_name": highres_trails["sat_name"][bool_which_satellites_cross_FOV],
                      "epoch": highres_trails["epoch"],
                      "delta_t": None,
                      "is_visible": highres_trails["is_visible"][bool_which_satellites_cross_FOV],
                      "is_sunlit": highres_trails["is_sunlit"][bool_which_satellites_cross_FOV],
                      "is_moonlit": highres_trails["is_moonlit"][bool_which_satellites_cross_FOV],
                      "sat_distance_to_earth": highres_trails["sat_distance_to_earth"][bool_which_satellites_cross_FOV],
                      "is_sat_behind_or_on_top_earth": highres_trails["is_sat_behind_or_on_top_earth"][bool_which_satellites_cross_FOV]}

    # Get altitude of the satellites.
    altitude_velocity_satellites = sp.satellites.get_orbital_altitude_velocity_of_satellites(TLE_satellites=constellation[bool_which_satellites_cross_FOV_1][bool_which_satellites_cross_FOV],
                                                                                             epoch=np.linspace(mjd_start, mjd_end, 10000),
                                                                                             delta_t=None)
    altitude_satellites = altitude_velocity_satellites["altitude"]
    velocity_satellites = altitude_velocity_satellites["velocity"]
    bool_which_satellites_cross_FOV_highres = db_which_satellites_cross_FOV["bool_does_the_track_intersect_with_FOV"]
    intersect_coordinates = db_which_satellites_cross_FOV["intersect_coordinates"]

    highres_trails["N_trails_highres"] = bn.nansum(bool_which_satellites_cross_FOV_highres)
    highres_trails["bool_trails_highres"] = bool_which_satellites_cross_FOV_highres
    highres_trails["intersect_coordinates"] = intersect_coordinates
    highres_trails["altitude_satellites"] = altitude_satellites
    highres_trails["velocity_satellites"] = velocity_satellites

    #if verbose: print(highres_trails["angular_radius_earth"])
    print("Saving satellite trails...")
    output_filename = output.replace(".fits", ".dat")
    print("Final satellite trails: " + str(highres_trails["N_trails_highres"]))

    output_database = {"basic_configuration": basic_configuration_db,
                       "highres_in_FOV_trails": highres_trails,
                       "all_trails": visibility_satellites_from_observer,
                       "output_filename": output_filename,
                       "delta_t": delta_t}

    output_database_lite =  {"basic_configuration": basic_configuration_db,
                             "highres_in_FOV_trails": highres_trails,
                             #"all_trails": visibility_satellites_from_observer,
                             "output_filename": output_filename,
                             "delta_t": delta_t}


    if save_to_file and (not save_to_file_lite):
        rs.utils.save_dict(output_database, input_name=output_filename)

    if save_to_file_lite:
        rs.utils.save_dict(output_database_lite, input_name=output_filename)


    if render_movie:
        sp.plots.render_satellite_trails_movie(visibility_satellites_from_exposure=visibility_satellites_from_observer,
                                               pointing=[exposure_params["ra"], exposure_params["dec"]],
                                               ra_FOV=ra_FOV, dec_FOV=dec_FOV,
                                               outname=output.replace(".fits",".gif"),
                                               figsize=(20,10), verbose=True,
                                               print_names = print_names)

    return(output_database)

########################



def generate_trail_mask(filename, ext, ra_trail, dec_trail, trail_width, verbose=False):
    n = 10000000
    mask_value = 1
    from scipy.interpolate import splrep, BSpline
    from scipy.ndimage import binary_dilation
    from astropy.io import fits
    hdu = fits.open(filename)
    t = np.linspace(0, len(ra_trail)-1, len(ra_trail))
    x, y = rs.utils.radec_to_xy(ra=ra_trail, dec=dec_trail, fits_name=filename, ext=ext)

    t_spline = np.linspace(np.min(t), np.max(t), n)
    #x_tck = splrep(t, x, s=0, k=1)
    #y_tck = splrep(t, y, s=0, k=1)
    #x_spline =  BSpline(*x_tck)(t_spline)
    #y_spline =  BSpline(*y_tck)(t_spline)

    x_spline = np.interp(x=t_spline, xp=t, fp=x, left=None, right=None, period=None)
    y_spline = np.interp(x=t_spline, xp=t, fp=y, left=None, right=None, period=None)
    # Find distance from each pixel to the spline
    shape_array = hdu[ext].data.shape
    x_image = np.round(x_spline, 0).astype("int")
    y_image = np.round(y_spline, 0).astype("int")
    bool_in_FOV = (x_image >= 0) & (x_image < shape_array[1]) & (y_image >= 0) & (y_image < shape_array[0])

    print_full = 0
    if np.sum(bool_in_FOV) == 0:
        print("Warning: [generate_trail_mask] The satellite does not cross the FOV!")
        print_full = 1

    x_image = x_image[bool_in_FOV]
    y_image = y_image[bool_in_FOV]

    # Mask the pixels in the trail
    streaked_image = np.zeros(shape_array)
    for i in range(len(x_image)):
        streaked_image[y_image[i], x_image[i]] = mask_value

    # Convolve the initial trail seed by a pixel sigma of 1, due to the intrapixel uncertainty.
    #from astropy.convolution import Gaussian2DKernel
    #from astropy.convolution import convolve
    #kernel = Gaussian2DKernel(x_stddev=1)
    #streaked_image = convolve(streaked_image, kernel)
    #streaked_image[streaked_image>0] = 1


    # Make it bigger.
    streaked_image[np.isnan(streaked_image)] = 0
    trail_width_counter = trail_width
    while trail_width_counter > 0:
        streaked_image = binary_dilation(streaked_image, iterations=1, structure=np.array([[ True,  True,  True], [True,  True,  True], [ True,  True,  True]], dtype=bool))
        trail_width_counter = trail_width_counter - 1
        if trail_width_counter == 0:
            break
        streaked_image = binary_dilation(streaked_image, iterations=1, structure=np.array([[False,  True,  False], [True,  True,  True], [ False,  True,  False]], dtype=bool))
        trail_width_counter = trail_width_counter - 1

    #if trail_width > 2:
    #    streaked_image = binary_dilation(streaked_image, iterations=1, structure=np.array([[ True,  True,  True], [True,  True,  True], [ True,  True,  True]], dtype=bool))
    #    streaked_image = binary_dilation(streaked_image, iterations=trail_width-1, structure=np.array([[False,  True,  False], [True,  True,  True], [ False,  True,  False]], dtype=bool))
    #else:
    #    streaked_image = binary_dilation(streaked_image, iterations=1, structure=np.array([[False,  True,  False], [True,  True,  True], [ False,  True,  False]], dtype=bool))


    if verbose:
        from astropy.wcs import WCS as astropy_wcs
        wcs = astropy_wcs(hdu[ext].header)

        fig = plt.figure(figsize=(15,15))
        ax = plt.subplot()
        ax.imshow(hdu[0].data, origin='lower')
        ax.scatter(x_image, y_image, color="red")
        ax.grid(color='white', ls='solid')

        if print_full:
            ax.plot(x_spline, y_spline, '-', label='s=0', alpha=0.4)
            ax.set_xlim(-5000,10000)
            ax.set_ylim(-5000,10000)

        else:
            ax.plot(x_spline[bool_in_FOV], y_spline[bool_in_FOV], '-', label='s=0', alpha=0.4)

        ax.set_xlabel(r'Right ascension (deg)')
        ax.set_ylabel(r'Declination (deg)')

    return(streaked_image)

###############################

def generate_streaked_image_from_sim(trail_db, outname, verbose=False):
    trail_movement = sp.satellites.find_mjd_entrance_and_exit_FOV(trail_db)
    # Make dummy exposure
    #outname = dict_name.replace(".dat", ".fits")
    rs.telescopes.SPHEREx.make_dummy_exposure(ra=trail_db["basic_configuration"]["exposure_params"]["ra"],
                                              dec=trail_db["basic_configuration"]["exposure_params"]["dec"],
                                              pa=trail_db["basic_configuration"]["exposure_params"]["pa"],
                                              outname=outname)

    canvas = fits.open(outname)


    for i in range(len(trail_movement["sat_name"])):
        trail_width = 50
        streaked_mask = generate_trail_mask(filename=outname, ext=0,
                                            ra_trail=trail_movement["ra_valid"][i,:],
                                            dec_trail=trail_movement["dec_valid"][i,:],
                                            trail_width=trail_width, verbose=verbose)

        canvas[0].data[streaked_mask == 1] = canvas[0].data[streaked_mask == 1] + 1

    if verbose:
        plt.show()

    if verbose:
        sp.plots.plot_trails_vs_FOV(trail_db)

    canvas.verify("silentfix")
    canvas.writeto(outname, overwrite=True)


###################################

def distance_and_omega_to_observer_in_trail(trail_db):

    # PROBLEM - If the satellite does not have any snapshot inside the FOV, then its magnitude wont be computed.
    # We need to extract the omega and distance even if the satellite is not inside, but close.
    trail_movement = find_mjd_entrance_and_exit_FOV(trail_db)
    n_trails = trail_db["highres_in_FOV_trails"]["ra"].shape[0]
    import bottleneck as bn
    median_distance_while_in_FOV = np.zeros(n_trails)
    median_omega_while_in_FOV    = np.zeros(n_trails)

    for i in range(n_trails):
        distance_i = trail_db["highres_in_FOV_trails"]["distance_to_sat"][i,:]
        omega_i    = trail_movement["omega_sat"][i,:]
        epoch_in_FOV_i = trail_movement["epoch_in_FOV"][i,:]
        #print(distance_i[epoch_in_FOV_i])
        median_distance_while_in_FOV[i] = bn.nanmedian(distance_i[epoch_in_FOV_i])
        median_omega_while_in_FOV[i] = bn.nanmedian(omega_i[epoch_in_FOV_i])

    return({"distance_to_observer": median_distance_while_in_FOV, "omega": median_omega_while_in_FOV, "trail_movement": trail_movement})


############################




def thermal_radiation_satellite(area, distance, wavelengths, temperature):
    from astropy.modeling.models import BlackBody
    import astropy.units as u
    # BlackBody provides the results in ergs/(cm^2 Hz s sr) when scale has no units
    bb = BlackBody(temperature=temperature, scale=1)
    bb_result = bb(wavelengths)

    angular_area_at_distance = area/distance**2*u.steradian
    thermal_flux = rs.constants.thermal_emissivity*(bb_result*angular_area_at_distance).to("Jy")
    return(thermal_flux)


############
# Get the magnitude of the Sun at the requested wavelength


def magnitude_sun(lambda_ref):
    import pandas as pd
    import os
    import astropy.units as u

    # Load the spectra of the Sun
    mag_sun_db = pd.read_csv(os.environ["ROSALIACACHE"] + "/CORE/magnitude_sun.txt", sep="\t")
    from scipy import interpolate
    magnitude_interpolator = interpolate.interp1d(x=mag_sun_db["lambda_mum"]*10**4, y=mag_sun_db["AB_App"])
    mag_ref = magnitude_interpolator(lambda_ref.to("AA"))
    return(mag_ref)


###############################

def find_TLE_from_sparkles_db(sat_names):
    # Reconstruct the constellation
    satellites_list = sat_names
    constellations_all = sp.satellites.load_constellation(nsats=max_n_sats, verbose=False)

    print(constellations_all)
    constellation_to_simulate = []
    all_constellation_names = []

    # First we map all the names of the satellites
    for satellite_i_constellation in constellations_all:
        satellite_i_constellation_name = satellite_i_constellation.name
        all_constellation_names.append(satellite_i_constellation_name)

    all_constellation_names = np.array(all_constellation_names)
    satellites_list = np.array(satellites_list)
    # Then we find the TLEs of our target satellites in the right order
    for i in range(len(satellites_list)):
        constellation_to_simulate.append(constellations_all[all_constellation_names == satellites_list[i]][0])

    constellation_to_simulate = np.array(constellation_to_simulate)
    return(constellation_to_simulate)

#######################

def earthshine_illumination(epoch, TLE, nside=32):
    import healpy as hp
    import astropy.units as u
    from astropy.time import Time
    from astropy.time import TimezoneInfo  # Specifies a timezone

    orbit_snapshot = sp.satellites.get_orbit_snapshot(epoch_mjd=epoch, TLE=TLE)
    ra_earth = orbit_snapshot["ra_earth"]
    dec_earth = orbit_snapshot["dec_earth"]
    ra_sun = orbit_snapshot["ra_sun"]
    dec_sun = orbit_snapshot["dec_sun"]
    ra_moon = orbit_snapshot["ra_moon"]
    dec_moon = orbit_snapshot["dec_moon"]
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
                                             radius=np.radians(angular_radius_earth).value,
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

    earthshine_sun_ratio = total_flux_earthshine/rs.constants.flux_sun_jy_V

    return({"equivalent_magnitude_earthshine": equivalent_magnitude_earthshine,
           "earthshine_sun_ratio": earthshine_sun_ratio,
           "altitude": altitude_telescope,
           "ra_earth": ra_earth, "dec_earth": dec_earth,
           "ra_sun": ra_sun, "dec_sun": dec_sun,
           "ra_moon": ra_moon, "dec_moon": dec_moon})

###########################


def get_size_satellites(sat_names, min_area=1, max_area=125, fully_random=False):
    # Get the size of satellites. 
    constellations_dir = os.path.dirname(sp.__file__) + "/CORE/CONSTELLATIONS/"
    active_satellite_db_name = constellations_dir + "SPACETRACK_FULL_TLE_9March2026_names.csv"
    active_satellite_db = pd.read_csv(active_satellite_db_name)
    # clean_active_db = active_satellite_db[active_satellite_db["valid"] == 1]

    area = np.zeros(len(sat_names))

    for i in range(len(sat_names)):
        active_satellite_db_id = np.where(active_satellite_db["satname"] == sat_names[i])[0]
        if len(active_satellite_db_id) > 0:
            # print(active_satellite_db.iloc[active_satellite_db_id])
            area[i] = active_satellite_db.iloc[active_satellite_db_id]["area_2"].iloc[0]
        elif "SPACEXODC_L" in sat_names[i]:
            area[i] = 700 # m2 # https://aas.org/sites/default/files/2026-03/American%20Astronomical%20Society%20-%20SpaceX%20Orbital%20Data%20Centers%20Petition%20to%20Deny.pdf
        elif "STARLINK2" in sat_names[i]:
            area[i] = 125 # m2
        elif "STARLINK" in sat_names[i]:
            area[i] = 25 # m2
        else: 
            area[i] = np.random.uniform(low=min_area, high=max_area, size=1)
    return(area)

def brightness_satellite_trails(trail_db, min_sat_size=1, max_sat_size=125, fully_random=False):
    #if True:
    from tqdm import tqdm
    from astropy.time import Time
    import astropy.units as u


    # Simulate the parameters from the satellite
    dsat = np.array(trail_db["dsat"])


    # Assigning a size to the satellites, based on the database. 
    
    if fully_random:
        area_satellite = np.random.uniform(low=min_sat_size, high=max_sat_size, size=len(dsat))
    else:
        area_satellite = get_size_satellites(trail_db["sat_name_all"], min_area=1, max_area=125)

    # area_satellite
    # indices SXODC = np.where(...)
    #  If name == SXODC
    #      area_satellite[indicesSXODC] = 700
    #

    orientation_satellite = np.abs(np.sin(np.radians(np.random.uniform(low=0, high=360, size=len(dsat)))))
    albedo = np.random.uniform(low=0.1, high=0.5, size=len(dsat))
    T_satellites = np.random.normal(loc=280, scale=3, size=len(dsat))

    equivalent_area_satellite = area_satellite * orientation_satellite     # area_satellite = 125 # m2 Starlink v2 mini
    equivalent_size_sat = np.sqrt(equivalent_area_satellite/np.pi)
    R2p = equivalent_size_sat**2 * albedo #


    omega_sat = trail_db["omega_sat"] # arcsec/s of the satellite in the FOV
    #expstart = Time(trail_db["expstart"], format='mjd')
    #expend = Time(trail_db["expend"], format='mjd')
    #exptime = (expend-expstart).to("second").value
    exptime = trail_db["exptime"]
    #print(exptime)

    mirror_diameter = 2*trail_db["mirror_radius"] # trail_db["basic_configuration"]["telescope"].mirror_radius.to("m").value
    pixel_scale = trail_db["pixel_scale"] # trail_db["basic_configuration"]["telescope"].get_pixscale(trail_db["basic_configuration"]["instrument"])
    theta_sat = np.sqrt((((2*equivalent_size_sat)**2 + mirror_diameter**2)/dsat**2)*(180/np.pi*60*60)**2 + (pixel_scale.to("arcsec").value)**2) # arcsec


    #musat_sun = msat_sun - 2.5*np.log10(4/np.pi/theta_sat/omega_sat/exptime)
    #musat_moon = msat_moon - 2.5*np.log10(4/np.pi/theta_sat/omega_sat/exptime)

    #msat_sun = rs.constants.mapp_sun_V_AB + 2.5*np.log10(dsat**2/R2p) # - 2.5*np.log10(np.cos(45)*np.cos(45)*1E4/dsat**2) #
    #msat_moon = rs.constants.mapp_moon_V_AB + 2.5*np.log10(dsat**2/R2p) # - 2.5*np.log10(1E4/dsat**2) #

    #intsat_sun = 10**(-0.4*(musat_sun+56.1))
    #intsat_moon = 10**(-0.4*(musat_moon+56.1))

    # Now estimate the Spectral Energy distirbution of the satellites
    n_wave_bins = 100
    wavelengths = np.logspace(np.log10(0.16e-6), np.log10(100e-6), num=n_wave_bins) * u.m
    mAB_SED_sun = sp.satellites.magnitude_sun(lambda_ref=wavelengths)

    sun_SED = 10**(-0.4*(mAB_SED_sun-8.9))

    # mAB_sat_SED_reflected = mAB_SED_sun[:, np.newaxis] + 2.5*np.log10()
    # reflected_flux_jy = 10**(-0.4*(mAB_sat_SED_reflected-8.9))


    thermal_sat_SED = np.zeros((n_wave_bins, len(dsat)))
    thermal_earthshine_SED = np.zeros((n_wave_bins, len(dsat)))
    earthshine_SED = np.zeros((n_wave_bins, len(dsat)))
    sunshine_SED = np.zeros((n_wave_bins, len(dsat)))
    moon_SED = np.zeros((n_wave_bins, len(dsat)))
    reflected_flux_obs = np.zeros((n_wave_bins, len(dsat)))
    combined_flux_obs = np.zeros((n_wave_bins, len(dsat)))
    reflected_flux_only_sun = np.zeros((n_wave_bins, len(dsat)))
    reflected_flux_only_moon = np.zeros((n_wave_bins, len(dsat)))
    reflected_flux_only_earth = np.zeros((n_wave_bins, len(dsat)))
    surface_brightness = np.zeros((n_wave_bins, len(dsat)))
    surface_brightness_earthshine = np.zeros((n_wave_bins, len(dsat)))
    surface_brightness_moonshine = np.zeros((n_wave_bins, len(dsat)))
    surface_brightness_sunshine = np.zeros((n_wave_bins, len(dsat)))
    surface_brightness_thermal_sat = np.zeros((n_wave_bins, len(dsat)))
    surface_brightness_thermal_earthshine = np.zeros((n_wave_bins, len(dsat)))

    mode="lambert_sphere"
    r_earth_m = rs.constants.r_earth.to("m").value
    if mode=="lambert_sphere":
        phase_sat_sun = trail_db["phase_sat_sun"]
        phase_sat_moon = trail_db["phase_sat_moon"]
        phase_sat_earth = trail_db["phase_sat_earth"]

        moonshine_factor  = (2/(3*np.pi))* (np.sin(phase_sat_moon)  + (np.pi - phase_sat_moon)*np.cos(phase_sat_moon))
        sunshine_factor   = (2/(3*np.pi))* (np.sin(phase_sat_sun)   + (np.pi - phase_sat_sun)*np.cos(phase_sat_sun))
        earthshine_factor_A = (2/(3*np.pi))* (np.sin(phase_sat_earth) + (np.pi - phase_sat_earth)*np.cos(phase_sat_earth))
        earthshine_factor_B1 = ((r_earth_m)/(r_earth_m+trail_db["altitude_satellites"]))**2
        earthshine_factor_B2 = (1-((r_earth_m)/(r_earth_m+trail_db["altitude_satellites"]))**2)

    for i in tqdm(range(len(dsat))):
        epoch = trail_db["trail_epoch"][i]
        satellite_altitude = trail_db["altitude_satellites"][i]
        moon_SED[:,i] = rs.constants.moon_sun_ratio * sun_SED * trail_db["moon_phase"][i]/100


        earthshine_SED[:,i] = trail_db["earthshine_sun_ratio"][i] * sun_SED * earthshine_factor_A[i] # * earthshine_factor_B1[i] * earthshine_factor_B2[i]

        thermal_sat_SED[:,i] = sp.satellites.thermal_radiation_satellite(area=equivalent_area_satellite[i],
                                                       distance=dsat[i],
                                                       wavelengths=wavelengths,
                                                       temperature=T_satellites[i]*u.K)

        thermal_earthshine_factor = np.pi*albedo[i]*(rs.constants.r_earth.to("m").value / (rs.constants.r_earth.to("m").value + trail_db["altitude_satellites"][i]))**2 * earthshine_factor_A[i]
        thermal_earthshine_SED[:,i] = thermal_earthshine_factor*sp.satellites.thermal_radiation_satellite(area=equivalent_area_satellite[i],
                                                       distance=dsat[i],
                                                       wavelengths=wavelengths,
                                                       temperature=290*u.K)

        if not trail_db["sunlit_in_FOV"][i]:
            sunshine_SED[:,i] = sun_SED*0
        else:
            sunshine_SED[:,i] = sun_SED

        if not trail_db["moonlit_in_FOV"][i]:
            moon_SED[:,i] = moon_SED[:,i]*0

        reflected_flux_obs[:,i]  =       R2p[i]/(dsat[i]**2) * (sunshine_factor[i]*sunshine_SED[:,i] + moonshine_factor[i]*moon_SED[:,i] + earthshine_SED[:,i])
        reflected_flux_only_sun[:,i]  =  R2p[i]/(dsat[i]**2) * (sunshine_SED[:,i]*sunshine_factor[i])
        reflected_flux_only_moon[:,i]  = R2p[i]/(dsat[i]**2) * (moon_SED[:,i]*moonshine_factor[i])
        reflected_flux_only_earth[:,i] = R2p[i]/(dsat[i]**2) * (earthshine_SED[:,i])

        combined_flux_obs[:,i] = reflected_flux_obs[:,i] + thermal_sat_SED[:,i] + thermal_earthshine_SED[:,i]

        surface_brightness[:,i]                       = 4*combined_flux_obs[:,i]/(np.pi * theta_sat[i] * omega_sat[i] * exptime[i])
        surface_brightness_sunshine[:,i]              = 4*reflected_flux_only_sun[:,i]/(np.pi * theta_sat[i] * omega_sat[i] * exptime[i])
        surface_brightness_earthshine[:,i]            = 4*reflected_flux_only_earth[:,i]/(np.pi * theta_sat[i] * omega_sat[i] * exptime[i])
        surface_brightness_moonshine[:,i]             = 4*reflected_flux_only_moon[:,i]/(np.pi * theta_sat[i] * omega_sat[i] * exptime[i])
        surface_brightness_thermal_sat[:,i]           = 4*thermal_sat_SED[:,i]/(np.pi * theta_sat[i] * omega_sat[i] * exptime[i])
        surface_brightness_thermal_earthshine[:,i]    = 4*thermal_earthshine_SED[:,i]/(np.pi * theta_sat[i] * omega_sat[i] * exptime[i])


    mAB_sun_and_thermal = -2.5*np.log10(surface_brightness) + 8.9
    #musat_SED_sun = mAB_sun_and_thermal - 2.5*np.log10(4/np.pi/theta_sat/omega_sat/exptime)
    #intsat_SED_sun = 10**(-0.4*(musat_sun+56.1)) # Jy/arcsec2

    #int_obs = np.zeros(len(musat_sun))
    #for i in range(len(musat_sun)):
    #    if trail_movement["sunlit_in_FOV"][i] & trail_movement["moonlit_in_FOV"][i]:
    #        int_obs[i] = intsat_sun[i] + intsat_moon[i]
    #
    #    if (trail_movement["sunlit_in_FOV"][i] == True) & (trail_movement["moonlit_in_FOV"][i] == False):
    #        int_obs[i] = intsat_sun[i]
    #
    #    if (trail_movement["sunlit_in_FOV"][i] == False) & (trail_movement["moonlit_in_FOV"][i] == True):
    #       int_obs[i] = intsat_moon[i]

    # mu_obs = -2.5*np.log10(int_obs) - 56.1


    return({"wavelengths":  wavelengths,
            "surface_brightness": surface_brightness,
            "surface_brightness_sunshine": surface_brightness_sunshine,
            "surface_brightness_earthshine": surface_brightness_earthshine,
            "surface_brightness_moonshine": surface_brightness_moonshine,
            "surface_brightness_thermal_sat": surface_brightness_thermal_sat,
            "surface_brightness_thermal_earthshine": surface_brightness_thermal_earthshine,
            "area_satellite": area_satellite,
            "sunshine_factor": sunshine_factor,
            "moonshine_factor": moonshine_factor,
            "earthshine_factor": earthshine_factor_A*earthshine_factor_B1*earthshine_factor_B2,
            "orientation_satellite": orientation_satellite,
            "albedo": albedo,
            "sat_name":  trail_db["sat_name_all"],
            "omega_sat": omega_sat,
            "exptime": exptime,
            "R2p": R2p,
            "theta_sat": theta_sat,
            "T": T_satellites,
            "dsat": dsat})

############




def reap_trail_results(track_list, min_sat_size=1, max_sat_size=125, fully_random=False):
    max_n_sats =  sp.satellites.max_n_sats
    # nsats_list = np.array([100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000, 1200000, 1400000, max_n_sats])
    nsats_list = np.array([100, 200, 500, 1000, 2000, 5000, 10000, 15000, 20000, 50000, 100000, 200000, 500000, 1000000, 1200000, 1400000, sp.satellites.max_n_sats])
    # nsats_list = np.array([100, 200, 500, 700, 1000, 2000, 5000, 8236, 10000, 20000, 50000, 70000, 100000, 200000, 557794, 1000000])

    from astropy.time import Time
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    nsims_nbin = np.zeros(len(nsats_list))
    nsims_with_trail = np.zeros(len(nsats_list))
    exptime_per_sim = np.zeros(len(track_list))
    mjd_expstart = np.zeros(len(track_list))
    mjd_expend = np.zeros(len(track_list))
    # Initial loop - Find how many trails to we have 
    n_total_satellite_trails = 0 

   # Make a second table with the all track ids, to store the detectable trails
    crossing_trails = np.zeros(len(track_list))*np.nan
    nsats_per_sim = np.zeros(len(track_list))*np.nan
    limb_angle_per_exp = np.zeros(len(track_list))*np.nan

    print("Reading all exposures - First pass")
    for i in tqdm(range(len(track_list))):
        track_db_i = rs.utils.load_dict(track_list[i])
        # print(track_db_i["highres_in_FOV_trails"]["n_satellites"])
        n_total_satellite_trails = n_total_satellite_trails + np.sum(track_db_i["highres_in_FOV_trails"]["bool_trails_highres"])
        nsats_per_sim[i] = track_db_i["basic_configuration"]["nsats"]
        #print(track_db_i["basic_configuration"]["exposure_params"]["mjd_start"])
        mjd_expstart[i] = track_db_i["basic_configuration"]["exposure_params"]["mjd_start"]
        mjd_expend[i] = track_db_i["basic_configuration"]["exposure_params"]["mjd_end"]

    expstart_astropy_time = Time(mjd_expstart, format='mjd')
    expend_astropy_time = Time(mjd_expend, format='mjd')
    exptime_per_sim = (expend_astropy_time-expstart_astropy_time).to("second").value

    
    # Initialize the storage columns 
    telescope = np.zeros((n_total_satellite_trails), dtype=object)
    exposure_name = np.zeros((n_total_satellite_trails), dtype=object)

    track_id = np.zeros((n_total_satellite_trails))
    nsats = np.zeros((n_total_satellite_trails))
    mirror_radius = np.zeros((n_total_satellite_trails))
    pixscale = np.zeros((n_total_satellite_trails))

    ra_obs = np.zeros((n_total_satellite_trails))

    dec_obs = np.zeros((n_total_satellite_trails))
    ra_earth = np.zeros((n_total_satellite_trails))
    dec_earth = np.zeros((n_total_satellite_trails))
    ra_sun = np.zeros((n_total_satellite_trails))
    dec_sun = np.zeros((n_total_satellite_trails))
    ra_moon = np.zeros((n_total_satellite_trails))
    dec_moon = np.zeros((n_total_satellite_trails))
    altitude_telescope = np.zeros((n_total_satellite_trails))

    limb_angle = np.zeros((n_total_satellite_trails))

    expstart = np.zeros((n_total_satellite_trails))
    expend = np.zeros((n_total_satellite_trails))
    exptime = np.zeros((n_total_satellite_trails))
    satname  = np.zeros((n_total_satellite_trails), dtype=object)
    omega_sat = np.zeros((n_total_satellite_trails))
    pa_trail = np.zeros((n_total_satellite_trails))
    dsat = np.zeros((n_total_satellite_trails))
    altitude_satellites = np.zeros((n_total_satellite_trails))
    trail_epoch = np.zeros((n_total_satellite_trails))
    trail_time = np.zeros((n_total_satellite_trails))
    sunlit_in_FOV = np.zeros((n_total_satellite_trails))
    moonlit_in_FOV = np.zeros((n_total_satellite_trails))
    moon_phase = np.zeros((n_total_satellite_trails))
    earthshine_sun_ratio = np.zeros((n_total_satellite_trails))
    angular_radius_earth = np.zeros((n_total_satellite_trails))


    
    # Second pass: Fill each field satellite trail by satellite trail. 
    sat_counter = 0

    # Find the properties of the telescope
    telescope_string = track_db_i["basic_configuration"]["telescope"].TELESCOP
    telescope_class = rs.telescopes.telescope_class_finder(telescope_string)


    ntrails = np.zeros(len(track_list))
    ntrails_sunlit = np.zeros(len(track_list))
    ntrails_moonlit = np.zeros(len(track_list))

    ######## START FOR #############
    print("Reading all trails...")
    for i in tqdm(range(len(track_list))):
        track_db_i = rs.utils.load_dict(track_list[i])
        print(track_list[i])
        # Number of trails in this file
        n_satellite_trails_in_this_sim = np.sum(track_db_i["highres_in_FOV_trails"]["bool_trails_highres"])
        in_FOV_parameters = sp.satellites.find_mjd_entrance_and_exit_FOV(track_db_i)
        
        ntrails[i] = track_db_i["highres_in_FOV_trails"]["N_trails_highres"]
        ntrails_sunlit[i] = np.sum(in_FOV_parameters["sunlit_in_FOV"])
        ntrails_moonlit[i] = np.sum(in_FOV_parameters["moonlit_in_FOV"])
        
        distance_and_omega = sp.satellites.distance_and_omega_to_observer_in_trail(track_db_i)

        exp_med = (track_db_i["basic_configuration"]["exposure_params"]["mjd_start"] +  track_db_i["basic_configuration"]["exposure_params"]["mjd_end"])/2
        TLE_observer = telescope_class.TLE_exposure(epoch=exp_med)
        telescope_earthshine_illumination = sp.earth.find_earthshadow_from_satellite(TLE=TLE_observer, epoch=np.array([exp_med]))
        
        nsims_nbin[nsats_list == track_db_i["basic_configuration"]["nsats"]] = nsims_nbin[nsats_list == track_db_i["basic_configuration"]["nsats"]] + 1

        # Fill all the constant - per - simulation fields 
        if n_satellite_trails_in_this_sim > 0:
            nsims_with_trail[nsats_list == track_db_i["basic_configuration"]["nsats"]] = nsims_with_trail[nsats_list == track_db_i["basic_configuration"]["nsats"]] + 1
            telescope[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_db_i["basic_configuration"]["telescope"].TELESCOP
            exposure_name[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_list[i]
            track_id[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_list[i].split("_")[-3]
            mirror_radius[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_db_i["basic_configuration"]["telescope"].mirror_radius.to("m").value
            pixscale[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_db_i["basic_configuration"]["telescope"].get_pixscale(track_db_i["basic_configuration"]["instrument"])
            nsats[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_db_i["basic_configuration"]["nsats"]
            ra_obs[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_db_i["basic_configuration"]["exposure_params"]["ra"]
            dec_obs[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_db_i["basic_configuration"]["exposure_params"]["dec"]

            # For limb angle
            altitude_telescope[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = telescope_earthshine_illumination["altitude_telescope"]
            angular_radius_earth[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = np.degrees(telescope_earthshine_illumination["angular_radius_earth"])

            ra_earth[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = telescope_earthshine_illumination["ra_earth"]
            dec_earth[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = telescope_earthshine_illumination["dec_earth"]
            ra_sun[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = telescope_earthshine_illumination["ra_sun"]
            dec_sun[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = telescope_earthshine_illumination["dec_sun"]
            ra_moon[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = telescope_earthshine_illumination["ra_moon"]
            dec_moon[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = telescope_earthshine_illumination["dec_moon"]
            #--------------# 
            
            expstart[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_db_i["basic_configuration"]["exposure_params"]["mjd_start"]
            expend[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_db_i["basic_configuration"]["exposure_params"]["mjd_end"]

            valid_trails = track_db_i["highres_in_FOV_trails"]["bool_trails_highres"]
            satname[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = track_db_i["highres_in_FOV_trails"]["sat_name"]
            trail_epoch[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = in_FOV_parameters["trail_epoch"]
            trail_time[sat_counter:sat_counter+n_satellite_trails_in_this_sim] =  in_FOV_parameters["trail_time"]
            sunlit_in_FOV[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = in_FOV_parameters["sunlit_in_FOV"]
            moonlit_in_FOV[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = in_FOV_parameters["moonlit_in_FOV"]

            dsat[sat_counter:sat_counter+n_satellite_trails_in_this_sim]  = distance_and_omega["distance_to_observer"]
            omega_sat[sat_counter:sat_counter+n_satellite_trails_in_this_sim]  = distance_and_omega["omega"]
            pa_trail[sat_counter:sat_counter+n_satellite_trails_in_this_sim] = in_FOV_parameters["pa"]

        else:
            crossing_trails[i] = 0
        
        sat_counter = sat_counter + n_satellite_trails_in_this_sim

    pixscale = pixscale*u.arcsec

    # Now the individual properties of each satellite trail 
    TLEs = sp.satellites.find_TLE_from_sparkles_db(sat_names=satname)

    print("Estimating per trail properties (Moon phase)...")

    for i in tqdm(range(len(satname))):
        moon_phase[i] = sp.earth.moon_phase(epoch=trail_epoch[i])
        earthshine_illumination_sat_i = sp.satellites.earthshine_illumination(epoch=trail_epoch[i], TLE=TLEs[i])
        earthshine_sun_ratio[i] = earthshine_illumination_sat_i["earthshine_sun_ratio"]
        altitude_satellites[i] = earthshine_illumination_sat_i["altitude"].to("m").value


    ######## END FOR #############

    ##### Estimate Satellite phase angles for the different components ###########


    if telescope_string == "SPHEREx":
        h_telescope = 650000*u.m
    if telescope_string == "HST":
        h_telescope = 540000*u.m
    if telescope_string == "CSST":
        h_telescope = 450000*u.m
    if telescope_string == "ARRAKIHS":
        h_telescope = 800000*u.m
    if telescope_string == "MESSIER":
        h_telescope = 900000*u.m

    radec_obs   = SkyCoord(ra_obs*u.deg,   dec_obs*u.deg, frame='icrs')
    radec_earth = SkyCoord(ra_earth*u.deg, dec_earth*u.deg, frame='icrs')
    sep_obs_earth = radec_earth.separation(radec_obs).to(u.deg).value

    radec_moon  = SkyCoord(ra_moon*u.deg,  dec_moon*u.deg, frame='icrs')
    radec_sun   = SkyCoord(ra_sun*u.deg,   dec_sun*u.deg, frame='icrs')
    phase_sat_sun = np.pi - radec_obs.separation(radec_sun).to(u.rad).value
    phase_sat_moon = np.pi - radec_obs.separation(radec_moon).to(u.rad).value
    phase_sat_earth = np.arcsin(np.sin(radec_obs.separation(radec_earth).to(u.rad).value)*(h_telescope.to("m").value + rs.constants.r_earth.to("m").value)/(earthshine_illumination_sat_i["altitude"].to("m").value + rs.constants.r_earth.to("m").value))

    # Estimate the limb angle 
    #angular_radius_earth = np.degrees(np.arcsin(rs.constants.r_earth.to("m").value/(altitude_telescope + rs.constants.r_earth.to("m").value)))
    limb_angle = sep_obs_earth - angular_radius_earth

    ####################################################################
    
    expstart_astropy_time = Time(expstart, format='mjd')
    expend_astropy_time = Time(expend, format='mjd')
    exptime = (expend_astropy_time-expstart_astropy_time).to("second").value


    # Now estimate their brightness: 
    for_brightness_db = {"sat_name_all": satname, "trail_epoch": trail_epoch, "altitude_satellites": altitude_satellites, 
                         "omega_sat": omega_sat, "dsat": dsat, 
                         "phase_sat_sun": phase_sat_sun, "phase_sat_moon": phase_sat_moon, "phase_sat_earth": phase_sat_earth, 
                         "pixel_scale": pixscale, "mirror_radius": mirror_radius, "exptime": exptime, 
                         "sunlit_in_FOV": sunlit_in_FOV, "moonlit_in_FOV": moonlit_in_FOV, 
                         "moon_phase": moon_phase, "earthshine_sun_ratio": earthshine_sun_ratio,}
    
    brightness_db = sp.satellites.brightness_satellite_trails(trail_db = for_brightness_db, min_sat_size=min_sat_size, max_sat_size=max_sat_size, fully_random=fully_random)

    # Find the average wavelength for each telescope. 
    #hst_mean_wave = (0.2+1.7)/2
    #csst_mean_wave = (0.2+1.1)/2
    #arrakihs_mean_wave = (0.38+1.6)/2
    #spherex_mean_wave = (5.0+0.75)/2
    messier_wave_id = 22
    hst_wave_id = 27
    csst_wave_id = 22
    arrakihs_wave_id = 28
    spherex_wave_id = 44

    mu_hst = -2.5*np.log10(brightness_db["surface_brightness"][hst_wave_id,:]) + 8.9
    mu_csst = -2.5*np.log10(brightness_db["surface_brightness"][csst_wave_id,:]) + 8.9
    mu_arrakihs = -2.5*np.log10(brightness_db["surface_brightness"][arrakihs_wave_id,:]) + 8.9 
    mu_spherex = -2.5*np.log10(brightness_db["surface_brightness"][spherex_wave_id,:]) + 8.9
    mu_messier = -2.5*np.log10(brightness_db["surface_brightness"][messier_wave_id,:]) + 8.9

    # Is the trail detectable? 
    if telescope_string == "SPHEREx":
        mu = mu_spherex
        bool_detected = mu < 24.63

    if telescope_string == "HST":
        mu = mu_hst
        bool_detected = mu < 25.75

    if telescope_string == "CSST":
        mu = mu_csst
        bool_detected = mu < 25.75
    # Is the trail ARRAKIHS? 
    if telescope_string == "ARRAKIHS":
        mu = mu_arrakihs
        bool_detected = mu < 26.31
        
    if telescope_string == "MESSIER":
        mu = mu_messier
        bool_detected = mu < -999999
    
        
    # nsims_with_visible_trail

    
    db_total_trails = {"track_id": track_id,
                       "telescope": telescope,
                       "mirror_radius": mirror_radius,
                       "pixscale": pixscale,
                       "nsats": nsats,
                       "ra_obs": ra_obs, "dec_obs": dec_obs,
                       "ra_earth": ra_earth, "dec_earth": dec_earth, 
                       "ra_sun": ra_sun, "dec_sun": dec_sun, 
                       "ra_moon": ra_moon, "dec_moon": dec_moon, 
                       "altitude_telescope": altitude_telescope, "angular_radius_earth": angular_radius_earth,
                       "sep_obs_earth": sep_obs_earth, "limb_angle": limb_angle,
                       "expstart": expstart,
                       "expend": expend,
                       "phase_sat_sun": phase_sat_sun, "phase_sat_moon": phase_sat_moon, "phase_sat_earth": phase_sat_earth, 
                       "exptime": exptime, "exposure_name": exposure_name,
                       "trail_epoch": trail_epoch, "trail_time": trail_time,
                       "sunlit_in_FOV": sunlit_in_FOV, "moonlit_in_FOV": moonlit_in_FOV,
                       "dsat": dsat, "omega_sat": omega_sat, "altitude_satellites": altitude_satellites, "altitude_telescope": altitude_telescope, "pa_trail": pa_trail,
                       "earthshine_sun_ratio": earthshine_sun_ratio, "moon_phase":moon_phase, 
                       "mu": mu, "mu_hst": mu_hst, "mu_csst": mu_csst, "mu_arrakihs": mu_arrakihs, "mu_spherex": mu_spherex, "bool_detected":bool_detected, 
                        }

    
    import bottleneck as bn
    import sys, os
    sys.path.append("/Users/aborlaff/GIT/bootmedian/")
    import bootmedian as bm
    
    n_trails_per_exposure = np.zeros((8,len(nsats_list))) 
    fraction_exps_with_at_least_one_trail = np.zeros((4,len(nsats_list)))
    number_of_trails = []

    # Finally, we calculate the % of contaminated exposures.
    for i in range(len(track_list)):
        #if np.isnan(crossing_trails[i]):
        track_id = np.float32(track_list[i].split("_")[-3])
        nsats_i = np.float32(track_list[i].split("_")[-1].replace(".dat","").replace("NSATS",""))
        crossing_trails[i] = np.sum(bool_detected[(db_total_trails["track_id"]==track_id) & (db_total_trails["nsats"] == nsats_i)])
        limb_angle_per_exp[i] = np.nanmedian(limb_angle[(db_total_trails["track_id"]==track_id) & (db_total_trails["nsats"] == nsats_i)])

    
    print("Estimating the fraction of trails per exposure...")
    for i in tqdm(range(len(nsats_list))):
        nsats_i = nsats_list[i]
        # Fraction of contaminated exposures
        nsimulations_within_nsats_bin = len(nsats_per_sim[nsats_per_sim == nsats_i])
        trails_per_simulation_within_bin = np.sum(crossing_trails[nsats_per_sim == nsats_i]>0)
        fraction_exps_with_at_least_one_trail[0,i] = trails_per_simulation_within_bin/nsimulations_within_nsats_bin
        fraction_exps_with_at_least_one_trail[1,i] = np.sqrt(trails_per_simulation_within_bin)/nsimulations_within_nsats_bin

        # Number of trails per exposure
        sample_trail_per_nsats_bin = crossing_trails[nsats_per_sim==nsats_i]
        bootsum = bm.bootmedian(np.array(sample_trail_per_nsats_bin), mode="mean")
        n_trails_per_exposure[0,i] = nsats_i
        n_trails_per_exposure[1,i] = bootsum["median"]
        n_trails_per_exposure[2,i] = bootsum["s1_up"]
        n_trails_per_exposure[3,i] = bootsum["s1_down"]
        n_trails_per_exposure[4,i] = bootsum["s2_up"]
        n_trails_per_exposure[5,i] = bootsum["s2_down"]
        n_trails_per_exposure[6,i] = bootsum["s3_up"]
        n_trails_per_exposure[7,i] = bootsum["s3_down"]

    return({"db_total_trails": pd.DataFrame(db_total_trails), 
            "brightness_db": brightness_db,
            "properties_per_bin": {"n_trails_per_exposure":n_trails_per_exposure,
                                   "fraction_exps_with_at_least_one_trail": fraction_exps_with_at_least_one_trail},
            "properties_per_sim": {"trail_list": track_list, "crossing_trails": crossing_trails, "exptime": exptime_per_sim,
                                   "nsats_per_sim": nsats_per_sim, "limb_angle_per_exp": limb_angle_per_exp, 
                                   "ntrails": ntrails, "ntrails_sunlit": ntrails_sunlit, "ntrails_moonlit": ntrails_moonlit,
                                   }})