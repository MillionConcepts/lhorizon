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
from astropy.time import Time

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

from lhorizon.lhorizon_utils import convert_to_jd, default_lhorizon_session


class LHorizon:
    """
    A class for querying and formatting data from the
    `JPL Horizons <https://ssd.jpl.nasa.gov/horizons.cgi>`service.
    """

    def __init__(
        self,
        target: Union[int, str, MutableMapping] = "301",
        origin: Union[int, str, MutableMapping] = "500@399",
        epochs: Optional[Union[str, float, Mapping]] = None,
        session: Optional[requests.Session] = None,
        query_type: str = "OBSERVER",
        allow_long_queries: bool = False,
        query_options: Optional[Mapping] = None,
    ):
        """
        JPL HORIZONS interface object, the core class of `lhorizon`.

        Parameters
        ----------
        target : str or int, optional
            Name, number, or designation of the object to be queried. the Moon
            is used if no target is passed. Arbitrary topocentric coordinates
            can also be provided in a dict, like:
            {
                'lon': longitude in deg,
                'lat': latitude in deg (North positive, South negative),
                'elevation': elevation in km above the reference ellipsoid,
                ['body': Horizons body ID of the central body; optional;
                Earth is used if it is not provided.]
            }.
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
        """
        if isinstance(target, MutableMapping):
            target = self._prep_geodetic_location(target)
        self.target = target
        if isinstance(origin, MutableMapping):
            origin = self._prep_geodetic_location(origin)
        self.location = origin
        if query_type not in config.KNOWN_QUERY_TYPES:
            raise ValueError(
                "only "
                + str(config.KNOWN_QUERY_TYPES)
                + " are understood as query types."
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
        solar_elongation: Sequence[int] = (0, 180),
        max_hour_angle: int = 0,
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
    def _prep_epochs(epochs: Union[str, float, Mapping]):
        """
        convert epochs to a standardized form. should generally only be called
        by __init__
        """
        if epochs is None:
            return Time.now().jd
        if isinstance(epochs, Mapping):
            if not (
                "start" in epochs and "stop" in epochs and "step" in epochs
            ):
                raise ValueError(
                    "time range ({:s}) requires start, stop, "
                    "and step".format(str(epochs))
                )
            return epochs
        epochs = convert_to_jd(epochs)
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
        String representation of LHorizon
        """
        return (
            "LHorizon: target={:s}; location={:s}; epochs={:s}; {}" ""
        ).format(
            str(self.target),
            str(self.location),
            str(self.epochs),
            "queried" if self.check_queried() else "not queried",
        )

    def __repr__(self):
        """
        String representation of LHorizon object instance'
        """
        return self.__str__()
