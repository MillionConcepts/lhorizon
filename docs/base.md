# Table of Contents

* [lhorizon.base](#lhorizon.base)
  * [LHorizon](#lhorizon.base.LHorizon)
    * [dataframe](#lhorizon.base.LHorizon.dataframe)
    * [table](#lhorizon.base.LHorizon.table)
    * [check\_queried](#lhorizon.base.LHorizon.check_queried)
    * [query](#lhorizon.base.LHorizon.query)
    * [prepare\_request](#lhorizon.base.LHorizon.prepare_request)
    * [\_\_str\_\_](#lhorizon.base.LHorizon.__str__)
    * [\_\_repr\_\_](#lhorizon.base.LHorizon.__repr__)

<a name="lhorizon.base"></a>
# lhorizon.base

This is the base module for `lhorizon`. It implements a class, `LHorizon`,
used to query the `JPL Horizons <https://ssd.jpl.nasa.gov/horizons.cgi>`
solar system ephemerides service.

<a name="lhorizon.base.LHorizon"></a>
## LHorizon Objects

```python
class LHorizon()
```

JPL HORIZONS interface object, the core class of `lhorizon`.

Parameters
----------
target : str or int, optional
    Name, number, or designation of the object to be queried. the Moon
    is used if no target is passed. Arbitrary topocentric coordinates
    can also be provided in a dict, like:
    ```
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
origin : int, str, or dict, optional
    Coordinate origin (representing central body or observer location).
    Uses the same codes as JPL Horizons -- in some cases, text will
    work, in some cases it will not. If no location is provided,
    Earth's center is used. Arbitrary topocentic coordinates can also
    be given as a dict, in the same format as the target parameter.
epochs : dict[str, str] or Sequence[str, float, dt.datetime], optional
    Either a scalar in any astropy.time - parsable format,
    a list of epochs in jd, iso, or dt format, or a dict
    defining a range of times and dates. Timescale is UTC for OBSERVER
    queries and TDB for VECTORS queries. If no epochs are provided,
    the current time is used. Scalars or range dictionaries are
    preferred over lists, as they tend to be processed more easily by
    Horizons. The range dictionary format is:
    {
        ``'start'``:'YYYY-MM-DD [HH:MM:SS.fff]',
        ``'stop'``:'YYYY-MM-DD [HH:MM:SS.fff]',
        ``'step'``:'n[y|d|h|m]'
    }
    If no units are provided for step, Horizons evenly divides the
    period between start and stop into n intervals.
session: requests.Session, optional
    session object for optimizing API calls. A new session is generated
    if one is not passed.
allow_long_queries: bool, optional
    if True, allows long (>2000 character) URLs to be used to query
    JPL Horizons. These will often be truncated serverside, resulting
    in unexpected output, and so are not allowed by default.
query_options: dict, optional
    additional Horizons query options. See documentation for a list of
    supported options.

<a name="lhorizon.base.LHorizon.dataframe"></a>
#### dataframe

```python
 | dataframe() -> pd.DataFrame
```

return a DataFrame containing minimally-formatted response text from
JPL Horizons -- column names and quantities as sent, with almost no
changes but whitespace stripping.

this function triggers a query to JPL Horizons if a query has not yet
been sent. Otherwise, it uses the cached response.

<a name="lhorizon.base.LHorizon.table"></a>
#### table

```python
 | table() -> pd.DataFrame
```

return a DataFrame with additional formatting. Regularizes column
names, casts times to datetime, attempts to regularize units. All
contents should be in m-s. JPL Horizons has an extremely wide range of
special-case response formatting, so if these heuristics prune
necessary columns or appear to perform incorrect conversions, fall
back to LHorizon.dataframe().

this function triggers a query to JPL Horizons if a query has not yet
been sent. Otherwise, it uses the cached response.

<a name="lhorizon.base.LHorizon.check_queried"></a>
#### check\_queried

```python
 | check_queried() -> bool
```

determine whether this LHorizon has been queried with its currently-
formatted request. Note that if you manually change the request
parameters of a queried LHorizon and do not subsequently call
LHorizon.prepare_request(), LHorizon.check_queried() will
'incorrectly' return True.

<a name="lhorizon.base.LHorizon.query"></a>
#### query

```python
 | query(refetch: bool = False) -> None
```

send this LHorizon's currently-formatted request to JPL HORIZONS and
update this LHorizon's response attribute. if we have already fetched
with identical parameters, don't fetch again unless explicitly told to.

<a name="lhorizon.base.LHorizon.prepare_request"></a>
#### prepare\_request

```python
 | prepare_request()
```

Prepare request using active session and parameters. this is called
automatically by LHorizon.__init__(), but can also be called after
query parameters or request have been manually altered.

<a name="lhorizon.base.LHorizon.__str__"></a>
#### \_\_str\_\_

```python
 | __str__()
```

String representation of LHorizon object instance

<a name="lhorizon.base.LHorizon.__repr__"></a>
#### \_\_repr\_\_

```python
 | __repr__()
```

String representation of LHorizon object instance

