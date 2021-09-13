---
title: '`lhorizon`: geometry and targeting via JPL _Horizons_'
tags:
  - Python
  - planetary science
  - ephemerides
authors:
  - name: Michael St. Clair 
    orcid: 0000-0002-7877-3148 
    affiliation: 1
  - name: Matthew Siegler
    affiliation: 2
affiliations:
 - name: Chief Technical Officer, Million Concepts
   index: 1
 - name: Research Scientist, Planetary Science Institute
   index: 2
date: 25 June 2021
bibliography: paper.bib
---

# Summary

`lhorizon` helps you locate natural and artificial bodies and features in the
Solar System. It is built around a thick Python wrapper for the Jet Propulsion
Laboratory (JPL) Solar System Dynamics Group  _Horizons_ service
[@Giorgini_2015]. _Horizons_ is one of the only providers of ready-to-go,
no-assembly-required geometry data for almost every object in the
Solar System.  Other interfaces to _Horizons_ exist (see 'Other Related Work'
below for several examples), but `lhorizon` is particularly optimized for
stability and time-to-value for large queries and for processing results with
reference to arbitrary topocentric coordinate systems.

`lhorizon` offers a flexible, idiomatic, highly performant pseudo-API
to _Horizons_ that returns data as standard scientific Python objects (_NumPy_, @harris2020array `ndarrays` and _pandas_ DataFrames, @reback2020pandas). It
provides special handling functions for bulk, chunked, and body-listing
queries; it also includes an ancillary module, `lhorizon.targeter`, for finding
the footprint of an observer's boresight or field of view in topocentric
coordinates on target bodies. 

We wrote `lhorizon` in support of a research effort to use Earth-based radio
telescopes, including Arecibo and the Very Large Array (VLA), to perform heat
flow mapping of the Moon. We needed to coregister these data with existing
models, so we were specifically interested in answering questions like: “in
lunar latitude and longitude, where is Arecibo pointing?”. As Earth-based radio
telescopes are not primarily designed to answer questions about nearby bodies,
their processing pipelines aren't readily suited for goals like producing 
lunar maps. Using these instruments in unusual ways also resulted in
additional measurement uncertainties (_e.g._, geometric uncertainty) that we
wanted to minimize.  _Horizons_ was an appealing data source due to its high 
precision (up to microarcseconds for Moon positions relative to Earth 
in the relevant time frame, well above the limits of precision introduced by our 
other constraints) and its ability to deliver tables of positions relative to 
arbitrary topocentric points, natively referenced to the geodetic datums of
their host bodies (_e.g._, WGS84 for Earth), with robust corrections for light-time, 
gravitational delays, and aberration.

However, with millions of data points widely dispersed across times and
observing locations, we needed a highly performant programmatic interface to
achieve our task. We were pleased to discover that the _astroquery_
[@Ginsburg_2019] project included a module for querying _Horizons_ called
`jplhorizons`. This module, written primarily by Michael Mommert around 2016,
is tightly integrated with _astroquery_. It uses _astroquery_'s session
handlers and parsing system, and returns results in _astropy_ tables.
Unfortunately, we discovered that due to changes in the behavior of the
Horizons CGI endpoint, parts of `jplhorizons` that probably worked very well in
2016 no longer worked in 2019. We implemented workarounds, but discovered that
the performance of `jplhorizons` was inadequate for our use
case. _astroquery_'s parsers and _astropy_ tables are powerful, but this power
comes at a performance cost. The cost is irrelevant for many applications but
quite relevant for use cases with tens to hundreds of thousands of data points
per analysis. We wrote an entirely new response parser using only builtins, 
_NumPy_, and _pandas_, resulting in performance improvements of a factor of 10-100x.
(Since then, there have been significant backend improvements in _astropy_ 
tables, and `lhorizon` typically offers only about 10x speed and 50% memory 
reduction over the latest version of `jplhorizons`. Benchmark notebooks are available 
in our GitHub repository.)

We submitted minimal workarounds for the API issues to _astroquery_, but the
changes we made in our fork were too extensive to be folded into 
_astroquery_ via a PR -- especially because removing _astropy_ objects and idioms was one of our major design goals. We named this fork `lhorizon` and have continued developing it as a distinct project. 

# Statement of Need

JPL's geometry products are essential elements of academic and industrial 
projects related to planetary science, astronomy, geosciences, and many other 
fields. They are useful for any application involving artificial satellites 
(from data analysis to mission design) or the position of Solar System bodies 
(even “simple” quantities like solar angles at arbitrary Earth locations). 
They are thus invaluable public resources. Unfortunately, they are not always 
easy to use.

JPL offers two automated interfaces to its geometry products: the SPICE toolkit
[@naif_spice_data], developed by NAIF, NASA's Navigation and Ancillary
Information Facility, and _Horizons_. SPICE is very powerful but presents a
high barrier to entry. Using SPICE requires not only acquiring and configuring
software, but also collecting the appropriate data files, called “kernels”.
There is no central repository for kernels -- NAIF's website comes closest, but
crucial kernels are scattered across hundreds of other Planetary Data System
(PDS) archives. Loading a consistent kernel pool is challenging and requires
scripting in a domain-specific markup language. Learning the SPICE toolkit can
be challenging for both specialists and for general users who need quick access
to geometry data. SPICE implementations exist in several languages, and
excellent wrappers exist (notably the idiomatic Python wrapper _SpiceyPy_
[@Annex_2020]), but they do not solve the conceptual and data access
difficulties of SPICE.

_Horizons_ is, by comparison, user-friendly. While it does not implement all of
the utilities of the SPICE toolkit, it offers flexibility SPICE does not and
contains state information for many sites and bodies for which no SPICE kernels exist.
_Horizons_ offers several interface methods: interactive web, telnet, email, and
web CGI. Because bulk queries to the CGI endpoint are not easy to compose and parsing its responses
is not straightforward, simply building URLs for this interface and  
parsing the returned text significantly improves access to Solar System geometry data --
`lhorizon` does that and more. Some likely use cases include calculating solar angles on Mars,
determining the precise distance from the Solar System barycenter to an artificial satellite, 
and finding selenodetic coordinates for pixels within the field of view of a terrestrial telescope pointed
at the Moon. We include Jupyter Notebooks in our repository that illustrate these uses.

An official REST API to _Horizons_ is forthcoming but not yet available, and the details of its capabilities 
have not been publicly released [@Giorgini_2020]. It is likely that high-level wrappers for this API will be useful, 
and we plan to update `lhorizon` to fill this role.

# Other Related Work

Many wrappers, helpers, and interfaces for _Horizons_ have been developed, 
though most are incomplete, defunct, or encapsulated in other applications. 
They include:

* _py-NASA-horizons_, a vectors query wrapper; abandoned since 2013 and no longer functional [@py_nasa_horizons_repo].
* Mihok's _HORIZON-JPL_, a REST API; abandoned since 2014 and no longer functional [@horizon_jpl_repo].
* Fejes' _JS-HORIZONS_, a JavaScript library focused on physical rather than geometry data [@js_horizons_repo].

More broadly, libraries like `astropy.coordinates` [@astropy_2018] and 
_Skyfield_ [@skyfield_2019] that perform calculations based on JPL 
ephemerides are similar in application to `lhorizon` and should be considered 
by potential users.

This application space also includes lower-level ephemeris toolkits other 
than SPICE that may be preferable for some applications. For instance, the 
CALCEPH [@calceph] library, developed by the IMCCE of the Observatoire de Paris, offers 
interfaces to many programming languages and is compatible with a wider 
variety of ephemeris formats than SPICE.


# Acknowledgements

This work was supported by a NASA Solar System Workings grant, #NNX16AQ10G, and
a NASA Solar System Observations grant, #NNX17AF12G.

# References
