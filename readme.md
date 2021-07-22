# lhorizon

[![CI](https://img.shields.io/github/workflow/status/MillionConcepts/lhorizon/CI?logo=github)](https://github.com/MillionConcepts/lhorizon/actions)
[![codecov](https://codecov.io/gh/MillionConcepts/lhorizon/branch/main/graph/badge.svg)](https://codecov.io/gh/MillionConcepts/lhorizon)

## introduction

### purpose

`lhorizon` helps you find where things are in the solar system. It is built around a thick Python wrapper for the 
Jet Propulsion Laboratory (JPL) [Horizons](https://ssd.jpl.nasa.gov/?horizons) service. _Horizons_, provided by JPL's
Solar System Dynamics Group (SSD), is the only service in the world that offers no-assembly-required high-precision 
geometry data for almost every known body in the solar system. `lhorizon` offers tools to query _Horizons_ for data, 
parse its responses into useful Python objects, and smoothly incorporate them into bulk calculation and transformation 
workflows.

### origin

`lhorizon` began as a fork of [astroquery.jplhorizons](https://github.com/astropy/astroquery/tree/master/astroquery/jplhorizons) 
(originally written by Michael Mommert around 2016). I wrote it in order to circumvent a bug introduced to `jplhorizons` by 
serverside changes at JPL that prevented it from correctly parsing queries involving target or observer locations given 
in planetodetic coordinates, and more specifically to provide suppport for queries related to arbitrary locations on 
the lunar surface. In the process I extended it to implement a more efficient parser, add support for fast queries in 
bulk, and remove the use of `astroquery` and `astropy` features (in particular, `astropy` tables are very powerful, but 
too slow for the applications I wrote this for). At some point, I realized that a fast, standalone interface to 
Horizons might be useful to the community at large and decided to polish it into a general-use package.

### pronunciation

along the lines of "l'horizon" or "low-ree-zahn;" like "the horizon" in French, or the famous Palm Springs Desert 
Modern hotel (an easy drive from Pasadena).

## installation

We recommend that you use the `conda` package manager to control your Python environment for this library. (If you 
really don't want to use `conda`, the `setup.py` script in the root directory will _probably_ fetch the dependencies
you need from PyPi, but we do not test or officially support use of non-`conda` environments for `lhorizon`.)

If you're already equipped with `conda`, you can create an environment (named "lhorizon") for this package by running: 
`conda env create -f environment.yml`. (You could instead add its dependencies to an existing environment by running 
`conda env update -n existing_env -f environment.yml`). Then, if you'd like`lhorizon` installed as a site package in 
this environment, activate the environment and run `python setup.py install`. 

If you're new to `conda` or Python environment management in general, please take a look at the 
[conda installation guide](docs/conda_installation_guide.md). 
 
### dependencies and requirements

All explicit dependencies are listed in the environment.yml file in the root directory. Note that `lhorizon` requires 
Python >= 3.9; there are no plans to implement support for older Python versions. Some dependencies are optional and
could be omitted in restrictive install environments. Specifically: 
* `jupyter` is only required to run examples
* `pytest` and `pytest-mock` are only required to run tests
* `spiceypy` and `sympy` are only required for `lhorizon.target` and related tests and examples

Some features of `lhorizon` can be used without internet connectivity, but much of the library requires you to be able
to dial out to the jpl.nasa.gov domain.

`lhorizon` should function in any OS supported by `conda`. The baseline system requirements are fairly light. 
Counting dependencies and a base miniconda environment,`lhorizon` takes up about 2.6 GB of space. The respository itself
is ~75 MB, almost all of which could be pruned in a restrictive install environment that did not require full `git` 
history and the included SPICE kernels. Many uses of `lhorizon` are not resource-intensive and will run comfortably on 
a small machine like an AWS EC2 t3.micro instance. Conversely, resource requirements can scale as high as you like if 
you are planning to process extremely large sets of geometry data.

## usage

The Jupyter Notebooks provided in the [lhorizon/examples](lhorizon/examples) directory are the best quick-start guides 
to usage. See the [API reference](docs/api.md) for more details on the package's behavior.

## changelog

* 2021-06-21: Full 1.0 release. Extensive changes from older versions:
    * completes and rationalizes interface 
    * concatenates and standardizes target submodule
    * reasonably complete test coverage and documentation
    * somewhat more extensive example Notebooks

## cautions / known errors

* do not execute multiple queries to _Horizons_ in parallel using multiprocessing or other 
  techniques, manual or programmatic. This is a requirement of _Horizons_, not `lhorizon`: JPL has not designed 
  _Horizons_ to support parallel queries, and will tightly throttle requesters who attempt them. Look at functions in
  `lhorizon.handlers` for polite
  alternatives.
* `lhorizon` only officially supports observer / ephemeris and vector Horizons queries. Osculating elements queries are 
  not officially supported and may behave in unexpected ways. Support for elements queries is planned.

## support

To report bugs, make feature requests, or get support for case-specific uses of `lhorizon`, please file issues in this 
GitHub repository. For broader questions about `lhorizon` usage, please email mstclair@millionconcepts.com.

## contributions

We welcome contributions to `lhorizon`. They may simply be submitted as pull requests to this repository, although if 
you have ideas for large new features or major architectural changes, we encourage you to discuss them with us first;
please email mstclair@millionconcepts.com

## acknowledgements

The development of `lhorizon` has been supported partly by a NASA Solar System Observations grant, "Remote Measurement 
of Lunar Heat Flow From Earth Based Radio Astronomy" (PI Matthew Siegler).

## licensing

You can do almost anything with this software that you like, subject only to the extremely permissive terms of the [BSD 
3-Clause License](LICENSE).
