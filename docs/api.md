# Table of Contents

* [\_response\_parsers](#_response_parsers)
  * [make\_lhorizon\_dataframe](#_response_parsers.make_lhorizon_dataframe)
  * [clean\_visibility\_flags](#_response_parsers.clean_visibility_flags)
  * [clean\_up\_vectors\_series](#_response_parsers.clean_up_vectors_series)
  * [clean\_up\_observer\_series](#_response_parsers.clean_up_observer_series)
  * [clean\_up\_series](#_response_parsers.clean_up_series)
  * [polish\_lhorizon\_dataframe](#_response_parsers.polish_lhorizon_dataframe)
* [solutions](#solutions)
  * [ray\_sphere\_equations](#solutions.ray_sphere_equations)
  * [get\_ray\_sphere\_solution](#solutions.get_ray_sphere_solution)
  * [lambdify\_system](#solutions.lambdify_system)
  * [make\_ray\_sphere\_lambdas](#solutions.make_ray_sphere_lambdas)
* [config](#config)
* [dscratch](#dscratch)
* [\_request\_formatters](#_request_formatters)
  * [format\_geodetic\_origin](#_request_formatters.format_geodetic_origin)
  * [format\_geodetic\_target](#_request_formatters.format_geodetic_target)
  * [format\_epoch\_params](#_request_formatters.format_epoch_params)
  * [make\_commandline](#_request_formatters.make_commandline)
  * [assemble\_request\_params](#_request_formatters.assemble_request_params)
* [base](#base)
  * [LHorizon](#base.LHorizon)
    * [dataframe](#base.LHorizon.dataframe)
    * [table](#base.LHorizon.table)
    * [check\_queried](#base.LHorizon.check_queried)
    * [query](#base.LHorizon.query)
    * [prepare\_request](#base.LHorizon.prepare_request)
    * [\_\_str\_\_](#base.LHorizon.__str__)
    * [\_\_repr\_\_](#base.LHorizon.__repr__)
* [benchscratch](#benchscratch)
* [targeter\_utils](#targeter_utils)
  * [array\_reference\_shift](#targeter_utils.array_reference_shift)
* [target](#target)
  * [Targeter](#target.Targeter)
    * [\_\_init\_\_](#target.Targeter.__init__)
    * [find\_targets](#target.Targeter.find_targets)
    * [find\_target\_grid](#target.Targeter.find_target_grid)
    * [transform\_targets\_to\_body\_frame](#target.Targeter.transform_targets_to_body_frame)
* [benchscratch\_2](#benchscratch_2)
* [handlers](#handlers)
  * [estimate\_line\_count](#handlers.estimate_line_count)
  * [chunk\_time](#handlers.chunk_time)
  * [datetime\_from\_horizon\_epochs](#handlers.datetime_from_horizon_epochs)
  * [construct\_lhorizon\_list](#handlers.construct_lhorizon_list)
  * [query\_all\_lhorizons](#handlers.query_all_lhorizons)
  * [list\_sites](#handlers.list_sites)
  * [list\_majorbodies](#handlers.list_majorbodies)
  * [get\_observer\_quantity\_codes](#handlers.get_observer_quantity_codes)
* [lhorizon\_utils](#lhorizon_utils)
  * [listify](#lhorizon_utils.listify)
  * [snorm](#lhorizon_utils.snorm)
  * [hunt\_csv](#lhorizon_utils.hunt_csv)
  * [are\_in](#lhorizon_utils.are_in)
  * [is\_it](#lhorizon_utils.is_it)
  * [utc\_to\_tt\_offset](#lhorizon_utils.utc_to_tt_offset)
  * [utc\_to\_tdb](#lhorizon_utils.utc_to_tdb)
  * [dt\_to\_jd](#lhorizon_utils.dt_to_jd)
  * [numeric\_columns](#lhorizon_utils.numeric_columns)
  * [produce\_jd\_series](#lhorizon_utils.produce_jd_series)
  * [time\_series\_to\_et](#lhorizon_utils.time_series_to_et)
  * [sph2cart](#lhorizon_utils.sph2cart)
  * [cart2sph](#lhorizon_utils.cart2sph)
  * [hats](#lhorizon_utils.hats)
  * [make\_raveled\_meshgrid](#lhorizon_utils.make_raveled_meshgrid)
  * [default\_lhorizon\_session](#lhorizon_utils.default_lhorizon_session)
  * [perform\_telnet\_exchange](#lhorizon_utils.perform_telnet_exchange)
  * [have\_telnet\_conversation](#lhorizon_utils.have_telnet_conversation)
* [kernels](#kernels)
* [kernels.load](#kernels.load)
  * [load\_metakernel](#kernels.load.load_metakernel)

<a id="_response_parsers"></a>

# Module \_response\_parsers

helper functions for parsing response text from the JPL Horizons CGI.
these functions are intended to be called by LHorizon methods and should
generally not be called directly.

<a id="_response_parsers.make_lhorizon_dataframe"></a>

#### make\_lhorizon\_dataframe

```python
def make_lhorizon_dataframe(jpl_response: str, topocentric_target: bool = False) -> pd.DataFrame
```

make a DataFrame from Horizons CGI response text.

<a id="_response_parsers.clean_visibility_flags"></a>

#### clean\_visibility\_flags

```python
def clean_visibility_flags(horizon_dataframe: pd.DataFrame) -> pd.DataFrame
```

assign names to unlabeled 'visibility flag' columns -- solar presence,
lunar/interfering body presence, is-target-on-near-side-of-parent-body,
is-target-illuminated; drop then if empty

<a id="_response_parsers.clean_up_vectors_series"></a>

#### clean\_up\_vectors\_series

```python
def clean_up_vectors_series(pattern: str, series: Array) -> pd.Series
```

regularize units, format text, and parse dates in a VECTORS table column

<a id="_response_parsers.clean_up_observer_series"></a>

#### clean\_up\_observer\_series

```python
def clean_up_observer_series(pattern: str, series: Array) -> Optional[pd.Series]
```

regularize units, format text, and parse dates in an OBSERVER table column

<a id="_response_parsers.clean_up_series"></a>

#### clean\_up\_series

```python
def clean_up_series(query_type: str, pattern: str, series: Array) -> pd.Series
```

dispatch function for Horizons column cleanup functions

<a id="_response_parsers.polish_lhorizon_dataframe"></a>

#### polish\_lhorizon\_dataframe

```python
def polish_lhorizon_dataframe(horizon_frame: pd.DataFrame, query_type: str) -> pd.DataFrame
```

make a nicely-formatted table from a dataframe generated by
make_lhorizon_dataframe. make tractable column names. also convert
distance units from AU or km to m and arcseconds to degrees.

<a id="solutions"></a>

# Module solutions

functionality for solving body-intersection problems. used by
`lhorizon.targeter`. currently contains only ray-sphere intersection solutions
but could also sensibly contain expressions for bodies of different shapes.

<a id="solutions.ray_sphere_equations"></a>

#### ray\_sphere\_equations

```python
def ray_sphere_equations(radius: float) -> list[sp.Eq]
```

generate a simple system of equations for intersections between
a ray with origin at (0, 0, 0) and direction vector [x, y, z]
and a sphere with radius == 'radius' and center (mx, my, mz).

<a id="solutions.get_ray_sphere_solution"></a>

#### get\_ray\_sphere\_solution

```python
def get_ray_sphere_solution(radius: float, farside: bool = False) -> tuple[sp.Expr]
```

produce a solution to the generalized ray-sphere equation for a body of
radius `radius`. by default, take the nearside solution. this produces a
tuple of sympy expressions objects, which are fairly slow to evaluate;
unless you are planning to further manipulate them, you would probably
rather call make_ray_sphere_lambdas().

<a id="solutions.lambdify_system"></a>

#### lambdify\_system

```python
def lambdify_system(expressions: Sequence[sp.Expr], expression_names: Sequence[str], variables: Sequence[sp.Symbol]) -> dict[str, Callable]
```

returns a dict of functions that substitute the symbols in 'variables'
into the expressions in 'expressions'. 'expression_names' serve as the
keys of the dict.

<a id="solutions.make_ray_sphere_lambdas"></a>

#### make\_ray\_sphere\_lambdas

```python
def make_ray_sphere_lambdas(radius: float, farside=False) -> dict[str, Callable]
```

produce a dict of functions that return solutions for the ray-sphere
equation for a sphere of radius `radius`.

<a id="config"></a>

# Module config

configuration options for `lhorizon`. Modifying members of this module will
change the default behavior of `LHorizon` objects.

### options

* OBSERVER_QUANTITIES: default Horizons QUANTITIES columns for OBSERVER queries
* VECTORS_QUANTITIES: default Horizons QUANTITIES columns for VECTORS queries
* TIMEOUT: timeout in seconds for JPL
* HORIZONS_SERVER: address of Horizons CGI gateway
* DEFAULT_HEADERS: default headers for Horizons requests
* TABLE_PATTERNS: tables of regexes used to match Horizons fields and the
    arguably more-readable column names we assign them to

<a id="dscratch"></a>

# Module dscratch

<a id="_request_formatters"></a>

# Module \_request\_formatters

formatters to translate various parameters and options into URL parameters
that can be parsed by JPL Horizons' CGI. These are mostly intended to be used
by LHorizon methods and should probably not be called directly.

<a id="_request_formatters.format_geodetic_origin"></a>

#### format\_geodetic\_origin

```python
def format_geodetic_origin(location: Mapping) -> dict
```

creates dict of URL parameters for a geodetic coordinate origin

<a id="_request_formatters.format_geodetic_target"></a>

#### format\_geodetic\_target

```python
def format_geodetic_target(location: Mapping) -> str
```

creates command string for a geodetic target

<a id="_request_formatters.format_epoch_params"></a>

#### format\_epoch\_params

```python
def format_epoch_params(epochs: Union[Sequence, Mapping]) -> dict
```

creates dict of URL parameters from epochs

<a id="_request_formatters.make_commandline"></a>

#### make\_commandline

```python
def make_commandline(target: Union[str, int, Mapping], closest_apparition: Union[bool, str], no_fragments: bool)
```

makes 'primary' command string for Horizons CGI request'

<a id="_request_formatters.assemble_request_params"></a>

#### assemble\_request\_params

```python
def assemble_request_params(commandline: str, query_type: str, extra_precision: bool, max_hour_angle: float, quantities: str, refraction: bool, refsystem: str, solar_elongation: Sequence[float]) -> dict[str]
```

final-stage assembler for Horizons CGI URL parameters

<a id="base"></a>

# Module base

This is the base module for `lhorizon`. It implements a class, `LHorizon`,
used to query the `JPL Horizons <https://ssd.jpl.nasa.gov/horizons.cgi>`
solar system ephemerides service.

<a id="base.LHorizon"></a>

## LHorizon Objects

```python
class LHorizon()
```

JPL HORIZONS interface object, the core class of `lhorizon`.

### Parameters
    target: Union[int, str, MutableMapping] = "301",
    origin: Union[int, str, MutableMapping] = "500@399",
    epochs: Optional[Union[str, float, Sequence[float], Mapping]] = None,
    session: Optional[requests.Session] = None
#### target: Union[int, str, MutableMapping] = "301"

Name, number, or designation of the object to be queried. the Moon
is used if no target is passed. Arbitrary topocentric coordinates
can also be provided in a dict, like:
```python
{
    'lon': longitude in deg,
    'lat': latitude in deg (North positive, South negative),
    'elevation': elevation in km above the reference ellipsoid,
    ['body': Horizons body ID of the central body; optional;
    Earth is used if it is not provided.]
}.
```
Horizons must possess a rotational model and reference ellipsoid
for the central body in order to process topocentric queries --
don't expect this to work with artificial satellites or most small
bodies, for instance.  Also note that Horizons always treats
west-longitude as positive for prograde bodies and east-longitude
as positive for retrograde bodies, with the very notable
exceptions of the Earth, Moon, and Sun; despite the fact that they
are prograde, it treats east-longitude as positive on these three
bodies.

#### origin: Union[int, str, MutableMapping] = "500@399"
Coordinate origin (representing central body or observer location).
Uses the same codes as JPL Horizons -- in some cases, text will
work, in some cases it will not. If no location is provided,
Earth's center is used. Arbitrary topocentic coordinates can also
be given as a dict, in the same format as the target parameter.
#### epochs: Optional[Union[str, float, Sequence[float], Mapping]]
Either a scalar in any astropy.time - parsable format,
a list of epochs in jd, iso, or dt format, or a dict
defining a range of times and dates. Timescale is UTC for OBSERVER
queries and TDB for VECTORS queries. If no epochs are provided,
the current time is used. Scalars or range dictionaries are
preferred over lists, as they tend to be processed more easily by
Horizons. The range dictionary format is:
```python
{
    'start':'YYYY-MM-DD [HH:MM:SS.fff]',
    'stop':'YYYY-MM-DD [HH:MM:SS.fff]',
    'step':'n[y|d|h|m]'
}
```
If no units are provided for `step`, Horizons evenly divides the
period between `start` and `stop` into n intervals.
#### session: Optional[requests.Session]
session object for optimizing API calls. A new session is generated
if one is not passed.
#### allow_long_queries: bool = False
if True, allows long (>2000 character) URLs to be used to query
JPL Horizons. These will often be truncated serverside, resulting
in unexpected output, and so are not allowed by default.
#### query_options: dict, optional
lower-level options passed to JPL Horizons. not all of these options are
meaningful for all queries. See JPL documentation for fuller descriptions
of some of these options. allowed keys and value types are:
* `airmass_lessthan: int` cuts off points with airmass > value
* `solar_elongation: Sequence[int]` e.g. `(30, 60)` suppresses times at
which angular separation between Sun and target in degrees exceeds this
value
* `max_hour_angle: float` suppresses times at which local hour angle at
Earth topocentric location exceeds this value in angular hours
* `rate_cutoff: float` suppresses times at which observer-target relative
rate in arcseconds/hour exceeds this value
* `skip_daylight: bool = False` suppresses times at which Sun is visible
from observer
* `refraction: bool = False` apply correction for atmospheric refraction
(Earth sites only)
* `refsystem: str = "J2000"` base coordinate reference system. default is
"J2000", Earth mean equator and equinox of January 1 2000,
closely aligned with ICRF and equivalent to SPICE "J2000'. Can also be
"B1950", FK5 / Earth mean equator of 1950.
* `quantities: str` Horizons quantity codes, expressed as a
comma-separated string. defaults for each query type
can be set in `lhorizon.config`. See JPL documentation for a full list of
code. "A" will return all available quantities.
* `extra_precision: bool=False`: return full available precision for
RA/Dec values in OBSERVER tables

### attributes

All parameters are also accessible class attributes. However, we do
not suggest that users modify target, origin, epochs, or query_type after
initialization. If session, query_options, or allow_long_queries are
modified, `lhorizon.prepare_request()` must be called in order for changes
to these attributes to affect subsequent queries to JPL Horizons.

#### request
`request.PreparedRequest` object: request for JPL Horizons.

#### response
`requests.response` objects: response from JPL Horizons. Examining
`lhorizon.response.content` is a DIY alternative to using the
`lhorizon.table()` or `lhorizon.dataframe()` methods.

### methods

<a id="base.LHorizon.dataframe"></a>

#### LHorizon.dataframe

```python
def dataframe() -> pd.DataFrame
```

return a DataFrame containing minimally-formatted response text from
JPL Horizons -- column names and quantities as sent, with almost no
changes but whitespace stripping.

this function triggers a query to JPL Horizons if a query has not yet
been sent. Otherwise, it uses the cached response.

<a id="base.LHorizon.table"></a>

#### LHorizon.table

```python
def table() -> pd.DataFrame
```

return a DataFrame with additional formatting. Regularizes column
names, casts times to datetime, attempts to regularize units. All
contents should be in m-s. JPL Horizons has an extremely wide range of
special-case response formatting, so if these heuristics prune
necessary columns or appear to perform incorrect conversions, fall
back to LHorizon.dataframe().

this function triggers a query to JPL Horizons if a query has not yet
been sent. Otherwise, it uses the cached response.

<a id="base.LHorizon.check_queried"></a>

#### LHorizon.check\_queried

```python
def check_queried() -> bool
```

determine whether this LHorizon has been queried with its currently-
formatted request. Note that if you manually change the request
parameters of a queried LHorizon and do not subsequently call
LHorizon.prepare_request(), LHorizon.check_queried() will
'incorrectly' return True.

<a id="base.LHorizon.query"></a>

#### LHorizon.query

```python
def query(refetch: bool = False) -> None
```

send this LHorizon's currently-formatted request to JPL HORIZONS and
update this LHorizon's response attribute. if we have already fetched
with identical parameters, don't fetch again unless explicitly told to.

<a id="base.LHorizon.prepare_request"></a>

#### LHorizon.prepare\_request

```python
def prepare_request()
```

Prepare request using active session and parameters. this is called
automatically by LHorizon.__init__(), but can also be called after
query parameters or request have been manually altered.

<a id="base.LHorizon.__str__"></a>

#### LHorizon.\_\_str\_\_

```python
def __str__()
```

String representation of LHorizon object instance

<a id="base.LHorizon.__repr__"></a>

#### LHorizon.\_\_repr\_\_

```python
def __repr__()
```

String representation of LHorizon object instance

<a id="benchscratch"></a>

# Module benchscratch

<a id="targeter_utils"></a>

# Module targeter\_utils

<a id="targeter_utils.array_reference_shift"></a>

#### array\_reference\_shift

```python
def array_reference_shift(positions: Array, time_series: Sequence, origin: str, destination: str, wide: bool = False)
```

using SPICE / SpiceyPy, transform an array of position vectors from origin
(frame) to destination (frame) at times in time_series. also computes
spherical representation of these coordinates. time_series must be in et
(seconds since J2000). Appropriate SPICE kernels must be loaded
prior to calling this function using `spiceypy.furnsh()` or an
even higher-level interface to `FURNSH` like
`lhorizon.kernels.load_metakernel()`

<a id="target"></a>

# Module target

<a id="target.Targeter"></a>

## Targeter Objects

```python
class Targeter()
```

<a id="target.Targeter.__init__"></a>

#### Targeter.\_\_init\_\_

```python
def __init__(target: Ephemeris, solutions: Mapping[str, Callable] = None, target_radius: Optional[float] = None)
```

target: LHorizon instance or dataframe; if a dataframe, must
    have columns named 'ra, dec, dist', 'az, alt, dist', or 'x, y, z'
    if the LHorizon instance is an OBSERVER query, uses ra_app_icrf
    and dec_app_icrf, if VECTORS, uses x/y/z

solutions: mapping of functions that each accept six args -- x1, y1,
    z1, x2, y2, z2 -- and return at least x, y, z position of an
    "intersection" (however defined). for compatibility with other
    functions in this module, should return NaN values for cases in
    which no intersection is found. if this parameter is not passed,
    generates ray-sphere solutions from the passed target radius.

target_radius: used only if no intersection solutions are
    passed; generates a system of ray-sphere intersection solutions for
    a target body of this radius.

<a id="target.Targeter.find_targets"></a>

#### Targeter.find\_targets

```python
def find_targets(pointings: Union[pd.DataFrame, LHorizon]) -> None
```

find targets using pointing vectors in a passed dataframe or lhorizon.
time series must match time series in body ephemeris. stores passed
pointings in self.ephemerides['pointing'] and solutions in
self.ephemerides['topocentric']

note that target center vectors and pointing vectors must be in the
same frame of reference or downstream results will be silly.

if you pass it a set of pointings without a time field, it will assume
that their time field is identical to the time field of
self.ephemerides["body"].

unless you do something extremely fancy in the solver,
the intersections will be 'geometric' quantities and thus reintroduce
some error due to light-time, rotation, aberration, etc. between target
body surface and target body center -- but considerably less error than
if you don't have a corrected vector from origin to target body center.

<a id="target.Targeter.find_target_grid"></a>

#### Targeter.find\_target\_grid

```python
def find_target_grid(raveled_meshgrid: pd.DataFrame) -> None
```

finds targets at a single moment in time for a grid of coordinates
expressed as an output of lhorizon_utils.make_raveled_meshgrid().
stores them in self.ephemerides["topocentric"] and the raveled meshgrid
in self.ephemerides["pointing"].

all non-time-releated caveats from Targeter.find_targets() apply.

<a id="target.Targeter.transform_targets_to_body_frame"></a>

#### Targeter.transform\_targets\_to\_body\_frame

```python
def transform_targets_to_body_frame(source_frame="j2000", target_frame="j2000")
```

transform targets from source_frame to body_frame. you must initialize
self.ephemerides["topocentric"] using find_targets() or
find_target_grid() before calling this function.

<a id="benchscratch_2"></a>

# Module benchscratch\_2

<a id="handlers"></a>

# Module handlers

This module contains a number of specialized query constructors and related
helper functions for lhorizon.

<a id="handlers.estimate_line_count"></a>

#### estimate\_line\_count

```python
def estimate_line_count(horizons_dt: MutableMapping[str, dt.datetime], seconds_per_step: float)
```

estimate number of lines that will be returned by _Horizons_ for a given
query. Cannot give correct answers for cases in which airmass, hour
angle, or other restrictive options are set. Used by bulk query
constructors to help split large queries across multiple `LHorizon`s.

<a id="handlers.chunk_time"></a>

#### chunk\_time

```python
def chunk_time(epochs: MutableMapping, chunksize: int) -> list[dict]
```

chunk time into a series of intervals that will return at most `chunksize`
lines from _Horizons_.

<a id="handlers.datetime_from_horizon_epochs"></a>

#### datetime\_from\_horizon\_epochs

```python
def datetime_from_horizon_epochs(start: str, stop: str, step: Union[int, str])
```

convert epoch dict to datetime in order to estimate response length.

<a id="handlers.construct_lhorizon_list"></a>

#### construct\_lhorizon\_list

```python
def construct_lhorizon_list(epochs: MutableMapping, target: Union[int, str, MutableMapping] = "301", origin: Union[int, str, MutableMapping] = "500@399", session: Optional[requests.Session] = None, query_type: str = "OBSERVER", query_options: Optional[Mapping] = None, chunksize=85000) -> list[LHorizon]
```

construct a list of `LHorizon`s. Intended for queries that will
return over 90000 lines, currently the hard limit of the _Horizons_
CGI. this function takes most of the same arguments as `LHorizon`, but
epochs must be specified as a dictionary with times in ISO format.

NOTE: this function does not support chunking long lists of
explicitly-defined individual epochs. queries of this type are extremely
inefficient for _Horizons_ and delivering many of them in quick succession
typically causes it to tightly throttle the requester.

<a id="handlers.query_all_lhorizons"></a>

#### query\_all\_lhorizons

```python
def query_all_lhorizons(lhorizons: Sequence[LHorizon], delay_between=2, delay_retry=8, max_retries=5)
```

queries a sequence of `LHorizon`s using a shared
session, carefully closing sockets and pausing between them, regenerating
session and pausing for a longer interval if _Horizons_ rejects a query

<a id="handlers.list_sites"></a>

#### list\_sites

```python
def list_sites(center_body: int = 399) -> pd.DataFrame
```

query _Horizons_ for all named sites recognized on the specified body and
format this response as a DataFrame. if no body is specified, uses Earth
(399).

<a id="handlers.list_majorbodies"></a>

#### list\_majorbodies

```python
def list_majorbodies() -> pd.DataFrame
```

query Horizons for all currently-recognized major bodies and format the
response into a DataFrame.

<a id="handlers.get_observer_quantity_codes"></a>

#### get\_observer\_quantity\_codes

```python
def get_observer_quantity_codes() -> str
```

retrieve observer quantity code table from HORIZONS telnet interface

<a id="lhorizon_utils"></a>

# Module lhorizon\_utils

<a id="lhorizon_utils.listify"></a>

#### listify

```python
def listify(thing: Any) -> list
```

Always a list, for things that want lists. use with care.

<a id="lhorizon_utils.snorm"></a>

#### snorm

```python
def snorm(thing: Any, minimum: float = 0, maximum: float = 1, m0: Optional[float] = None, m1: Optional[float] = None) -> Union[list[float], float]
```

simple min-max scaler. minimum and maximum are the limits of the range of
the returned sequence. m1 and m2 are optional parameters that specify
floor and ceiling values for the input other than its actual minimum and
maximum. If a single value is passed for thing, returns a float;
otherwise, returns a sequence of floats.

<a id="lhorizon_utils.hunt_csv"></a>

#### hunt\_csv

```python
def hunt_csv(regex: Pattern, body: str) -> list
```

finds chunk of csv in a larger string defined as regex, splits it,
and returns as list. really useful only for single lines.
worse than StringIO -> numpy or pandas csv reader in other cases.

<a id="lhorizon_utils.are_in"></a>

#### are\_in

```python
def are_in(items: Iterable, oper: Callable = and_) -> Callable
```

iterable -> function
returns function that checks if its single argument contains all
(or by changing oper, perhaps any) items

<a id="lhorizon_utils.is_it"></a>

#### is\_it

```python
def is_it(*types: type) -> Callable[Any, bool]
```

partially-evaluated predicate form of `isinstance`

<a id="lhorizon_utils.utc_to_tt_offset"></a>

#### utc\_to\_tt\_offset

```python
def utc_to_tt_offset(time: dt.datetime) -> float
```

return number of seconds necessary to advance UTC
to TT. we aren't presently supporting dates prior to 1972
because fractional leap second handling is another thing.

<a id="lhorizon_utils.utc_to_tdb"></a>

#### utc\_to\_tdb

```python
def utc_to_tdb(time: Union[dt.datetime, str]) -> dt.datetime
```

return time in tdb / jpl horizons coordinate time from passed time in utc.
may in some cases be closer to tt, but offset should be no more than 2 ms
in the worst case. only works for times after 1972 because of fractional
leap second handling. strings are assumed to be in UTC+0. passed datetimes
must be timezone-aware.

<a id="lhorizon_utils.dt_to_jd"></a>

#### dt\_to\_jd

```python
def dt_to_jd(time: Union[dt.datetime, pd.Series]) -> Union[float, pd.Series]
```

convert passed datetime or Series of datetime to julian day number (jd).
algorithm derived from Julian Date article on scienceworld.wolfram.com,
itself based on Danby, J. M., _Fundamentals of Celestial Mechanics_

<a id="lhorizon_utils.numeric_columns"></a>

#### numeric\_columns

```python
def numeric_columns(data: pd.DataFrame) -> list[str]
```

return a list of all numeric columns of a DataFrame

<a id="lhorizon_utils.produce_jd_series"></a>

#### produce\_jd\_series

```python
def produce_jd_series(epochs: Union[Timelike, Sequence[Timelike]]) -> pd.Series
```

convert passed epochs to julian day number (jd). scale is assumed to be
utc. this may of course produce very slightly spurious results for dates
in the future for which leap seconds have not yet been assigned. floats or
floatlike strings will be interpreted as jd and not modified. inputs of
mixed time formats or scales will likely produce undesired behavior.

<a id="lhorizon_utils.time_series_to_et"></a>

#### time\_series\_to\_et

```python
def time_series_to_et(time_series: Union[
        str, Sequence[str], dt.datetime, Sequence[dt.datetime], pd.Series
    ]) -> pd.Series
```

convert time -> 'seconds since J2000' epoch scale preferred by SPICE.
accepts anything `pandas` can cast to Series and interpret as datetime.
if not timezone-aware, assumes input is in UTC.

<a id="lhorizon_utils.sph2cart"></a>

#### sph2cart

```python
def sph2cart(lat: Union[float, Array], lon: Union[float, Array], radius: Union[float, Array] = 1, unit: str = "degrees")
```

convert spherical to cartesian coordinates. assumes input is in degrees
by default; pass unit="radians" to specify input in radians. if passed any
arraylike objects, returns a DataFrame, otherwise, returns a tuple of
values.

caveats:
1. this assumes a coordinate convention in which latitude runs from -90
    to 90 degrees.

<a id="lhorizon_utils.cart2sph"></a>

#### cart2sph

```python
def cart2sph(x0: Union[float, Array], y0: Union[float, Array], z0: Union[float, Array], unit: str = "degrees") -> Union[pd.DataFrame, tuple]
```

convert cartesian to spherical coordinates. returns degrees by default;
pass unit="radians" to return radians. if passed any arraylike objects,
returns a DataFrame, otherwise, returns a tuple of values.

caveats:
1. this assumes a coordinate convention in which latitude runs from -90
    to 90 degrees.
2. returns longitude in strictly positive coordinates.

<a id="lhorizon_utils.hats"></a>

#### hats

```python
def hats(vectors: Union[np.ndarray, pd.DataFrame, pd.Series]) -> Union[np.ndarray, pd.DataFrame, pd.Series]
```

convert an array of passed "vectors" (row-wise-stacked sequences of
floats) to unit vectors

<a id="lhorizon_utils.make_raveled_meshgrid"></a>

#### make\_raveled\_meshgrid

```python
def make_raveled_meshgrid(axes: Sequence[np.ndarray], axis_names: Optional[Sequence[str, int]] = None)
```

produces a flattened, indexed version of a 'meshgrid' (a cartesian
product of axes standing in for a vector space, conventionally produced
by numpy.meshgrid)

<a id="lhorizon_utils.default_lhorizon_session"></a>

#### default\_lhorizon\_session

```python
def default_lhorizon_session() -> requests.Session
```

returns a requests.Session object with default `lhorizon` options

<a id="lhorizon_utils.perform_telnet_exchange"></a>

#### perform\_telnet\_exchange

```python
def perform_telnet_exchange(message: bytes, read_until_this: bytes, connection: Telnet) -> bytes
```

send message via connection, block until read_until_this is received
or connection's timeout is met, and return all input up to encounter
with read_until_this.

<a id="lhorizon_utils.have_telnet_conversation"></a>

#### have\_telnet\_conversation

```python
def have_telnet_conversation(conversation_structure: Sequence[tuple[bytes, bytes]], connection: Telnet, lazy: bool = False) -> Union[Iterator, tuple[bytes]]
```

perform a series of noninteractive telnet exchanges via connection
and return the output of those exchanges.

if lazy is True, return the conversation as an iterator that
performs and yields the output of each exchange when incremented.

<a id="kernels"></a>

# Module kernels

<a id="kernels.load"></a>

# Module kernels.load

<a id="kernels.load.load_metakernel"></a>

#### load\_metakernel

```python
def load_metakernel()
```

convenience wrapper for `spiceypy.furnsh()` and thus SPICE `FURNSH`.
it's impossible to accurately 'target' paths in a flexible way inside a
SPICE metakernel; this sweeps directory structure messiness under the rug.

