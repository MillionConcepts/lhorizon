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

This is a prerelease of lhorizons 1.0, which completes and rationalizes the interface, adds a submodule for figuring 
out, in target-body-centric coordinates, what part of a solar system body something is pointing at, and adds reasonably 
complete test coverage.

## cautions

This module only officially supports observer / ephemeris and vector Horizons queries. Osculating elements queries are 
not officially supported and may behave in unexpected ways.

Some functions may produce warnings and / or offsets by a handful of seconds for dates prior to 1960.