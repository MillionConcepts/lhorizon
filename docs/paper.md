---
title: '`lhorizon`: geometry and targeting via JPL _Horizons_'
tags:
  - Python
  - planetary science
  - ephemerides
authors:
  - name: Michael St. Clair 
    orcid: 0000-0002-7877-3148 
    affiliation: Million Concepts
affiliations:
 - name: Chief Technical Officer, Million Concepts
   index: 1
date: 15 June 2021
bibliography: paper.bib
---

# Summary

`lhorizon` helps you find where things are in the solar system. It is built around a thick Python wrapper for the Jet 
Propulsion Laboratory (JPL) Solar System Dynamics Group  _Horizons_ service 
[@Giorgini_2015].  _Horizons_ is the only system in the world that provides 
ready-to-go, no-assembly-required access to geometry data for almost every object in the solar system.  Other 
interfaces to _Horizons_ exist, but `lhorizon` is particularly optimized for stability and time-to-value for large 
queries and for processing results with reference to arbitrary topocentric coordinate systems.

`lhorizon` offers a flexible, idiomatic, highly performant pseudo-API to _Horizons_ that returns data as standard 
scientific Python objects (numpy `ndarrays` and `pandas` DataFrames). It provides special handling functions for bulk, 
chunked, and body-listing queries; it also includes an ancillary module, `lhorizon.targeter`, for finding the footprint 
of an observer’s boresight or field of view in topocentric coordinates on target bodies.  

We wrote `lhorizon` in support of a research effort to use Earth-based radio telescopes, including Arecibo and the Very 
Large Array (VLA), to perform heat flow mapping of the Moon. We needed to coregister these data with existing models, 
so we were specifically interested in answering questions like: “in lunar latitude and longitude, where is Arecibo 
pointing?” These facilities were not primarily designed to answer questions about nearby bodies, so their processing 
pipelines did not make lunar maps. Because we were using these instruments in unusual ways, there were many 
uncertainties in the measurements, and we wanted to minimize geometric uncertainty.  _Horizons_ is high-precision and 
has the unique capability to produce corrected positions relative to arbitrary topocentric points, so it was an 
appealing source of ephemerides. 

However, we had millions of data points, widely dispersed across times and observing locations, so we needed a highly 
performant programmatic interface. We were pleased to discover that the _astroquery_ [@Ginsburg_2019] project included 
a module for querying _Horizons_ called  `jplhorizons`. This module, written primarily by Michael Mommert around 2016, 
is tightly integrated with _astroquery_. It uses _astroquery_’s session handlers and parsing system, and returns 
results in _astropy_ tables. Unfortunately, we discovered that `jplhorizons` had experienced bitrot due to server-side 
changes in _Horizons_ that broke functionality we specifically needed. We implemented workarounds, but discovered that 
the performance of `jplhorizons` was inadequate for our use case. (We have since submitted  minimal workarounds for 
the `jplhorizons` issues to _astroquery_.) _astroquery_’s parsers and _astropy_ tables are powerful, but this power 
comes at a performance cost. The cost is irrelevant for many applications, but quite relevant for use cases with tens 
to hundreds of thousands of data points per analysis. We wrote an entirely new response parser using only builtins, 
_numpy_, and _pandas_, resulting in performance improvements of 10-100x. `lhorizon`’s other features have grown from 
there.

# Statement of Need

JPL is the most authoritative producer of solar system ephemerides. Its geometry products are essential elements of 
academic and industrial work in planetary science, astronomy, geosciences, and many other fields. They are useful for 
any application that makes use of artificial satellites or needs to know about the position of solar system bodies 
(even “simple” quantities like the solar angle at an arbitrary Earth location). Their value as public resources is 
incalculable. Unfortunately, they are not always easy to use.

JPL offers two automated interfaces to its geometry products: the SPICE toolkit [@naif_spice_data] (developed by NAIF, 
NASA's Navigation and Ancillary Information Facility) and _Horizons_. SPICE is very powerful but has an extremely high 
barrier to entry. Using SPICE requires not only acquiring and configuring software, but also collecting the appropriate 
data files, called “kernels.” Not counting automatically-generated kernels for minor bodies like asteroids, there are 
tens of thousands of kernels; counting them, there are tens of millions. There is no central repository for kernels -- 
NAIF’s website comes closest, but crucial kernels are scattered across hundreds of other Planetary 
Data System (PDS) archives.  Making kernels work together is challenging and requires scripting in a domain-specific 
markup language. The SPICE “required reading” [@spice_required_reading] is dozens of chapters and hundreds of pages 
long. SPICE is difficult for planetary scientists and specialized engineers, let alone nonspecialists who need quick 
access to geometry data. SPICE implementations exist in several languages, and excellent wrappers exist (notably the 
idiomatic Python wrapper _SpiceyPy_ [@Annex_2020]), but they do not solve the conceptual and data access difficulties 
of SPICE.

_Horizons_ is, by comparison, user-friendly. While it does not implement all of the utilities of the SPICE toolkit, 
it covers more sites and offers flexibility SPICE does not.  _Horizons_ offers several interface methods: interactive 
web, telnet, email, and web CGI. A wrapper that builds URLs for the CGI interface and parses returned text is an 
obvious architecture for a _Horizons_ pseudo-API. Because bulk queries are not easy to compose and parsing the returned 
text is not straightforward, this goes a long way towards improving access to solar system geometry data. An official 
REST API to _Horizons_ is forthcoming but not yet available, and the details of its capabilities have not been publicly 
released [@Giorgini_2020]. It is likely that high-level wrappers for this API will be useful, and we plan to update 
`lhorizon` to fill this role.

# Other Related Work

Many wrappers, helpers, and interfaces for _Horizons_ have been developed, though most are incomplete, defunct, or 
encapsulated in other applications. They include:

* _py-NASA-horizons_, a vectors query wrapper; abandoned since 2013 and no longer functional [@py_nasa_horizons_repo]
* Mihok’s _HORIZON-JPL_, a REST API; abandoned since 2014 and no longer functional [@horizon_jpl_repo]
* Fejes’ _JS-HORIZONS_, a js library focused on physical rather than geometry data [@js_horizons_repo]

More broadly, libraries like `astropy.coordinates` [@astropy_2018] and _Skyfield_ [@skyfield_2019] that perform 
calculations on JPL ephemerides are similar in application to `lhorizon` and should be considered by potential users.

# Acknowledgements

This work was supported by a NASA Solar System Workings grant … blah blah blah 
