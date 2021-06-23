"""
This is the base module for `lhorizon`. It implements a class, `LHorizon`,
used to query the `JPL Horizons <https://ssd.jpl.nasa.gov/horizons.cgi>`
solar system ephemerides service.
"""

from collections.abc import Mapping, MutableMapping, Sequence
from typing import Union, Optional
import warnings

import pandas as pd
import requests

import lhorizon.config as config
from lhorizon._response_parsers import (
    make_lhorizon_dataframe,
    polish_lhorizon_dataframe,
)

from lhorizon._request_formatters import (
    make_commandline,
    assemble_request_params,
    format_epoch_params,
    format_geodetic_origin,
)

from lhorizon.lhorizon_utils import produce_jd_series, default_lhorizon_session


class LHorizon:
    """
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
    """

    def __init__(
        self,
        target: Union[int, str, MutableMapping] = "301",
        origin: Union[int, str, MutableMapping] = "500@399",
        epochs: Optional[Union[str, float, Sequence[float], Mapping]] = None,
        session: Optional[requests.Session] = None,
        query_type: str = "OBSERVER",
        allow_long_queries: bool = False,
        query_options: Optional[Mapping] = None,
    ):
        if isinstance(target, MutableMapping):
            target = self._prep_geodetic_location(target)
        self.target = target
        if isinstance(origin, MutableMapping):
            origin = self._prep_geodetic_location(origin)
        self.location = origin
        if query_type not in ("VECTORS", "OBSERVER"):
            raise ValueError(
                "only VECTORS and OBSERVER are supported as query types."
            )
        self.query_type = query_type
        self.epochs = self._prep_epochs(epochs)
        if session is None:
            session = default_lhorizon_session()
        self.session = session
        self.response = None
        self.request = None
        self.allow_long_queries = allow_long_queries
        if query_options is None:
            query_options = {}
        self.query_options = query_options
        self.prepare_request()

    def dataframe(self) -> pd.DataFrame:
        """
        return a DataFrame containing minimally-formatted response text from
        JPL Horizons -- column names and quantities as sent, with almost no
        changes but whitespace stripping.

        this function triggers a query to JPL Horizons if a query has not yet
        been sent. Otherwise, it uses the cached response.
        """
        if self.response is None:
            self.query()
        if ("g:" in str(self.target)) or isinstance(self.target, Mapping):
            get_target_location = True
        else:
            get_target_location = False
        frame = make_lhorizon_dataframe(
            self.response.text, topocentric_target=get_target_location
        )
        return frame

    def table(self) -> pd.DataFrame:
        """
        return a DataFrame with additional formatting. Regularizes column
        names, casts times to datetime, attempts to regularize units. All
        contents should be in m-s. JPL Horizons has an extremely wide range of
        special-case response formatting, so if these heuristics prune
        necessary columns or appear to perform incorrect conversions, fall
        back to LHorizon.dataframe().

        this function triggers a query to JPL Horizons if a query has not yet
        been sent. Otherwise, it uses the cached response.
        """
        return polish_lhorizon_dataframe(self.dataframe(), self.query_type)

    def check_queried(self) -> bool:
        """
        determine whether this LHorizon has been queried with its currently-
        formatted request. Note that if you manually change the request
        parameters of a queried LHorizon and do not subsequently call
        LHorizon.prepare_request(), LHorizon.check_queried() will
        'incorrectly' return True.
        """
        # it's not a requery if no query appears to have been performed or if
        # someone has messed with the object in some weird way
        if (self.response is None) or (self.request is None):
            return False
        # it's also not a requery if the parameters have changed; otherwise,
        # it is a requery
        return self.response.url == self.request.url

    def query(self, refetch: bool = False) -> None:
        """
        send this LHorizon's currently-formatted request to JPL HORIZONS and
        update this LHorizon's response attribute. if we have already fetched
        with identical parameters, don't fetch again unless explicitly told to.
        """
        if refetch or not self.check_queried():
            self.response = self.session.send(
                self.request, timeout=config.TIMEOUT
            )

    def prepare_request(self):
        """
        Prepare request using active session and parameters. this is called
        automatically by LHorizon.__init__(), but can also be called after
        query parameters or request have been manually altered.
        """
        self._prepare(**self.query_options)

    def _prepare(
        self,
        airmass_lessthan: int = 99,
        solar_elongation: Sequence[float] = (0, 180),
        max_hour_angle: float = 0,
        rate_cutoff: Optional[float] = None,
        skip_daylight: bool = False,
        refraction: bool = False,
        refsystem: str = "J2000",
        closest_apparition=False,
        no_fragments=False,
        quantities=None,
        extra_precision=False,
    ):
        """
        sets up url parameters and calls self.session.prepare_request(). this
        should generally not be called directly; call self.prepare_request()
        after properly formatting self.query_options or other parameters.
        """

        # assemble 'command line' (convention from original telnet interface)
        command = make_commandline(
            self.target, closest_apparition, no_fragments
        )
        if quantities is None:
            quantities = getattr(config, self.query_type + "_QUANTITIES")

        # TODO: document this
        params = assemble_request_params(
            command,
            self.query_type,
            extra_precision,
            max_hour_angle,
            quantities,
            refraction,
            refsystem,
            solar_elongation,
        )
        if isinstance(self.location, Mapping):
            params |= format_geodetic_origin(self.location)
        else:
            params["CENTER"] = "'" + str(self.location) + "'"
        if rate_cutoff is not None:
            params["ANG_RATE_CUTOFF"] = str(rate_cutoff)
        params |= format_epoch_params(self.epochs)
        if airmass_lessthan < 99:
            params["AIRMASS"] = str(airmass_lessthan)
        if skip_daylight:
            params["SKIP_DAYLT"] = "YES"
        else:
            params["SKIP_DAYLT"] = "NO"

        # build, prep, and store request
        request = requests.Request(
            "GET", config.HORIZONS_SERVER, params=params
        )
        self.request = self.session.prepare_request(request)
        self._check_url_length()

    def _check_url_length(self):
        """
        Raise an error for long urls that HORIZONS may truncate. If
        self.allow_long_queries is True, simply issue a warning.
        """
        if len(self.request.url) >= 2000:
            if self.allow_long_queries is True:
                warnings.warn(
                    (
                        "The url used in this query is very long "
                        "and might have been truncated. The results of "
                        "the query might be compromised. If you queried "
                        "a list of epochs, consider querying a range."
                    )
                )
            else:
                raise ValueError(
                    "The url used in this query is > 2000 characters. It is "
                    "likely to be truncated serverside and produce unexpected "
                    "results. If you queried a list of epochs, consider "
                    "querying a range; also consider using one of the helper "
                    "functions for bulk queries in lhorizon.handlers. If "
                    "you're absolutely sure you want to send this query, "
                    "initialize this LHorizons object again with "
                    "allow_long_queries=True."
                )

    @staticmethod
    def _prep_epochs(epochs: Union[Sequence, str, float, Mapping]):
        """
        convert epochs to a standardized form. should generally only be called
        by __init__
        """
        import datetime as dt
        if epochs is None:
            return produce_jd_series(dt.datetime.utcnow())
        if isinstance(epochs, Mapping):
            if not (
                "start" in epochs and "stop" in epochs and "step" in epochs
            ):
                raise ValueError(
                    "time range ({:s}) requires start, stop, "
                    "and step".format(str(epochs))
                )
            return epochs
        epochs = produce_jd_series(epochs)
        return epochs

    @staticmethod
    def _prep_geodetic_location(location: MutableMapping):
        """
        convert geodetic location dicts to a standardized form. should
        generally only be called by __init__
        """
        if "lon" not in location or "lat" not in location:
            raise ValueError("'location' must contain at least lon & lat")
        if "body" not in location:
            location["body"] = "399"
        if "elevation" not in location:
            location["elevation"] = "0"
        return location

    def __str__(self):
        """
        String representation of LHorizon object instance
        """
        if isinstance(self.epochs, pd.Series):
            print_epochs = self.epochs.values
        else:
            print_epochs = self.epochs
        return (
            "LHorizon: target={:s}; location={:s}; epochs={:s}; {}" ""
        ).format(
            str(self.target),
            str(self.location),
            str(print_epochs),
            "queried" if self.check_queried() else "not queried",
        )

    def __repr__(self):
        """
        String representation of LHorizon object instance
        """
        return self.__str__()
