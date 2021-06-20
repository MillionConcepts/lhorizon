import datetime as dt
import re
from collections.abc import Sequence
from functools import reduce
from math import floor
from operator import or_
from typing import Any, Optional, Pattern, Union

import numpy as np
import pandas as pd
import pandas.api.types
import requests
from numpy.linalg import norm

from lhorizon import config as config
from lhorizon._type_aliases import Array, Timelike


def listify(thing: Any) -> list:
    """Always a list, for things that want lists. use with care."""
    if isinstance(thing, str) or (not isinstance(thing, Sequence)):
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


LEAP_SECOND_THRESHOLDS = [
    dt.datetime(1972, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1972, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1973, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1974, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1975, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1976, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1977, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1978, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1979, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1981, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1982, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1983, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1985, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1987, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1989, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1990, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1992, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1993, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1994, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1995, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1997, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1998, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(2005, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(2008, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(2012, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(2015, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(2016, 12, 31, tzinfo=dt.timezone.utc)
]


def dt_to_jd(time: Union[dt.datetime, pd.Series]) -> Union[float, pd.Series]:
    """
    convert passed datetime or Series of datetime to julian day number (jd).
    algorithm derived from Julian Date article on scienceworld.wolfram.com,
    itself based on Danby, J. M., Fundamentals of Celestial Mechanics
    """
    # use accessor on datetime series
    if isinstance(time, pd.Series):
        time = time.dt
    y, m, d = time.year, time.month, time.day
    h = time.hour + time.minute / 60 + time.second / 3600
    return sum([
        367 * y,
        -1 * floor(7 * (y + floor((m + 9) / 12)) / 4),
        -1 * floor(3 * (floor((y + (m - 9) / 7) / 100) + 1) / 4),
        floor(275 * m / 9) + d + 1721028.5,
        h / 24
    ])


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


DT_J2000 = dt.datetime(2000, 1, 1, 11, 58, 55, 816000)


def time_series_to_et(time_series):
    """
    convert time -> 'seconds since J2000' epoch scale preferred by SPICE --
    anything pandas
    """
    if not isinstance(time_series, pd.Series):
        time_series = pd.Series(listify(time_series))
    return (time_series.astype("datetime64") - DT_J2000).dt.total_seconds()


def is_it(*types):
    """partially-evaluated predicate form of isinstance"""

    def it_is(whatever):
        return isinstance(whatever, types)

    return it_is


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
    """
    radius = np.sqrt(x0 ** 2 + y0 ** 2 + z0 ** 2)
    longitude = np.arctan(y0 / x0)
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
