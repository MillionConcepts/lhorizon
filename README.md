# **warning: not-even-unstable future branch in process of reorganization. do not use.**

# lhorizon

## introduction

```lhorizon``` offers tools to query the [JPL HORIZONS](https://ssd.jpl.nasa.gov/?horizons) web service for solar system
ephemerides and parse its responses into useful Python objects. It is a fork of 
[astroquery.jplhorizons](https://github.com/astropy/astroquery/tree/master/astroquery/jplhorizons) (originally written 
by Michael Mommert around 2016). I originally wrote it in order to circumvent a bug introduced to jplhorizons by 
serverside changes at JPL that prevents it from correctly parsing queries involving target or observer locations given 
in planetodetic coordinates, and more specifically to provide additional suppport for queries related to arbitrary 
locations on the lunar surface. (I have also submitted a minimal bug fix for this problem to astroquery trunk.) In the 
process I extended it to implement a more efficient parser, add support for fast queries in bulk, and give output in 
pandas dataframes rather than astropy tables (they are very powerful, but too slow for the applications I wrote this 
for).

See [mars_sun_angle.ipynb](lhorizon/examples/mars_sun_angle.ipynb) and 
[galex_vectors.ipynb](lhorizon/examples/galex_vectors.ipynb) for simple examples of usage. More examples and associated 
utilities forthcoming.

## cautions

This module only officially supports observer / ephemeris Horizons queries. Vector support is present and in the process 
of being documented. Element queries may or may not work. 

This software is in early alpha stage. Bugs are expected; please report them. 
