import os
import setuptools
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "SPARKLES",
    version = "0.1.0",
    author = "Alejandro S. Borlaff",
    author_email = "a.s.borlaff@nasa.gov",
    description = ("A software to find satellite trails in Low Earth Orbit telescopes"),
    license = "BSD",
    keywords = "CPS / Satellite trails / Mega-constellations / LEO",
    url = "https://github.com/Borlaff/Sparkles_I",
    packages=setuptools.find_packages(where=".", exclude=()),
    package_data={'': ['*.mplstyle', '*.csv', '*.txt']},
    install_requires=['multiprocess', 'bottleneck', 'xmltodict',
                      'romanisim @ git+https://github.com/spacetelescope/romanisim.git', 'asdf',
                      'cartopy',
                      'healpy', 'regions', 'LSSTDESC.Coord', 'numpy==1.26.4',
                      'galsim', 'skyfield @ git+https://github.com/Borlaff/python-skyfield.git', 'tqdm', 'pybind11>=2.12', 'pandas',
                      'requests', 'numexpr', 'astroquery', 'scipy', 'matplotlib',
                      'astropy_healpix', 'pytest', 'celluloid', 'ipython', 'pysynphot',
                      'sphericalpolygon'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
