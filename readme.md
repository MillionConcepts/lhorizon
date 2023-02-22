# lhorizon

[![CI](https://img.shields.io/github/actions/workflow/status/MillionConcepts/lhorizon/ubuntu_tests.yaml)](https://github.com/MillionConcepts/lhorizon/actions/workflows/ubuntu_tests.yaml)
[![codecov](https://codecov.io/gh/MillionConcepts/lhorizon/branch/main/graph/badge.svg)](https://codecov.io/gh/MillionConcepts/lhorizon)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/MillionConcepts/lhorizon/main?filepath=examples)
[![DOI](https://joss.theoj.org/papers/10.21105/joss.03495/status.svg)](https://doi.org/10.21105/joss.03495)
## introduction

### purpose

`lhorizon` helps you find things in the Solar System. It is built around a thick Python wrapper for the 
Jet Propulsion Laboratory (JPL) [Horizons](https://ssd.jpl.nasa.gov/?horizons) service. _Horizons_, provided by JPL's
Solar System Dynamics Group (SSD), is one of the only sources in the world that offers no-assembly-required 
high-precision data on the relative positions and velocities of almost every known body in the Solar System. 
`lhorizon` offers tools to query _Horizons_ for data, parse its responses into useful Python objects, and smoothly 
incorporate them into bulk calculation and transformation workflows.

If you would a quick overview of major package functionality, 
[you can try these example Notebooks on Binder.](https://mybinder.org/v2/gh/MillionConcepts/lhorizon/main?filepath=examples)

### origin

`lhorizon` began as a fork of [astroquery.jplhorizons](https://github.com/astropy/astroquery/tree/master/astroquery/jplhorizons) 
(originally written by Michael Mommert around 2016). We wrote it in order to circumvent a bug introduced to `jplhorizons` by 
serverside changes at JPL that prevented it from correctly parsing queries involving target or observer locations given 
in planetodetic coordinates, and more specifically to provide suppport for queries related to arbitrary locations on 
the lunar surface. In the process, we extended it to implement a more efficient parser, add support for fast queries in 
bulk, and remove the use of `astroquery` and `astropy` features (for both performance and API compatibility reasons). 
At some point, we realized that a fast, standalone interface to Horizons might be useful to the community at large and 
decided to polish it into a general-use package.

### pronunciation

along the lines of "l'horizon" or "low-ree-zahn;" like "the horizon" in French, or the famous Palm Springs Desert 
Modern hotel (an easy drive from Pasadena).

## installation

### automated

`lhorizon` is available on `conda-forge`, and we recommend installing it using the `conda` package manager: 
`conda install -c conda-forge lhorizon`.

We do not test or officially support the use of non-`conda` environments for `lhorizon`, but it can also be installed from PyPi: 
`pip install lhorizon`, or, if you'd like all the bells and whistles, `pip install lhorizon[target, examples, tests]`.

### manual

If you'd like to install `lhorizon` by hand, we again recommend that you use `conda` to assemble a Python environment.

If you're already equipped with `conda`, you can create an environment (named "lhorizon") for this package by cloning this repository
and running: `conda env create -f environment.yml` from the repository root directory. 
(You could instead add its dependencies to an existing environment by running `conda env update -n existing_env -f environment.yml`). 
Then, if you'd like`lhorizon` installed as a site package in this environment, activate the environment and run `pip install -e .`. 

If you're new to `conda` or Python environment management in general, please take a look at our easy 
[conda installation guide](docs/conda_installation_guide.md). 
 
### dependencies and requirements

`lhorizon` requires Python >= 3.9 (there are no plans to implement support for older Python versions).

the following packages are required for usage / installation:
* `more-itertools`
* `numpy`
* `pandas`
* `requests`
* `pip`

the following dependencies are optional and could potentially be omitted in restrictive install environments: 
* `jupyter` is only required to run examples
* `pytest`, `pytest-cov`, and `pytest-mock` are only required to run tests
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

The Jupyter Notebooks provided in the [examples](https://nbviewer.jupyter.org/github/MillionConcepts/lhorizon/tree/main/examples/) 
directory are the best quick-start guides to usage. You can also [try these examples out on Binder.](https://mybinder.org/v2/gh/MillionConcepts/lhorizon/main?filepath=examples)

See the [API reference](docs/api.md) for more details on the package's behavior.

## tests & benchmarks

Tests can be found in the [lhorizon.tests](lhorizon/tests) module. You can run them simply by executing `pytest` 
at the command line from the repository root directory.

You can also find some performance benchmarks in the [benchmarks](lhorizon/benchmarks) directory. Instructions for 
running them can be found in [benchmarks/readme.md](benchmarks/readme.md)

## changelog

* 2021-06-21: Full 1.0.0 release. Extensive changes from older versions:
  * completes and rationalizes interface 
  * concatenates and standardizes target submodule
  * reasonably complete test coverage and documentation
  * somewhat more extensive example Notebooks
* 2021-08-13: 1.1.0 release. 
  * adds additional convenience functions
  * substantially broadens test coverage
  * improves installation scripts
  * examples are now available via Binder
  * package is now available on `conda-forge` and `pip`
  * special thanks to [@malmans2](https://github.com/malmans2) for his help with this release in review for 
    [JOSS](https://joss.theoj.org/)!
* 2021-09-13: 1.1.1 release.
  * various bugfixes and documentation improvements
  * thanks again to everyone involved with the JOSS review, including [@malmans2](https://github.com/malmans2), 
    [@steo85it](https://github.com/steo85it), and [@arfon](https://github.com/arfon) 
* 2021-09-14: 1.1.2 release. Packaging-only changes.

## cautions / known issues

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
