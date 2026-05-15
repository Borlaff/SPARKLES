# Alejandro S. Borlaff. NASA Ames Research Center. a.s.borlaff@nasa.gov / asborlaff@gmail.com
# January 20, 2023.
#
# STRAYCOR/PSF module
# This module will hold all the programs related to the modelling and removal
# of the PSF.
#
# Version log:
# v.1.0 - 20 Enero 2023. First loading of programs inherited from former monolithic straycor.py
#
##########################################################

############################
import os
import sys
import pandas as pd
import numpy as np
import bottleneck as bn
from tqdm import tqdm
from astropy.io import fits
import astropy.wcs as wcs
import matplotlib.pyplot as plt
from celluloid import Camera
from astropy.io import ascii
import astropy.units as u
from astropy.coordinates import ICRS, Angle, SkyCoord
import rosalia as rs
import sparkles as sp

# Suppress warnings. Comment this out if you wish to see the warning messages
import warnings
warnings.filterwarnings('ignore')


################################################################################

def anim_satellites_POV(i, observer_TLE, targets_TLE, epoch, nside=512):
    plot_satellites_POV(observer_TLE, targets_TLE, epoch, nside=512)
    return()


################################################################################


def plot_FOV_with_trails(i, ax, trails, bool_which_satellites_cross_FOV, ra_FOV, dec_FOV):
    # Get the number of trails
    n_trails = len(trails["visible_and_sunlit"])

    # Plot FOV
    ax.plot(ra_FOV, dec_FOV, color="firebrick")
    ax.set_xlim((np.max(ra_FOV)-1, np.min(ra_FOV)+1))
    ax.set_ylim((np.min(dec_FOV)-1, np.max(dec_FOV)+1))
    ra_track = trails["ra"][i,:]
    dec_track = trails["dec"][i,:]


    if bool_which_satellites_cross_FOV[i]:
        ax.plot(ra_track, dec_track)


################################################################################


def render_satellite_trails_movie(visibility_satellites_from_exposure,
                                  pointing, ra_FOV, dec_FOV,
                                  outname, figsize=(20,10), verbose=True, print_names=False):

    plt.style.use('dark_background')

    fig = plt.figure(figsize=figsize)
    #gs = fig.add_gridspec(2, 2)
    #ax1 = fig.add_subplot(gs[0, 0])
    #ax2 = fig.add_subplot(gs[0, 1])
    #ax3 = fig.add_subplot(gs[1, :])

    gs = fig.add_gridspec(1, 1)
    ax3 = fig.add_subplot(gs[0, 0])

    camera = Camera(fig)
    nframes = visibility_satellites_from_exposure["ra"].shape[1]


    ax3.set_xlim(360, 0)
    ax3.set_ylim(-90, 90)
    ax3.set_xlabel("RA (ICRS)")
    ax3.set_ylabel("DEC (ICRS)")

    # Ax 2
    #ax2.set_xlim(np.max(ra_FOV), np.min(ra_FOV))
    #ax2.set_ylim(np.min(dec_FOV), np.max(dec_FOV))
    bool_which_satellites_cross_FOV = sp.satellites.which_satellites_cross_FOV(visibility_satellites_from_exposure, ra_FOV, dec_FOV, verbose=False)["bool_does_the_track_intersect_with_FOV"]

    for i in tqdm(range(nframes), position=0, leave=True):
        #plot_FOV_with_trails(i=i, ax=ax2, trails=visibility_satellites_from_exposure,
        #                     bool_which_satellites_cross_FOV=bool_which_satellites_cross_FOV,
        #                     ra_FOV=ra_FOV, dec_FOV=dec_FOV)

        # Ax 3
        ax3.scatter(pointing[0], pointing[1],  alpha=1, marker="+", edgecolor="white", facecolor="None", s=200)
        plot_satellites_POV(i, ax3, visibility_satellites_from_exposure, ra_FOV, dec_FOV, print_names)
        camera.snap()

        # Plot the pointing direction as a red dot

    if verbose: print("Saving movie...")
    movie = camera.animate()
    movie.save(outname)
    #if verbose: Image(outname)
    if verbose: print("Done! " + outname)
    plt.style.use('default')
    return(outname)


################################################################################

def starlink_gui(i, satellites, TLE_observer):
    ######### HOW TO RUN #################
    # plt.style.use('dark_background')
    # fig = plt.figure(figsize=(20,20))
    # ax = fig.add_subplot(projection='3d')

    # TLE_observer = satellites[0]
    # ani = FuncAnimation(plt.gcf(), starlink_gui, interval=50, fargs=(satellites, TLE_observer, ))
    # plt.show()

    xs = np.zeros(len(satellites))
    ys = np.zeros(len(satellites))
    zs = np.zeros(len(satellites))
    is_sunlit = np.zeros(len(satellites))

    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    plt.cla()

    """
    Here we calculate the relative positions of the satellites from the observer POV
    """
    planets = sf.api.load("de440.bsp")
    earth = planets["EARTH"]
    observer_vector = earth + TLE_observer
    #for target_i in tqdm(targets):
    #    target_vector   = earth + target
    #    coords_satellite_i_from_LEO_observer = observer_vector.at(t).observe(target_vector).apparent()


    ts = sf.api.load.timescale()
    t = ts.now()

    # Plot the observer
    xs_observer, ys_observer, zs_observer =  TLE_observer.at(t).xyz.km
    ax.scatter(xs_observer, ys_observer, zs_observer, marker=".", color="red", alpha=0.9, s=200)



    for i in range(len(satellites)):
        # Find out if the satellites are sunlit
        xs[i], ys[i], zs[i] =  satellites[i].at(t).xyz.km
        is_sunlit[i] = satellites[i].at(t).is_sunlit(planets)

        # Find out if the satellite is visible from the observer

        # .is_behind_earth()

    ax.scatter(xs[is_sunlit == True], ys[is_sunlit == True], zs[is_sunlit == True], marker=".", color="yellow", alpha=0.5)
    #ax.scatter(xs[is_sunlit], ys[is_sunlit], zs[is_sunlit], marker=".", color="yellow", alpha=0.5)

    # Plot Earth grid
    u_grid, v_grid = np.mgrid[0:2*np.pi:200j, 0:np.pi:100j]
    x = rs.constants.r_earth.to(u.km)*np.cos(u_grid)*np.sin(v_grid)
    y = rs.constants.r_earth.to(u.km)*np.sin(u_grid)*np.sin(v_grid)
    z = rs.constants.r_earth.to(u.km)*np.cos(v_grid)
    ax.plot_wireframe(x, y, z, color="blue", alpha=0.1)

    ax.set_ylim(-7000, 7000)
    ax.set_xlim(-7000,7000)
    ax.set_zlim(-7000, 7000)

    #plt.legend(loc='upper left')
    #plt.tight_layout()


################################################################################


def plot_satellites_POV(i, ax, visibility_satellites_from_exposure, ra_FOV, dec_FOV, print_names):
    #### PLOT ZONE ####
    distance_to_sat = visibility_satellites_from_exposure["distance_to_sat"][:,i]
    markersize = 1/distance_to_sat
    markersize = 100*markersize/bn.nanmax(markersize) + 1
    ra_sun    = visibility_satellites_from_exposure["ra_sun"]
    dec_sun   = visibility_satellites_from_exposure["dec_sun"]
    ra_earth  = visibility_satellites_from_exposure["ra_earth"]
    dec_earth = visibility_satellites_from_exposure["dec_earth"]
    ra_moon   = visibility_satellites_from_exposure["ra_moon"]
    dec_moon  = visibility_satellites_from_exposure["dec_moon"]
    radius_earth = visibility_satellites_from_exposure["angular_radius_earth"][i].value*180/np.pi
    # Circle around EARTH
    earth_circle = rs.utils.circle_around_position(ra=ra_earth[i], dec=dec_earth[i],
                                                   radius=radius_earth, npoints=5000)
    sun_circle = rs.utils.circle_around_position(ra=ra_sun[i], dec=dec_sun[i],
                                                   radius=0.5, npoints=100)
    moon_circle = rs.utils.circle_around_position(ra=ra_moon[i], dec=dec_moon[i],
                                                   radius=0.5, npoints=100)

    ax.scatter(earth_circle.ra.degree, earth_circle.dec.degree, s=5, color="dodgerblue", alpha=0.5)
    ax.scatter(sun_circle.ra.degree,   sun_circle.dec.degree,   s=5, color="gold",       alpha=0.5)
    ax.scatter(moon_circle.ra.degree,  moon_circle.dec.degree,  s=5, color="silver",     alpha=0.5)

    ax.scatter(ra_sun[i],    dec_sun[i],    alpha=1, marker=r'$\odot$',      edgecolor="gold", facecolor="None", s=300)
    ax.scatter(ra_earth[i],  dec_earth[i],  alpha=1, marker=r'$\bigoplus$',  edgecolor="dodgerblue", facecolor="None", s=300)
    ax.scatter(ra_moon[i],   dec_moon[i],   alpha=1, marker=r'$\bigotimes$', edgecolor="silver", facecolor="None", s=300)

    #ndim=10
    #for j in range(ndim):
    #    earth_circle_dim = rs.utils.circle_around_position(ra=ra_earth[j], dec=dec_earth[j],
    #                                                       radius=ndim/(i+1)*radius_earth, npoints=1000)

    #    ax.scatter(earth_circle_dim.ra.degree, earth_circle_dim.dec.degree, s=5, color="dodgerblue", alpha=1/(i+1)**2)    #print("RA")

    #    sun_circle_dim = rs.utils.circle_around_position(ra=ra_sun[j], dec=dec_sun[j],
    #                                                       radius=10/i*radius_earth, npoints=365)
    #
    #    ax.scatter(earth_circle_dim.ra.degree, earth_circle_dim.dec.degree, s=5, color="dodgerblue", alpha=1/(i+1)**2)    #print("RA")

    # Visible and sunlit

    visible_and_sunlit     = np.logical_and(visibility_satellites_from_exposure["is_visible"][:,i],
                                            visibility_satellites_from_exposure["is_sunlit"][:,i])
    filter_scatter = visible_and_sunlit

    ax.scatter(visibility_satellites_from_exposure["ra"][:,i][filter_scatter],
               visibility_satellites_from_exposure["dec"][:,i][filter_scatter], alpha=1,
               marker="o", color="yellow", s=markersize[filter_scatter], label="Visible and sunlit")



    #print(visibility_satellites_from_exposure["ra"][:,i][filter_scatter].shape)

    #print("filter_scatter")
    #print(filter_scatter.shape)
    #print("sat_name")
    #print(visibility_satellites_from_exposure["sat_name"].shape)

    if print_names:
        for j in range(len(visibility_satellites_from_exposure["sat_name"][filter_scatter])):
            ax.text(visibility_satellites_from_exposure["ra"][:,i][filter_scatter][j],
                    visibility_satellites_from_exposure["dec"][:,i][filter_scatter][j], alpha=0.9,
                    s=visibility_satellites_from_exposure["sat_name"][filter_scatter][j], color="yellow")

    # For the visible and sunlit, plot the trail line.
    #for j in range(i):
    #    ra_i = visibility_satellites_from_exposure["ra"][:,i][filter_scatter]
    #    dec_i = visibility_satellites_from_exposure["dec"][:,i][filter_scatter]
    #    s = markersize[filter_scatter]
    #
    #    for k in range(len(ra_i)):
    #        ax.scatter(ra_i, dec_i, alpha=1, marker="o", color="yellow", s=s, label="Visible and sunlit")


    # Visible not sunlit
    #filter_scatter = visibility_satellites_from_exposure["visible_not_sunlit"][:,i]

    visible_and_not_sunlit     = np.logical_and(visibility_satellites_from_exposure["is_visible"][:,i],
                                                ~visibility_satellites_from_exposure["is_sunlit"][:,i])
    filter_scatter = visible_and_not_sunlit

    ax.scatter(visibility_satellites_from_exposure["ra"][:,i][filter_scatter],
               visibility_satellites_from_exposure["dec"][:,i][filter_scatter], alpha=0.9,
               marker="o", color="ghostwhite", s=markersize[filter_scatter], label="Visible - Not sunlit")

    if print_names:
        for j in range(len(visibility_satellites_from_exposure["sat_name"][filter_scatter])):
            ax.text(visibility_satellites_from_exposure["ra"][:,i][filter_scatter][j],
                    visibility_satellites_from_exposure["dec"][:,i][filter_scatter][j], alpha=0.9,
                    s=visibility_satellites_from_exposure["sat_name"][filter_scatter][j], color="ghostwhite")


    # Not visible and sunlit
    #filter_scatter = visibility_satellites_from_exposure["not_visible_and_sunlit"][:,i]

    not_visible_and_sunlit     = np.logical_and(~visibility_satellites_from_exposure["is_visible"][:,i],
                                                    visibility_satellites_from_exposure["is_sunlit"][:,i])
    filter_scatter = not_visible_and_sunlit

    ax.scatter(visibility_satellites_from_exposure["ra"][:,i][filter_scatter],
               visibility_satellites_from_exposure["dec"][:,i][filter_scatter], alpha=0.5,
               marker="o", color="darkorange", s=markersize[filter_scatter], label="Not visible - Sunlit")


    # Visible not sunlit
    #filter_scatter = visibility_satellites_from_exposure["not_visible_not_sunlit"][:,i]

    not_visible_and_not_sunlit     = np.logical_and(~visibility_satellites_from_exposure["is_visible"][:,i],
                                                    ~visibility_satellites_from_exposure["is_sunlit"][:,i])
    filter_scatter = not_visible_and_not_sunlit

    ax.scatter(visibility_satellites_from_exposure["ra"][:,i][filter_scatter],
               visibility_satellites_from_exposure["dec"][:,i][filter_scatter], alpha=0.5,
               marker="o", color="slategray", s=markersize[filter_scatter], label="Not visible or sunlit")



    ax.plot(np.array(list(ra_FOV) + [ra_FOV[0]]), np.array(list(dec_FOV) + [dec_FOV[0]]), alpha=1, color="red", linewidth=2)

################################################################################

def plot_trails_inside_FOV(trails_db, FOV_corners):
    # Plot the trails inside the FOV
    fig, ax = plt.subplots(figsize=(8,8))
    n_satellites = trails_db["n_satellites"]
    for i in range(n_satellites):
        ra = trails_db["ra"][i,:]
        dec = trails_db["dec"][i,:]
        ax.plot(ra, dec, label=trails_db["sat_name"][i])
        ax.scatter(ra, dec)

    # Make the plot line thickness scale with the angular size.
    ax.set_xlim(np.max(FOV_corners[:,0]), np.min(FOV_corners[:,0]))
    ax.set_ylim(np.min(FOV_corners[:,1]), np.max(FOV_corners[:,1]))
    ax.set_xlabel("RA (ICRS)")
    ax.set_ylabel("DEC (ICRS)")



    ax.legend(frameon=False)
    plt.show()

#######################

def plot_trails_vs_FOV(trail_db):
    fig, ax = plt.subplots(figsize=(8, 8))

    for i in range(trail_db["highres_in_FOV_trails"]["N_trails_highres"]):
        ra = trail_db["highres_in_FOV_trails"]["ra"][i,:]
        dec = trail_db["highres_in_FOV_trails"]["dec"][i,:]
        ax.plot(ra, dec, alpha=0.5)
        ra_FOV = trail_db["basic_configuration"]["ra_FOV"]
        dec_FOV = trail_db["basic_configuration"]["dec_FOV"]
        ax.set_xlim([np.nanmax(ra_FOV)+1, np.nanmin(ra_FOV)-1])
        ax.set_ylim([np.nanmin(dec_FOV)-1, np.nanmax(dec_FOV)+1])
        ax.plot(np.array(list(ra_FOV) + [ra_FOV[0]]),
                np.array(list(dec_FOV) + [dec_FOV[0]]),
                alpha=1, color="red", linewidth=2)

    plt.show()

#######################


from itertools import cycle
from shutil import get_terminal_size
from threading import Thread
from time import sleep


class Loader:
    def __init__(self, desc="Loading...", end="Done!", timeout=0.1):
        """
        A loader-like context manager

        Args:
            desc (str, optional): The loader's description. Defaults to "Loading...".
            end (str, optional): Final print. Defaults to "Done!".
            timeout (float, optional): Sleep time between prints. Defaults to 0.1.
        """
        self.desc = desc
        self.end = end
        self.timeout = timeout

        self._thread = Thread(target=self._animate, daemon=True)
        self.steps = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        self.done = False

    def start(self):
        self._thread.start()
        return self

    def _animate(self):
        for c in cycle(self.steps):
            if self.done:
                break
            print(f"\r{self.desc} {c}", flush=True, end="")
            sleep(self.timeout)

    def __enter__(self):
        self.start()

    def stop(self):
        self.done = True
        cols = get_terminal_size((80, 20)).columns
        print("\r" + " " * cols, end="", flush=True)
        print(f"\r{self.end}", flush=True)

    def __exit__(self, exc_type, exc_value, tb):
        # handle exceptions with those variables ^
        self.stop()



#################

def generate_streaked_image_from_sim(trail_db, telescope_name, i):
    # if True:
    from astropy.time import Time
    import astropy.units as u
    from astropy.convolution import convolve_fft

    sims_db = pd.DataFrame(trail_db[telescope_name]["properties_per_sim"])
    trails_db = pd.DataFrame(trail_db[telescope_name]["db_total_trails"])

    trail_db_name = sims_db["trail_list"][i]
    mu_satellite_trails = np.array(trails_db[trails_db["exposure_name"] ==  trail_db_name]["mu"])
    theta_satellite_trails = np.array(trail_db[telescope_name]["brightness_db"]["theta_sat"][trails_db["exposure_name"] ==  trail_db_name])
    dsat_satellite_trails = np.array(trail_db[telescope_name]["brightness_db"]["dsat"][trails_db["exposure_name"] ==  trail_db_name])

    # Make dummy exposure
    outname = trail_db_name.replace(".dat", ".fits")
    trail_db = rs.utils.load_dict(trail_db_name)
    in_FOV_parameters = sp.satellites.find_mjd_entrance_and_exit_FOV(trail_db)
    ntrails_sunlit = np.sum(in_FOV_parameters["sunlit_in_FOV"])
    print("N Sunlit trails: " + str(ntrails_sunlit))
    
    telescope = trail_db['basic_configuration']['telescope']
    telescope.make_dummy_exposure(ra=trail_db["basic_configuration"]["exposure_params"]["ra"],
                                  dec=trail_db["basic_configuration"]["exposure_params"]["dec"],
                                  pa=trail_db["basic_configuration"]["exposure_params"]["pa"], 
                                  outname=outname)

    

    PSF_telescope = telescope.get_PSF()
    
    canvas = fits.open(outname)

    try: 
        pixel_scale = np.abs(canvas[0].header["CD1_1"])*60*60*u.arcsec
    except:
        pixel_scale = np.abs(canvas[0].header["CDELT1"])*60*60*u.arcsec
        

    # Add additional header parameters 
    expstart = Time(trail_db["basic_configuration"]["exposure_params"]["mjd_start"], format='mjd')
    expend = Time(trail_db["basic_configuration"]["exposure_params"]["mjd_end"], format='mjd')
    exptime = (expend-expstart).to("second").value

    canvas[0].header["EXPSTART"] =  trail_db["basic_configuration"]["exposure_params"]["mjd_start"]
    canvas[0].header["EXPTIME"] =  exptime


    #################################################
    # Add the background. First some zodiacal light # 
    #
    #if trail_db["basic_configuration"]["telescope"] == "CSST":
    #    zody_e_rate = rs.detectors.mu2fe(mu=22, instrument=trail_db["basic_configuration"]["instrument"], 
    #                                     filter_name="MCI.F630M", telescope=trail_db["basic_configuration"]["telescope"], 
    #                                     verbose=False)
    #
    # 
    #
    #################################################
    trails_canvas = np.zeros(canvas[0].data.shape)
    trails_id_canvas = np.zeros(canvas[0].data.shape) - 1
    print("exptime = " + str(exptime))

    trails_names = []
    trails_id = []
    
    if not os.path.exists(outname.replace(".fits", "_trails.fits")):
        for i in tqdm(range(len(trail_db["highres_in_FOV_trails"]["sat_name"]))):
            print(trail_db["highres_in_FOV_trails"]["sat_name"][i])
            trail_width = theta_satellite_trails[i] / pixel_scale.to("arcsec").value

            # WARNING! Now all the mock images are in e/s and contain zodiacal light already
            # Need to add the electrons expected from the satellite trail (8.389495508246602 / Conversion factor [ electron sr / (MJy s) ] )
            # Then add photon noise 
            # Then save. 
            
            int_sat_trail_jypx2 = (pixel_scale.to("arcsec").value)**2 * 10**(-0.4*(mu_satellite_trails[i]-8.9)) 
            if np.isnan(int_sat_trail_jypx2): int_sat_trail_jypx2=0
            
            
            print("mu = " + str(mu_satellite_trails[i]))
            print("dsat = " + str(dsat_satellite_trails[i]))        
            print("int = " + str(int_sat_trail_jypx2))
            print("width = " + str(trail_width))

            if int_sat_trail_jypx2 != 0:
                streaked_mask = sp.satellites.generate_trail_mask(filename=outname, ext=0,
                                                   ra_trail=trail_db["highres_in_FOV_trails"]["ra"][i,:],
                                                   dec_trail=trail_db["highres_in_FOV_trails"]["dec"][i,:],
                                                   trail_width=int(np.round(trail_width/2,0)), verbose=False)


                trails_canvas[streaked_mask == 1] = trails_canvas[streaked_mask == 1] + int_sat_trail_jypx2
                trails_id_canvas[streaked_mask == 1] = i

                trails_names.append(trail_db["highres_in_FOV_trails"]["sat_name"][i])
                trails_id.append(i)
                
    else:
        trails_canvas = fits.open(outname.replace(".fits", "_trails.fits"))[1].data

    # Transform trails from jy/px2 to e/s
    mu = -2.5*np.log10(trails_canvas/(pixel_scale.to("arcsec").value)**2) + 8.9
    trails_canvas = telescope.mu2fe(mu=mu)
    
    rs.utils.save_fits(array = [trails_canvas.value, trails_id_canvas], name = outname.replace(".fits", "_trails.fits"), overwrite=True)
    rs.utils.save_fits(array = PSF_telescope, name = outname.replace(".fits", "_psf.fits"), overwrite=True)

    
    ### 
    # Convolve the trails with the PSF of the telescope 
    print("Convolving PSF with trails...")
    os.system("astconvolve -K --hdu=1 --khdu=0 " + outname.replace(".fits", "_trails.fits") + " --kernel=" + outname.replace(".fits", "_psf.fits"))

    #trails_convolved = convolve_fft(trails_canvas, PSF_telescope, allow_huge=True)
    trails_convolved = fits.open(outname.replace(".fits", "_trails_convolved.fits"))[1].data
    print("Done.")
    
    # Then add the result to the image. 
    canvas[0].data = (canvas[0].data + trails_convolved)*exptime

    # Add the photon noise
    print("Adding photon noise")
    try:
        canvas[0].data = np.random.poisson(canvas[0].data)
    except:
        canvas[0].data = np.random.normal(loc=canvas[0].data, scale=np.sqrt(canvas[0].data)) # np.random.poisson(e_arrakihs_with_zody).astype(np.float64)
    print("Done")

    trails_db = pd.DataFrame({"trails_id": trails_id, "trails_names":trails_names}).to_csv(outname.replace(".fits", ".csv"))
    
    canvas.verify("silentfix")
    canvas.writeto(outname, overwrite=True)

    fits.append(outname, trails_id_canvas, canvas[0].header)