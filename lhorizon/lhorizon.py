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

import datetime as dt
import math
import re
import warnings
from io import StringIO
from collections import OrderedDict
from functools import reduce, partial
from operator import and_
from typing import Mapping, Sequence, Union

import astropy.units as u
import astropy.time as at
import dateutil.parser as dtp
import numpy as np
import pandas as pd
import requests
from astropy.time import Time

from lhorizon.config import EPH_QUANTITIES, HORIZONS_SERVER, TIMEOUT
from more_itertools import chunked
from utils import snorm, listify




def hunt_csv(regex, body):
    """
    finds chunk of csv in a larger text file defined as regex, splits it,
    and returns as list. useful only for single lines.
    worse than StringIO -> numpy or pandas csv reader in other cases.
    """
    csv_string = re.search(regex, body)[0]
    if r"\n" in csv_string:
        lines = csv_string.split(r"\n")
        processed_lines = []
        for line in lines:
            csv_fields = line.split(",")
            csv_fields = [field.strip() for field in csv_fields]
            processed_lines.append(csv_fields)
        return processed_lines
    csv_fields = csv_string.split(",")
    return [field.strip() for field in csv_fields]


def format_horizon(horizon_frame):
    # make tractable column names for a dataframe from a Horizons response.
    # also convert distance units from AU to m
    # and arcseconds to degrees
    au_to_m = (1 * u.au).to(u.m).value
    horizon_columns = {
        "time": pd.Series(
            [
                dtp.parse(instant)
                for instant in horizon_frame["Date__(UT)__HR:MN:SC.fff"]
            ]
        ),
        "az": horizon_frame["Azi_(a-app)"].astype(np.float64),
        "alt": horizon_frame["Elev_(a-app)"].astype(np.float64),
        "dist": pd.Series(
            [
                au_to_m * delta
                for delta in horizon_frame["delta"].astype(np.float64)
            ]
        ),
        "sub_lon": horizon_frame["ObsSub-LON"].astype(np.float64),
        "sub_lat": horizon_frame["ObsSub-LAT"].astype(np.float64),
        # convert from arcseconds to degree
        "ang_diam": horizon_frame["Ang-diam"].astype(np.float64) / 3600,
    }
    # only present for lunar ephemerides with selenographic coords specified
    if "T-O-M" in horizon_frame.columns:
        horizon_columns["t_o_m_angle"] = horizon_frame["T-O-M"].astype(
            np.float64
        )
    # only present for ephemerides with planetographic coords specified
    if "geo_lat" in horizon_frame.columns:
        for p_coord in ["geo_lat", "geo_lon", "geo_el"]:
            horizon_columns[p_coord] = horizon_frame[p_coord].astype(
                np.float64
            )
    return pd.DataFrame(horizon_columns)


def make_horizon_dataframe(raw_horizon_response, get_target_location=False):
    """
    make a dataframe from a raw horizon response.
    dataframe may contain ephemerides at one or more times.
    """

    # delimiters for column and data sections
    # TODO: this only works right if all the columns are selected. maybe
    # specifying this in a better way would be better.
    horizon_column_search = re.compile(r"Date.*(?=\n\*+)")
    horizon_data_search = re.compile(r"(?<=\$\$SOE\n)(.|\n)*(?=\$\$EOE)")

    # grab these sections and write them into a string buffer
    columns = re.search(horizon_column_search, raw_horizon_response)[0]
    data = re.search(horizon_data_search, raw_horizon_response)[0]
    data_buffer = StringIO()
    data_buffer.write(columns + "\n" + data)
    data_buffer.seek(0)

    # read this buffer as csv
    horizon_dataframe = pd.read_csv(data_buffer, sep=" *, *", engine="python")
    horizon_dataframe.rename(
        mapper={
            "Unnamed: 2": "solar_presence",
            "Unnamed: 3": "lunar_presence",
            "Unnamed: 4": "nearside_flag",
            "Unnamed: 5": "illumination_flag",
        },
        axis=1,
        inplace=True,
    )
    # add the target's geodetic coordinates if desired
    if get_target_location:
        horizon_target_search = re.compile(
            r"(?<=Target geodetic : )\d.*(?= {)"
        )
        target_geodetic_coords = hunt_csv(
            horizon_target_search, raw_horizon_response
        )
        horizon_dataframe["geo_lon"] = target_geodetic_coords[0]
        horizon_dataframe["geo_lat"] = target_geodetic_coords[1]
        horizon_dataframe["geo_el"] = target_geodetic_coords[2]

    # drop empty columns and return
    return horizon_dataframe.dropna(axis=1)


class LHorizon:
    """
    A class for querying the
    `JPL Horizons <https://ssd.jpl.nasa.gov/horizons.cgi>`service.

    rewritten from astroquery.JPLHorizons. contains fixes and added
    functionality related to queries about the Moon.
    """

    def __init__(
        self,
        target_id=None,
        location=None,
        epochs=None,
        id_type="majorbody",
        session=None,
        query_type="OBSERVER",
    ):
        """
        Instantiate JPL query.

        Parameters
        ----------
        target_id : str or int, required
            Name, number, or designation of the object to be queried
        location : int, str, or dict, optional
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
        self.target_id = target_id
        self.location = location
        if epochs is not None:
            if isinstance(epochs, Mapping):
                if not (
                    "start" in epochs and "stop" in epochs and "step" in epochs
                ):
                    raise ValueError(
                        "time range ({:s}) requires start, stop, "
                        "and step".format(str(epochs))
                    )
            elif not isinstance(epochs, Sequence):
                # turn scalars into list
                epochs = [epochs]
        self.query_type = query_type
        if isinstance(epochs, Sequence):
            # coerce iterable / scalar iso or dt inputs to jd
            is_not_jd = True
            formats = ["jd", "iso", "datetime"]
            while is_not_jd:
                try:
                    form = formats.pop()
                    epochs = listify(at.Time(epochs, format=form).jd)
                    is_not_jd = False
                except (ValueError, TypeError):
                    if len(formats) == 0:
                        raise

        self.epochs = epochs
        if id_type not in [
            "smallbody",
            "majorbody",
            "designation",
            "name",
            "asteroid_name",
            "comet_name",
            "id",
        ]:
            raise ValueError("id_type ({:s}) not allowed".format(id_type))
        self.id_type = id_type
        self.session = session
        self.response = None
        self.uri = None
        self.request_payload = None

    def __str__(self):
        """
        String representation of HorizonsClass object instance'
        """
        return (
            'LHorizons instance "{:s}"; location={:s}, '
            "epochs={:s}, id_type={:s}"
        ).format(
            str(self.target_id),
            str(self.location),
            str(self.epochs),
            str(self.id_type),
        )

    def query(
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
        force_requery=False,
        query_type=None,
    ):

        """
        Query JPL Horizons for ephemerides.
        """

        # check for required information
        if self.target_id is None:
            raise ValueError("'id' parameter not set. Query aborted.")
        if self.location is None:
            self.location = "500@399"
        if self.epochs is None:
            self.epochs = Time.now().jd

        if query_type is None:
            query_type = self.query_type

        # assemble commandline based on self.id_type
        commandline = str(self.target_id)
        if self.id_type in [
            "designation",
            "name",
            "asteroid_name",
            "comet_name",
        ]:
            commandline = {
                "designation": "DES=",
                "name": "NAME=",
                "asteroid_name": "ASTNAM=",
                "comet_name": "COMNAM=",
            }[self.id_type] + commandline
        if self.id_type in [
            "smallbody",
            "asteroid_name",
            "comet_name",
            "designation",
        ]:
            commandline += ";"
            if isinstance(closest_apparition, bool):
                if closest_apparition:
                    commandline += " CAP;"
            else:
                commandline += " CAP{:s};".format(closest_apparition)
            if no_fragments:
                commandline += " NOFRAG;"

        request_payload = OrderedDict(
            [
                ("batch", 1),
                ("TABLE_TYPE", query_type),
                ("QUANTITIES", "'" + str(quantities) + "'"),
                ("COMMAND", '"' + commandline + '"'),
                (
                    "SOLAR_ELONG",
                    (
                        '"'
                        + str(solar_elongation[0])
                        + ","
                        + str(solar_elongation[1])
                        + '"'
                    ),
                ),
                ("LHA_CUTOFF", (str(max_hour_angle))),
                ("CSV_FORMAT", "YES"),
                ("CAL_FORMAT", "BOTH"),
                ("ANG_FORMAT", "DEG"),
                # NOTE TO MICHAEL FROM SELF:
                # that's a cute way to query values while assembling a literal
                (
                    "APPARENT",
                    ({False: "AIRLESS", True: "REFRACTED"}[refraction]),
                ),
                ("REF_SYSTEM", refsystem),
                ("EXTRA_PREC", {True: "YES", False: "NO"}[extra_precision]),
            ]
        )

        if isinstance(self.location, dict):
            if (
                "lon" not in self.location
                or "lat" not in self.location
                or "elevation" not in self.location
            ):
                raise ValueError(
                    ("'location' must contain lon, lat, " "elevation")
                )

            if "body" not in self.location:
                self.location["body"] = "399"
            request_payload["CENTER"] = "coord@{:s}".format(
                str(self.location["body"])
            )
            request_payload["COORD_TYPE"] = "GEODETIC"
            request_payload["SITE_COORD"] = "'{:f},{:f},{:f}'".format(
                self.location["lon"],
                self.location["lat"],
                self.location["elevation"],
            )
        else:
            request_payload["CENTER"] = "'" + str(self.location) + "'"

        if rate_cutoff is not None:
            request_payload["ANG_RATE_CUTOFF"] = str(rate_cutoff)

        # parse self.epochs
        if isinstance(self.epochs, (list, tuple, np.ndarray)):
            request_payload["TLIST"] = "\n".join(
                [str(epoch) for epoch in self.epochs]
            )
        elif isinstance(self.epochs, dict):
            if (
                "start" not in self.epochs
                or "stop" not in self.epochs
                or "step" not in self.epochs
            ):
                raise ValueError(
                    "'epochs' must contain start, " + "stop, step"
                )
            request_payload["START_TIME"] = (
                '"' + self.epochs["start"].replace("'", "") + '"'
            )
            request_payload["STOP_TIME"] = (
                '"' + self.epochs["stop"].replace("'", "") + '"'
            )
            request_payload["STEP_SIZE"] = (
                '"' + self.epochs["step"].replace("'", "") + '"'
            )
        else:
            # treat epochs as scalar
            request_payload["TLIST"] = str(self.epochs)

        if airmass_lessthan < 99:
            request_payload["AIRMASS"] = str(airmass_lessthan)

        if skip_daylight:
            request_payload["SKIP_DAYLT"] = "YES"
        else:
            request_payload["SKIP_DAYLT"] = "NO"

        self.request_payload = request_payload

        # don't re-fetch an identical request unless explicitly told to
        if reduce(
            and_,
            (
                self.response is not None,
                not force_requery,
                request_payload == self.request_payload,
            ),
        ):
            return self.response

        # set return_raw flag, if raw response desired

        # query and parse
        if self.session is None:
            active_session = requests.Session()
        else:
            active_session = self.session
        response = active_session.get(
            HORIZONS_SERVER,
            params=request_payload,
            timeout=TIMEOUT,
        )
        if self.session is None:
            active_session.close()
        self.uri = response.url
        self.response = response

        # check length of uri
        if len(self.uri) >= 2000:
            warnings.warn(
                (
                    "The uri used in this query is very long "
                    "and might have been truncated. The results of "
                    "the query might be compromised. If you queried "
                    "a list of epochs, consider querying a range."
                )
            )
        return response

    def table(self):
        if self.response is None:
            self.query()
        if "g:" in str(self.target_id):
            get_target_location = True
        else:
            get_target_location = False
        frame = make_horizon_dataframe(
            self.response.text, get_target_location=get_target_location
        )
        return frame

    def pointing(self):
        """
        make a dataframe of pointing-relevant information
        from Horizons response text. make tractable column names.
        also convert distance units from AU to m and arcseconds to degrees.
        """
        horizon_frame = self.table()
        au_to_m = (1 * u.au).to(u.m).value
        horizon_columns = {}
        # we have to use regex here because sometimes they
        # put extra underscores for spacing
        pointing_column_patterns = {
            r"Date_+\(UT\)": "time",
            r"Date_+JDUT": "jd",
            r"R.A.*\(ICRF\)": "ra_ast",  # astrometric ra
            r"DEC.*\(ICRF\)": "dec_ast",  # astrometric dec
            r"R.A.*\(rfct-app\)": "ra_app_r",
            # refracted apparent ra in weird frame?
            r"DEC.*\(rfct-app\)": "dec_app_r",
            # refracted apparent dec in weird frame?
            r"R.A.*\(a-app\)": "ra_app",  # airless apparent ra in weird frame?
            r"DEC.*\(a-app\)": "dec_app",
            # airless apparent dec in weird frame?
            r"RA.*\(ICRF-a-app\)": "ra_app_icrf",
            r"DEC.*\(ICRF-a-app\)": "dec_app_icrf",
            r"RA.*\(ICRF-r-app\)": "ra_app_icrf_r",
            r"DEC.*\(ICRF-r-app\)": "dec_app_icrf_r",
            r"Azi.*\(a-app\)": "az",
            r"Elev.*\(a-app\)": "alt",
            r"Azi.*\(r-appr\)": "az_r",
            r"Elev.*\(r-appr\)": "alt_r",
            "delta": "dist",
            "ObsSub-LON": "sub_lon",
            "ObsSub-LAT": "sub_lat",
            "SunSub-LON": "sub_lon",
            "SunSub-LAT": "sub_lat",
            "Ang-diam": "ang_diam",
            "T-O-M": "t_o_m",
            r"NP\.ang": "npa",
            "geo_lat": "geo_lat",
            "geo_lon": "geo_lon",
            "geo_el": "geo_el",
        }
        for pattern in pointing_column_patterns:
            matches = [
                col for col in horizon_frame.columns if re.match(pattern, col)
            ]
            # did we not ask for this quantity? move on
            if len(matches) == 0:
                continue
            # multiple matches? better fix something
            assert len(matches) == 1
            series = horizon_frame[matches[0]]
            output_name = pointing_column_patterns[pattern]
            if pattern == r"Date_+\(UT\)":
                horizon_columns[output_name] = pd.Series(
                    [dtp.parse(instant) for instant in series]
                )
            if pattern.startswith(
                (
                    "R.A.",
                    "DEC",
                    "Azi",
                    "Elev",
                    "RA",
                    "NP",
                )
            ):
                try:
                    float(series[0])
                except ValueError:
                    # generally "n. a." values for locations that
                    # apparent az / alt aren't
                    # meaningful for, like earth topocenter
                    continue
                try:
                    horizon_columns[output_name] = series.astype(np.float64)
                except ValueError:
                    # generally random spaces added after a minus sign
                    try:
                        horizon_columns[output_name] = series.str.replace(
                            " ", ""
                        ).astype(np.float64)
                    except ValueError:
                        # ok, something's actually wrong
                        raise
            if pattern == "delta":
                horizon_columns[output_name] = pd.Series(
                    [au_to_m * delta for delta in series.astype(np.float64)]
                )
            if pattern in ["ObsSub-LON", "ObsSub-LAT"]:
                horizon_columns[output_name] = series.astype(np.float64)
            if pattern == "Ang-diam":
                # convert from arcseconds to degree
                horizon_columns[output_name] = series.astype(np.float64) / 3600
            # only present for lunar ephemerides with selenographic coords
            # specified
            if pattern == "T-O-M":
                horizon_columns[output_name] = series.astype(np.float64)
            # only present for ephemerides with planetographic coords specified
            if pattern in ["geo_lat", "geo_lon", "geo_el"]:
                horizon_columns[output_name] = series.astype(np.float64)
        return pd.DataFrame(horizon_columns)


def get_lhorizon_moon(
    lunar_coords,
    time_series,
    observer_location=-1,
    query_options=None,
    session=None,
):
    """
    convenience method. gets lunar ephemerides from Horizons for arbitrary
    selenographic
    coordinates, observer location, and input time series. unlike
    get_horizon_moon_list(), this uses JPL Horizons' bulk epoch functionality
    to get ephemerides at many times in a single response. this is much, much
    faster, because JPL Horizons hates receiving hundreds of separate queries
    in quick succession. however, has the downside that it evenly spaces the
    sampled times across the interval defined by the time series, so there may
    be quantization errors if the series is also not evenly spaced. JPL
    will also reject epochs that space samples by fewer than 0.5 seconds.
    """

    if query_options is None:
        query_options = {}

    # format the selenographic position coordinate for horizons
    # 301 is horizons code for the moon
    # g: latitude, longitude, elevation is the prefix for planetodetic coords
    # @ is the separator between coordinates and body
    if lunar_coords is not None:
        lunar_location = "g: " + str(lunar_coords)[1:-1] + " @ 301"
    else:
        lunar_location = "301"

    # format time parameters for horizons:
    # start / stop are beginning and end as y-m-d h:m:s:mmm
    # step is number of samples, evenly spaced

    epochs = {
        "start": time_series[0],
        "stop": time_series[len(time_series) - 1],
        "step": str(len(time_series) - 1),
    }

    moon = LHorizon(
        target_id=lunar_location,
        id_type="id",
        location=observer_location,
        epochs=epochs,
        session=session,
    )
    moon.query(**query_options)

    return moon.pointing()


def moon_phase(moontime):
    """
    Time (in any astropy.time-parseable format) -> float giving moon phase in
    degrees at that time.
    """
    moontime = at.Time(moontime)
    epochs = {
        "start": str(moontime.utc),
        "stop": str((moontime + 1 * u.min).utc),
        "step": "1",
    }
    phased_moon = LHorizon(target_id=301, id_type="id", epochs=epochs)
    phased_moon.query(quantities=10)
    illum = phased_moon.table()
    # translate percentage to degrees
    phase = snorm(illum.iloc[0, 2], 0, 180, 0, 100)
    # are we before or after the full moon?
    if illum.iloc[0, 0] > illum.iloc[1, 0]:
        phase = 360 - phase
    return phase


# #####################
# bulk query helpers
# ####################
HORIZON_TIME_ABBREVIATION_DICT = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "y": 60 * 60 * 24 * 365,
}


def datetime_from_horizons_syntax(start, stop, step):
    return {
        "start": dtp.parse(start),
        "stop": dtp.parse(stop),
        "step size": HORIZON_TIME_ABBREVIATION_DICT[step[-1]] * int(step[:-1]),
    }


def estimate_line_count(start, stop, step):
    horizons_dt = datetime_from_horizons_syntax(start, stop, step)
    return math.ceil(
        (horizons_dt["stop"] - horizons_dt["start"]).total_seconds()
        / horizons_dt["step size"]
    )


def chunk_time(start, stop, step, chunk_size):
    horizons_dt = datetime_from_horizons_syntax(start, stop, step)
    chunks = chunked(range(estimate_line_count(start, stop, step)), chunk_size)
    times = []
    for chunk in chunks:
        start = horizons_dt["start"] + dt.timedelta(
            seconds=horizons_dt["step size"] * chunk[0]
        )
        stop = horizons_dt["start"] + dt.timedelta(
            seconds=horizons_dt["step size"] * chunk[-1]
        )
        times.append(
            {
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "step": step,
            }
        )
    return times


def construct_bulk_horizon_query(
    target_body_id,
    observer_body_id,
    start,
    stop,
    step,
    observer_coordinates=None,
    query_type="OBSERVER",
    chunksize=80000,
):

    session = requests.Session()
    if observer_coordinates is not None:
        observer_coordinates["body"] = observer_body_id
    partial_observation = partial(
        LHorizon,
        target_id=target_body_id,
        location=observer_coordinates,
        id_type="id",
        session=session,
        query_type=query_type,
    )
    return [
        partial_observation(epochs=chunk)
        for chunk in chunk_time(start, stop, step, chunksize)
    ]


def fetch_bulk_pointing_table(bulk_horizon_query):
    for horizon_query in bulk_horizon_query:
        horizon_query.query()
        print(
            "collected data from "
            + horizon_query.epochs["start"]
            + " to "
            + horizon_query.epochs["stop"]
        )
    print("concatenating all data")
    return pd.concat(
        [horizon_query.pointing() for horizon_query in bulk_horizon_query]
    )


def fetch_bulk_generic(bulk_horizon_query):
    for horizon_query in bulk_horizon_query:
        horizon_query.query()
        print(
            "collected data from "
            + horizon_query.epochs["start"]
            + " to "
            + horizon_query.epochs["stop"]
        )
    print("concatenating all data")
    return pd.concat(
        [horizon_query.table() for horizon_query in bulk_horizon_query]
    )
