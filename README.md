# lhorizons

## introduction

LHorizons offers tools to query the [JPL HORIZONS](https://ssd.jpl.nasa.gov/?horizons) web service for solar system ephemerides and parse its responses into useful Python objects. It is a fork of [astroquery.jplhorizons](https://github.com/astropy/astroquery/tree/master/astroquery/jplhorizons) (originally written by Michael Mommert around 2016). It was originally written in order to circumvent a bug introduced to jplhorizons by serverside changes at JPL that prevents it from correctly parsing queries involving target or observer locations given in planetodetic coordinates, and more specifically  to provide additional suppport for queries related to arbitrary locations on the lunar surface. (I have also submitted a minimal bug fix for this problem to astroquery trunk.) It also implements a more efficient parser and has some specialized support for fast queries in bulk. It gives output in pandas dataframes rather than astropy tables (they are very powerful, but too slow for the applications I wrote this for). (The astropy dependency is now basically necessary only for astropy.time's MJD handling. I am considering replacing it with something more lightweight if I can find something suitable.)

See [mars_sun_angle.ipynb](src/mars_sun_angle.ipynb) for one simple example of usage. More examples and associated utilities forthcoming.

## cautions

This module only officially supports observer / ephemeris Horizons queries. Vector or element queries may or may not work if you try them; I have no idea. I am unlikely to add support for these unless I ever personally need them. 

This software is in early alpha stage. Bugs are expected; please report them. 
