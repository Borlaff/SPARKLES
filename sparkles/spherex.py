import os
import glob
import numpy as np
import rosalia as rs
from astropy.io import fits

def repair_spherex(spherex_name):
    import astropy.wcs as astropy_wcs
    spherex_fits = fits.open(spherex_name)
    xsize = spherex_fits[1].header["NAXIS1"]
    ysize = spherex_fits[1].header["NAXIS2"]
    ra_cen = spherex_fits[1].header["CRVAL1"]
    dec_cen = spherex_fits[1].header["CRVAL2"]
    w = astropy_wcs.WCS(naxis=2)

    w.wcs.crpix = [spherex_fits[1].header["CRPIX1"], spherex_fits[1].header["CRPIX2"]] # What is the center pixel of the XY grid.
    w.wcs.crval = [spherex_fits[1].header["CRVAL1"], spherex_fits[1].header["CRVAL2"]] # what is the galactic coordinate of that pixel.
    # w.wcs.cdelt = [spherex_fits[1].header["CTYPE1"] # what is the pixel scale in lon, lat.
    w.wcs.ctype = [spherex_fits[1].header["CTYPE1"],
                   spherex_fits[1].header["CTYPE2"]]     # you would have to determine if this is in fact a tangential projection.
    w.wcs.pc = [[spherex_fits[1].header["PC1_1"],spherex_fits[1].header["PC1_2"]],
        [spherex_fits[1].header["PC2_1"],spherex_fits[1].header["PC2_2"]]]


    # write the HDU object WITH THE HEADER
    header = w.to_header()

    # Remove Zodi
    spherex_fits[1].data = spherex_fits[1].data - spherex_fits["ZODI"].data


    #header = create_custom_wcs(crpix=[x_size/2, y_size/2], crval=[ra_cen, dec_cen], cdelt=[pixscale, pixscale])
    rs.utils.save_fits(array=spherex_fits[1].data,
                       name=spherex_name.replace(".fits","_rep.fits"),
                       header=header)

    return(spherex_name.replace(".fits","_rep.fits"))


def make_spherex_mosaic(spherex_exp_folder):
    spherex_1D1 = glob.glob(spherex_exp_folder + "/level2_*_[0-9]D1_*[0-9].fits")[0]
    spherex_1D2 = glob.glob(spherex_exp_folder + "/level2_*_[0-9]D2_*[0-9].fits")[0]
    spherex_1D3 = glob.glob(spherex_exp_folder + "/level2_*_[0-9]D3_*[0-9].fits")[0]
    spherex_1D4 = glob.glob(spherex_exp_folder + "/level2_*_[0-9]D4_*[0-9].fits")[0]
    spherex_1D5 = glob.glob(spherex_exp_folder + "/level2_*_[0-9]D5_*[0-9].fits")[0]
    spherex_1D6 = glob.glob(spherex_exp_folder + "/level2_*_[0-9]D6_*[0-9].fits")[0]

    spherex_exp_list = [spherex_1D1, spherex_1D2, spherex_1D3, spherex_1D4, spherex_1D5, spherex_1D6]
    #for i in range(len(spherex_exp_list)):
    #    repair_spherex(spherex_exp_list[i])

    frame_size = int(2040)
    pad = int(230)
    canvas = np.zeros((frame_size*2+pad, frame_size*3+pad*2)) * np.nan

    spherex_1D1_image = fits.open(spherex_1D1)[1].data - fits.open(spherex_1D1)["ZODI"].data
    spherex_1D2_image = fits.open(spherex_1D2)[1].data - fits.open(spherex_1D2)["ZODI"].data
    spherex_1D3_image = fits.open(spherex_1D3)[1].data - fits.open(spherex_1D3)["ZODI"].data
    spherex_1D4_image = fits.open(spherex_1D4)[1].data - fits.open(spherex_1D4)["ZODI"].data
    spherex_1D5_image = fits.open(spherex_1D5)[1].data - fits.open(spherex_1D5)["ZODI"].data
    spherex_1D6_image = fits.open(spherex_1D6)[1].data - fits.open(spherex_1D6)["ZODI"].data

    canvas[0:frame_size, 0:frame_size] = spherex_1D1_image
    canvas[0:frame_size, frame_size+pad:frame_size*2+pad] = spherex_1D2_image
    canvas[0:frame_size, frame_size*2+2*pad:frame_size*3+2*pad] = spherex_1D3_image

    canvas[frame_size+pad:2*frame_size+2*pad, 0:frame_size] = spherex_1D4_image
    canvas[frame_size+pad:2*frame_size+2*pad, frame_size+pad:frame_size*2+pad] = spherex_1D5_image
    canvas[frame_size+pad:2*frame_size+2*pad, frame_size*2+2*pad:frame_size*3+2*pad] = spherex_1D6_image

    outname = spherex_exp_folder + "/" + spherex_exp_folder.split("/")[-1] + ".fits"
    rs.utils.save_fits(array=canvas,
                       name=outname)

    return(outname)



def scan_spherex_script(sh_name):

    lines = open(sh_name).read().split('\n')
    n_lines = len(lines)
    n_images = n_lines - 78 - 1

    header_downloader_program = '\n'.join(lines[0:78])

    from tqdm import tqdm

    obsid = []
    detector = []
    image_lines = []
    download_lines = []
    #print(n_images)
    for i in tqdm(range(n_images)):
        download_line = lines[78+i]

        image_line = download_line.split(" ")[1]

        if "cutout" in image_line:
            continue

        download_lines.append(header_downloader_program + " " + download_line)
        #print(len(image_line))
        #return(image_line)
        #print(image_line.split("/"))
        image_lines.append(image_line)
        #print(image_line.split("/"))
        obsid.append(image_line.split("/")[11][7:24])
        detector.append(image_line.split("/")[10])

    import pandas as pd
    db = pd.DataFrame({"download_lines":download_lines, "image_lines": image_lines, "obsid": obsid, "detector": detector})

    # Now we have a database with the images and the OBSIDs.
    unique_obsid_list = sorted(list(set(db["obsid"]))) # This is the list without the duplicates.

    # Find how many OBSIDs have 6 images.
    for obsid in unique_obsid_list:
        n_images_in_obsid = len(db[db["obsid"] == obsid])
        if n_images_in_obsid != 6: # If there are not 6 images per obsid, drop them.
            db = db.drop(np.where(db["obsid"] == obsid)[0])
            db = db.reset_index(drop=True)
            #print("Drop! N=" + str(n_images_in_obsid))

    db = db.sort_values(by=['obsid'])
    db = db.reset_index(drop=True)
    return(db)

    #for i in tqdm(range(n_images)):
    #    os.system(header_downloader_program + '\n' + lines[78+i])



def make_n_open_spherex(db, download_only=False, only_one_obsid=False):

    import os
    cwd = os.getcwd()
    unique_obsid_list = sorted(list(set(db["obsid"]))) # This is the list without the duplicates.
    for obsid in unique_obsid_list:
        if only_one_obsid is not False:
            if only_one_obsid != obsid:
                continue
            else:
                print("Selected obsid found! Downloading " + obsid)

        try:
            # If we already analyzed this, move on.
            if os.path.exists(obsid + "/completed.flag"):
                print("OBSID: " + obsid + " completed!")
                continue
            # else, analyze it.
            spherex_exp_folder = os.path.abspath(obsid)

            db_obsid = db[db["obsid"] == obsid]
            db_obsid = db_obsid.sort_values(by=['detector'])
            print(db_obsid)
            if not os.path.exists(spherex_exp_folder + "/downloaded.flag"):
                from tqdm import tqdm
                for i in tqdm(range(6)):
                    rs.utils.execute_cmd(db_obsid["download_lines"].iloc[i])
                    os.system("mkdir " + obsid)
                    os.system("mv SPHERExLVFSurveyData*/*.fits " + obsid)
                    os.system("rm -r SPHERExLVFSurveyData*")

                os.system("echo 'OK' > " + obsid + "/downloaded.flag")
            if download_only:
                continue

            spherex_mosaic = make_spherex_mosaic(spherex_exp_folder = spherex_exp_folder)
            print(spherex_mosaic)
            os.chdir(spherex_exp_folder)
            cmd = "/Users/aborlaff/GRID/SAOImageDS9.app/Contents/MacOS/ds9 "+ spherex_mosaic + " " +\
                  "-geometry 2300x1200 "+\
                  "-cmap turbo -lock frame image -mode region -lock scalelimits yes -lock colorbar yes "+\
                  "-scale log -scale mode zscale -region shape line -zoom to fit "
            # print(cmd)
            os.system(cmd)
            os.system("echo 'OK' > completed.flag")
            os.chdir(cwd)
        except:
            print("Something happened with " + spherex_exp_folder)
            #os.system("rm " + obsid + "/downloaded.flag")
            #os.system("rm " + obsid + "/completed.flag")
            print("Jumping!")
