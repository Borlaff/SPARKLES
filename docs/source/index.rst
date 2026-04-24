.. SPARKLES documentation master file, created by
   sphinx-quickstart on Mon Apr 20 15:16:03 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Project SPARKLES
======================

|pic1| |pic2| |pic3| |pic4|

.. |pic1| image:: ../../images/NASA_worm.png
   :width: 24%

.. |pic2| image:: ../../images/Baeri.png
   :width: 24%

.. |pic3| image:: ../../images/sparkles_logo_2.png
   :width: 24%

.. |pic4| image:: ../../images/cps-logo.png
   :width: 24%

**SPARKLES** is a NASA Ames Research Center project that provides forecasts and models of satellite trail contamination for space-based astronomy. The documentation presented here serves as a living article following the publication of our research in *Nature* `(Borlaff, Marcum, Howell 2025) <https://www.nature.com/articles/s41586-025-09759-5>`_. As new satellite constellations are announced, launched, and adapted, this repository will gather upgrades to the original paper, improvements in the methodology, and resources for the community to understand and mitigate the impact of satellite megaconstellations on space telescopes.

Overcrowding of Low Earth Orbit (LEO) by artificial satellite constellations is `increasingly threatening the quality of astronomical observations from both ground and space <https://cps.iau.org/resources/public-materials/>`_. Their reflected light and direct emissions can create bright trails in the images captured by telescopes across the whole electromagnetic spectrum when passing through their fields of view. These *satellite trails* outshine the dim emissions from natural sources, such as galaxies, stars, asteroids and even exoplanets. 

.. figure:: ../../images/cover_nature_compressed.jpg
   :width: 100%

The **SPARKLES** project started at NASA Ames Research Center aiming to answer the following question: *How frequent are satellite trails will be in the future for space telescopes?*. In `(Borlaff, Marcum, Howell 2025)
<https://www.nature.com/articles/s41586-025-09759-5>`_ we discovered that if the current plans for satellite constellations are implemented, almost every single image from current and future space telescopes (96%) will show artificial light contamination from satellites, and the levels and extent of the pollution could greatly increase in the next decades. Artificial satellite trails would have a significant impact on the potential scientific return of some of these missions, as well as on the public's access to the wonders of the Universe.

In its current stage (April 2026), the *SPARKLES* project aims to provide a long-term repository of accurate forecasts of satellite trail frequencies on various space-based observatories, enabling astronomers, industrial partners, and government agencies to plan more effectively and advocate for responsible satellite constellation management.

.. note::

   Space is hard, and this project is under active development. **The satellite trail levels predicted here are not intended to be by any means a representation of the capabilities of any specific mission, but an approximate representation of the impact of satellite constellations for space based astronomy as a whole**. Satellites may be canceled or proposed, telescopes might adapt, we might find better ways to observe. The future is uncertain, and the models are not perfect.
    
   But satellite trails are increasingly more frequent in the science products from telescopes both on the ground and in space. As conditions change, we keep pushing everyday to make our models better. We will be including software, databases, and tutorials in the very near future. If you are part of a mission and would like to estimate the artificial satellite trail contamination rate, contact us! **SPARKLES** is a NASA Ames Research Center Project that needs your help to improve! If you find a useful capability that could be added, a problem to be resolved, or any other idea, `email us <a.s.borlaff@nasa.gov>`_.

The forecasts are updated based on the latest satellite proposals to the ITU and FCC, as they become available and are implemented in `Jonathan McDowell's Space Report <https://planet4589.org/>`_. The plot below illustrates the latest predictions of the average number of satellite trails per exposure of the selected space telescopes.

Latest Satellite Trail Forecast - April 16th, 2026
===================================================

.. figure:: ../../MODELS/latest_ntrails_vs_nsats.png
   :width: 100%
   :alt: Mean number of satellite trails per exposure as a function of satellite population
   
   **Figure 1**: Mean number of satellite trails per exposure as a function of the population of artificial satellites in Earth orbit.

Changelog
--------------

- Satellite debris with available cross-sectional area estimations *Planet4589* Satellite filtering list: (https://planet4589.org/space/supporting/asb/asb.html) are now included in the models. We select the main bus diameter times span of longest appendage as the maximum cross-sectional area of the satellite in face-on orientation (*AREA 2*). Catalogued objects (Space-track: (https://www.space-track.org/) with a) sizes smaller than <1 mm2, b) not orbiting Earth, and c) flagged as *DOWN* (de-orbited), are removed from the simulation. 


- Satellites with known dimensions (i.e., SpaceX Starlink Gen 1, 2, and xAI orbital data centers) have now a fixed area in the simulations. Those satellites for which their dimensions are unknown retain the original size distribution assumed in the original paper (1 -- 125 m2).


- The models include the latest FCC/ITU announcements (March 2026) from CTC1 and CTC2 (96,714 satellites each), and the SpaceX Orbital Data Centers (SXODC, 1,000,000 satellites). The total number of satellites considered (included existing debris, dead, and active satellites, and proposed constellations) adds up to 1,843,084. *Planet4589*: Satellite Constellation list: (https://planet4589.org/space/con/conlist.html)


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   forecast
   observations
   methods
   publications
   resources
   whoarewe


Disclaimer
--------------

This project is a NASA Ames Research Center effort to provide forecasts of satellite trail contamination for space-based astronomy. The forecasts are based on the best available data and models at the time of publication, but they are subject to change as new information becomes available. Our purpose is to support astronomical missions by providing the best forecast possible about artificial light pollution, and cannot be considered an evaluation of the capabilities or success of any of these missions. We love telescopes, astronomy, and space science, and we do our best to support it.  

The authors thank Meredith Rawls, Leslie Sage, Paul Woods, Casiana Muñoz Tuñón, Aaron Mckinnon, Nahum Alem, Rocio Velasco Poblaciones, John E. Beckman, Brendan P. Crill, and the SPHEREx team for their support and careful reviews. The authors acknowledge the support of the International Astronomical Union (IAU) Centre for the Protection of the Dark and Quiet Sky (CPS). The Centre coordinates collaborative and multidisciplinary international efforts from institutions and individuals working across multiple geographic areas, seeks to raise awareness, and mitigate the negative impact of satellite constellations on ground-based optical, infrared and radio astronomy observations as well as on humanity’s enjoyment of the night sky. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the NASA, BAERI, IAU, NSF NOIRLab, SKAO, ESO, or any host or member institution of the IAU/CPS. The use of NASA, BAERI, and the IAU/CPS logos only represent the affiliation of the project members and associates and does not imply, endorse, or inform about the official views of any government agency.