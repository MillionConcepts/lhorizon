import datetime as dt
from itertools import starmap
from telnetlib import Telnet

import pytz
import re
from collections.abc import Callable, Iterable, Sequence
from functools import reduce, partial
from math import floor
from operator import or_, and_, contains
from typing import Any, Optional, Pattern, Union, Iterator

import dateutil.parser as dtp
import numpy as np
import pandas as pd
import pandas.api.types
import requests
from numpy.linalg import norm

from lhorizon import config as config
from lhorizon._type_aliases import Array, Timelike
from lhorizon.constants import LEAP_SECOND_THRESHOLDS, DT_J2000_TDB


def listify(thing: Any) -> list:
    """Always a list, for things that want lists. use with care."""
    if isinstance(thing, str) or (
        (not isinstance(thing, Sequence) and (not isinstance(thing, Iterable)))
    ):
        return [thing]
    return list(thing)


def snorm(
    thing: Any,
    minimum: float = 0,
    maximum: float = 1,
    m0: Optional[float] = None,
    m1: Optional[float] = None,
) -> Union[list[float], float]:
    """
    simple min-max scaler. minimum and maximum are the limits of the range of
    the returned sequence. m1 and m2 are optional parameters that specify
    floor and ceiling values for the input other than its actual minimum and
    maximum. If a single value is passed for thing, returns a float;
    otherwise, returns a sequence of floats.
    """
    thing = listify(thing)
    if m0 is None:
        m0 = min(thing)
    if m1 is None:
        m1 = max(thing)
    scale = (maximum - minimum) / (m1 - m0)
    shift = minimum - m0 * scale
    scaled = [x * scale + shift for x in thing]
    if len(scaled) == 1:
        return scaled[0]
    return scaled


def hunt_csv(regex: Pattern, body: str) -> list:
    """
    finds chunk of csv in a larger string defined as regex, splits it,
    and returns as list. really useful only for single lines.
    worse than StringIO -> numpy or pandas csv reader in other cases.
    """
    csv_string = re.search(regex, body)[0]
    if are_in(["\r", "\n"], or_)(csv_string):
        lines = re.split(r"[\r\n]+", csv_string)
        processed_lines = []
        for line in lines:
            csv_fields = line.split(",")
            csv_fields = [field.strip() for field in csv_fields]
            processed_lines.append(csv_fields)
        return processed_lines
    csv_fields = csv_string.split(",")
    return [field.strip() for field in csv_fields]


def are_in(items: Iterable, oper: Callable = and_) -> Callable:
    """
    iterable -> function
    returns function that checks if its single argument contains all
    (or by changing oper, perhaps any) items
    """

    def in_it(container: Iterable) -> bool:
        inclusion = partial(contains, container)
        return reduce(oper, map(inclusion, items))

    return in_it


def is_it(*types: type) -> Callable[Any, bool]:
    """partially-evaluated predicate form of `isinstance`"""

    def it_is(whatever: Any):
        return isinstance(whatever, types)

    return it_is


def utc_to_tt_offset(time: dt.datetime) -> float:
    """
    return number of seconds necessary to advance UTC
    to TT. we aren't presently supporting dates prior to 1972
    because fractional leap second handling is another thing.
    """
    if time.year < 1972:
        raise ValueError("dates prior to 1972 are not currently supported")
    # this includes the horrible fractional leap seconds prior to 1972
    # and the base 32.184s offset between TAI and TT
    offset = 42.184
    for threshold in LEAP_SECOND_THRESHOLDS:
        if time > threshold:
            offset += 1
    return offset


def utc_to_tdb(time: Union[dt.datetime, str]) -> dt.datetime:
    """
    return time in tdb / jpl horizons coordinate time from passed time in utc.
    may in some cases be closer to tt, but offset should be no more than 2 ms
    in the worst case. only works for times after 1972 because of fractional
    leap second handling. strings are assumed to be in UTC+0. passed datetimes
    must be timezone-aware.
    """
    if isinstance(time, str):
        utc = pytz.timezone("UTC")
        time = utc.localize(dtp.parse(time))
    offset = dt.timedelta(seconds=utc_to_tt_offset(time))
    return (offset + time).replace(tzinfo=None)


def dt_to_jd(time: Union[dt.datetime, pd.Series]) -> Union[float, pd.Series]:
    """
    convert passed datetime or Series of datetime to julian day number (jd).
    algorithm derived from Julian Date article on scienceworld.wolfram.com,
    itself based on Danby, J. M., _Fundamentals of Celestial Mechanics_
    """
    # use accessor on datetime series
    if isinstance(time, pd.Series):
        time = time.dt
    y, m, d = time.year, time.month, time.day
    h = time.hour + time.minute / 60 + time.second / 3600
    return sum(
        [
            367 * y,
            -1 * floor(7 * (y + floor((m + 9) / 12)) / 4),
            -1 * floor(3 * (floor((y + (m - 9) / 7) / 100) + 1) / 4),
            floor(275 * m / 9) + d + 1721028.5,
            h / 24,
        ]
    )


def numeric_columns(data: pd.DataFrame) -> list[str]:
    """return a list of all numeric columns of a DataFrame"""
    return [
        col
        for col in data.columns
        if pandas.api.types.is_numeric_dtype(data[col])
    ]


def produce_jd_series(
    epochs: Union[Timelike, Sequence[Timelike]]
) -> pd.Series:
    """
    convert passed epochs to julian day number (jd). scale is assumed to be
    utc. this may of course produce very slightly spurious results for dates
    in the future for which leap seconds have not yet been assigned. floats or
    floatlike strings will be interpreted as jd and not modified. inputs of
    mixed time formats or scales will likely produce undesired behavior.
    """

    if not isinstance(epochs, pd.Series):
        epochs = listify(epochs)
        epochs = pd.Series(epochs)
    try:
        return epochs.astype(float)
    except (ValueError, TypeError):
        return dt_to_jd(epochs.astype("datetime64"))


def time_series_to_et(
    time_series: Union[
        str, Sequence[str], dt.datetime, Sequence[dt.datetime], pd.Series
    ]
) -> pd.Series:
    """
    convert time -> 'seconds since J2000' epoch scale preferred by SPICE.
    accepts anything `pandas` can cast to Series and interpret as datetime.
    if not timezone-aware, assumes input is in UTC.
    """
    if not isinstance(time_series, pd.Series):
        time_series = pd.Series(listify(time_series))
    time_series = time_series.astype("datetime64")
    if time_series.iloc[0].tzinfo is None:
        utc = pytz.timezone("UTC")
        time_series = time_series.map(utc.localize)
    tdb_times = time_series.map(utc_to_tdb)
    return (tdb_times - DT_J2000_TDB).dt.total_seconds()


def sph2cart(
    lat: Union[float, Array],
    lon: Union[float, Array],
    radius: Union[float, Array] = 1,
    unit: str = "degrees",
):
    """
    convert spherical to cartesian coordinates. assumes input is in degrees
    by default; pass unit="radians" to specify input in radians. if passed any
    arraylike objects, returns a DataFrame, otherwise, returns a tuple of
    values.

    caveats:
    1. this assumes a coordinate convention in which latitude runs from -90
        to 90 degrees.
    """
    if unit == "degrees":
        lat = np.radians(lat)
        lon = np.radians(lon)
    x0 = radius * np.cos(lat) * np.cos(lon)
    y0 = radius * np.cos(lat) * np.sin(lon)
    z0 = radius * np.sin(lat)

    if reduce(
        or_,
        map(is_it(pd.DataFrame, np.ndarray, pd.Series), [lat, lon, radius]),
    ):
        return pd.DataFrame({"x": x0, "y": y0, "z": z0})
    return x0, y0, z0


def cart2sph(
    x0: Union[float, Array],
    y0: Union[float, Array],
    z0: Union[float, Array],
    unit: str = "degrees",
) -> Union[pd.DataFrame, tuple]:
    """
    convert cartesian to spherical coordinates. returns degrees by default;
    pass unit="radians" to return radians. if passed any arraylike objects,
    returns a DataFrame, otherwise, returns a tuple of values.

    caveats:
    1. this assumes a coordinate convention in which latitude runs from -90
        to 90 degrees.
    2. returns longitude in strictly positive coordinates.
    """
    radius = np.sqrt(x0 ** 2 + y0 ** 2 + z0 ** 2)
    if x0 != 0:
        longitude = np.arctan2(y0, x0)
    else:
        longitude = np.pi / 2
    longitude = longitude % (np.pi * 2)
    latitude = np.arcsin(z0 / np.sqrt(x0 ** 2 + y0 ** 2 + z0 ** 2))
    if unit == "degrees":
        latitude = np.degrees(latitude)
        longitude = np.degrees(longitude)
    if reduce(
        or_, map(is_it(pd.DataFrame, np.ndarray, pd.Series), [x0, y0, z0])
    ):
        return pd.DataFrame({"lat": latitude, "lon": longitude, "r": radius})
    return latitude, longitude, radius


def hats(
    vectors: Union[np.ndarray, pd.DataFrame, pd.Series]
) -> Union[np.ndarray, pd.DataFrame, pd.Series]:
    """
    convert an array of passed "vectors" (row-wise-stacked sequences of
    floats) to unit vectors
    """
    norms = np.linalg.norm(vectors, axis=-1)
    return vectors / np.array(norms)[..., None]


def make_raveled_meshgrid(
    axes: Sequence[np.ndarray], axis_names: Optional[Sequence[str, int]] = None
):
    """
    produces a flattened, indexed version of a 'meshgrid' (a cartesian
    product of axes standing in for a vector space, conventionally produced
    by numpy.meshgrid)
    """
    if axis_names is None:
        axis_names = [str(ix) for ix in range(len(axes))]
    assert len(axes) == len(axis_names)
    axis_len = axes[0].shape[0]
    index_mesh = np.meshgrid(*[np.arange(axis_len) for _ in axes])
    meshgrid = np.meshgrid(*[axis for axis in axes])
    indices = {
        axis_names[ix] + "_ix": np.ravel(index_mesh[ix])
        for ix, _ in enumerate(axes)
    }
    grids = {
        axis_names[ix]: np.ravel(grid) for ix, grid in enumerate(meshgrid)
    }
    return pd.DataFrame(grids | indices)


def default_lhorizon_session() -> requests.Session:
    """returns a requests.Session object with default `lhorizon` options"""
    session = requests.Session()
    session.headers = config.DEFAULT_HEADERS
    session.stream = False
    return session


def open_noninteractive_jpl_telnet_connection() -> Telnet:
    jpl = Telnet()
    jpl.open("ssd.jpl.nasa.gov", 6775)
    jpl.read_until(b"|_____|/  |_|/       |_____|/ ")
    return jpl


def perform_telnet_exchange(
    message: bytes, read_until_this: bytes, connection: Telnet
) -> bytes:
    """
    send message via connection, block until read_until_this is received
    or connection's timeout is met, and return all input up to encounter
    with read_until_this.
    """
    connection.write(message)
    return connection.read_until(read_until_this)


def have_telnet_conversation(
    conversation_structure: Sequence[tuple[bytes, bytes]],
    connection: Telnet,
    lazy: bool = False,
) -> Union[Iterator, tuple[bytes]]:
    """
    perform a series of noninteractive telnet exchanges via connection
    and return the output of those exchanges.

    if lazy is True, return the conversation as an iterator that
    performs and yields the output of each exchange when incremented.
    """
    converse = partial(perform_telnet_exchange, connection=connection)
    conversation = starmap(converse, conversation_structure)
    if lazy:
        return conversation
    lines = tuple(conversation)
    connection.close()
    return lines
