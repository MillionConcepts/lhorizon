"""
This module implements a class for querying the
`JPL Horizons <https://ssd.jpl.nasa.gov/horizons.cgi>`service,
along with associated helper functions.

It is rewritten from astroquery.JPLHorizons. it contains fixes and added
functionality related to queries about targets and observers in arbitrary
frames, as well as helpers for bulk downloads. it loads results into pandas
dataframes rather than astropy tables for increased performance (at the
cost of integrated unit tracking).
"""

import warnings
from typing import Mapping, Union

import requests
from astropy.time import Time

from lhorizon.config import (
    EPH_QUANTITIES,
    HORIZONS_SERVER,
    TIMEOUT,
    KNOWN_ID_TYPES,
    KNOWN_QUERY_TYPES,
)
from lhorizon._response_parsers import (
    make_horizon_dataframe,
    polish_horizons_table,
)

from lhorizon._request_formatters import (
    make_commandline,
    assemble_request_params,
    format_epoch_params,
    format_geodetic_origin
)

from lhorizon.lhorizon_utils import convert_to_jd


class LHorizon:
    """
    A class for querying and formatting data from the
    `JPL Horizons <https://ssd.jpl.nasa.gov/horizons.cgi>`service.
    """
    def __init__(
        self,
        target="301",
        origin="500@399",
        epochs=None,
        id_type="majorbody",
        session=None,
        query_type="OBSERVER",
    ):
        """
        Instantiate JPL HORIZONS interface object.

        Parameters
        ----------
        target : str or int, required
            Name, number, or designation of the object to be queried
        origin : int, str, or dict, optional
            Observer's location for ephemerides queries or center body name
            for orbital element or vector queries. Uses the same codes as
            JPL Horizons. If no location is provided, Earth's center is
            used. Arbitrary topocentic coordinates for ephemerides queries
            can be provided in the format of a dictionary. The dictionary
            has to be of the form {``'lon'``: longitude in deg (East
            positive, West negative), ``'lat'``: latitude in deg (North
            positive, South negative), ``'elevation'``: elevation in km
            above the reference ellipsoid, [``'body'``: Horizons body ID of
            the central body; optional; if this value is not provided it is
            assumed that this location is on Earth]}.
        epochs : Any, dict[str, str] or Sequence[str, dt.datetime], optional
            Either a scalar in any astropy.time - parsable format,
            a list of epochs in JD, MJD, iso, or dt format, or a dict
            defining a range of times and dates; the range dictionary has to
            be of the form {``'start'``:'YYYY-MM-DD [HH:MM:SS]',
            ``'stop'``:'YYYY-MM-DD [HH:MM:SS]', ``'step'``:'n[y|d|m|s]'}.
            Timescale is UTC. If no epochs are provided, the current time is
            used.
        id_type : str, optional
            Identifier type, options:
            ``'smallbody'``, ``'majorbody'`` (planets but also
            anything that is not a small body), ``'designation'``,
            ``'name'``, ``'asteroid_name'``, ``'comet_name'``,
            ``'id'`` (Horizons id number), or ``'smallbody'`` (find the
            closest match under any id_type), default: ``'smallbody'``
        """
        if isinstance(target, Mapping):
            target = self._prep_geodetic_location(target)
        self.target = target
        if isinstance(origin, Mapping):
            origin = self._prep_geodetic_location(origin)
        self.location = origin
        if query_type not in KNOWN_QUERY_TYPES:
            raise ValueError(
                "only "
                + str(KNOWN_QUERY_TYPES)
                + " are understood as query types."
            )
        self.query_type = query_type
        self.epochs = self._prep_epochs(epochs)
        if id_type not in KNOWN_ID_TYPES:
            raise ValueError(
                "only " + str(KNOWN_ID_TYPES) + " are understood as id types."
            )
        self.id_type = id_type
        if session is None:
            session = requests.Session()
        self.session = session
        self.response = None
        self.request = None

    # TODO: determine if these might be nicer as properties
    def dataframe(self):
        """
        perform query if not yet queried. return as a dataframe with mostly-as-
        sent column names &c.
        """
        if self.response is None:
            self.query()
        if "g:" in str(self.target):
            get_target_location = True
        else:
            get_target_location = False
        frame = make_horizon_dataframe(
            self.response.text, get_target_location=get_target_location
        )
        return frame

    def table(self):
        """
        attempt to format it more nicely. may fail depending on query type.
        """
        return polish_horizons_table(self.dataframe())

    def check_queried(self):
        # it's not a requery if no query appears to have been performed or if
        # someone has messed with the object in some weird way
        if (self.response is None) or (self.request is None):
            return False
        # it's also not a requery if the parameters have changed; otherwise,
        # it is a requery
        return self.response.url == self.request.url

    def fetch(self, refetch=False):
        """
        fetch data from HORIZONS. if we have already fetched with identical
        parameters, don't fetch again unless explicitly told to.
        """
        if refetch or not self.check_queried():
            self.response = self.session.send(self.request, timeout=TIMEOUT)
        self._check_url_length()

    def query(self, *, refetch=False, **query_options):
        """
        Query JPL Horizons. See documentation for a full list of kwargs
        """
        self._prepare_request(**query_options)
        self.fetch(refetch)

    def _check_url_length(self):
        # TODO: consider moving this up in the process before they send a query
        """warn user about long urls that HORIZONS may reject"""
        if len(self.response.url) >= 2000:
            warnings.warn(
                (
                    "The url used in this query is very long "
                    "and might have been truncated. The results of "
                    "the query might be compromised. If you queried "
                    "a list of epochs, consider querying a range."
                )
            )

    def _prepare_request(
        self,
        airmass_lessthan=99,
        solar_elongation=(0, 180),
        max_hour_angle=0,
        rate_cutoff=None,
        skip_daylight=False,
        refraction=False,
        refsystem="J2000",
        closest_apparition=False,
        no_fragments=False,
        quantities: Union[int, str] = EPH_QUANTITIES,
        extra_precision=False,
    ):

        # assemble 'command line' (convention from original telnet interface)
        command = make_commandline(
            self.target, self.id_type, closest_apparition, no_fragments
        )
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
        request = requests.Request("GET", HORIZONS_SERVER, params=params)
        self.request = self.session.prepare_request(request)

    @staticmethod
    def _prep_epochs(epochs):
        if epochs is None:
            return Time.now().jd
        if isinstance(epochs, Mapping):
            if not (
                    "start" in epochs and "stop" in epochs and "step" in
                    epochs
            ):
                raise ValueError(
                    "time range ({:s}) requires start, stop, "
                    "and step".format(str(epochs))
                )
            return epochs
        epochs = convert_to_jd(epochs)
        return epochs

    @staticmethod
    def _prep_geodetic_location(location):
        if (
                "lon" not in location
                or "lat" not in location
                or "elevation" not in location
        ):
            raise ValueError("'location' must contain lon, lat, " "elevation")
        if "body" not in location:
            location["body"] = "399"
        return location

    def __str__(self):
        """
        String representation of LHorizon object instance'
        """
        return (
            'LHorizons instance "{:s}"; location={:s}, '
            "epochs={:s}, id_type={:s}"
        ).format(
            str(self.target),
            str(self.location),
            str(self.epochs),
            str(self.id_type),
        )


