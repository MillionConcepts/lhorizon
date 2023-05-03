import datetime as dt
import re
from collections.abc import Callable, Iterable, Sequence
from functools import reduce, partial, wraps
from itertools import starmap
from operator import or_, and_, contains
from telnetlib import Telnet
from typing import Any, Optional, Pattern, Union, Iterator

import numpy as np
import pandas as pd
import pandas.api.types
import requests
from erfa import cal2jd, taitt, utctai, dtdb
from numpy.linalg import norm

from lhorizon import config as config
from lhorizon._type_aliases import Array
from lhorizon.constants import J2000_TDB


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


def is_it(*types: type) -> Callable[[Any], bool]:
    """partially-evaluated predicate form of `isinstance`"""

    def it_is(whatever: Any):
        return isinstance(whatever, types)

    return it_is


def numeric_columns(data: pd.DataFrame) -> list[str]:
    """return a list of all numeric columns of a DataFrame"""
    return [
        col
        for col in data.columns
        if pandas.api.types.is_numeric_dtype(data[col])
    ]


LHORIZON_STRFTIME_MAPPING = {
    r'.*Date.*(?=HR)': '%Y-%b-%d ',
    r'HR': '%H',
    r'MN': '%M',
    r'SC': '%S',
    r'fff': '%f'
}


def convert_horizons_date_spec_to_strftime(date_spec):
    for k, v in LHORIZON_STRFTIME_MAPPING.items():
        date_spec = re.sub(k, v, date_spec)
    return date_spec


def _cast_timeseries(obj: Any):
    """
    pass any scalar or iterable interpretable by pandas as timestamp(s),
    get a datetime64 series back
    """
    if isinstance(obj, (pd.Series, np.ndarray)):
        if obj.dtype.kind != 'M':
            return obj.astype('datetime64[ns]')
        return obj
    return pd.Series(listify(obj)).astype("datetime64[ns]")


def timecast(func: Callable[[Any], pd.Series], recast=True):
    @wraps(func)
    def cast_recast(obj):
        _intype = type(obj)
        result = func(_cast_timeseries(obj))
        if recast is False:
            return result
        if isinstance(result, _intype):
            return result
        if "__iter__" not in dir(_intype):
            return result.iloc[0]
        if _intype is np.ndarray:
            return result.values
        if _intype is str:
            return str(result.iloc[0])
        if _intype is list:
            return result.tolist()
        if _intype is tuple:
            return tuple(result.tolist())
        # sorry!
        return result
    return cast_recast


def _jd_parts(time_series: pd.Series):
    """convert pandas time series to julian day number."""
    # erfa splits julian dates into two parts. first part is always 240000.5
    djm0, djm = cal2jd(
        time_series.dt.year, time_series.dt.month, time_series.dt.day
    )
    time_of_day = (time_series - time_series.dt.normalize())
    day_fraction = time_of_day / pd.Timedelta("1 day")
    return djm0, djm, day_fraction
    # note that djm0 + djm + day_fraction now gives JD in UT


@timecast
def utc_to_jd(utc_time: Any):
    """converts passed utc time or times to julian day number"""
    time_series = _cast_timeseries(utc_time)
    return sum(_jd_parts(time_series))


def utc_tdb_offset(time_series: pd.Series):
    """
    return offset between utc and tdb at each point of passed pandas time
    series in seconds
    """
    djm0, djm, day_fraction = _jd_parts(time_series)
    _, djm_tt = taitt(djm0, utctai(djm0, djm + day_fraction)[1])
    # assumes 0 longitude, no offset from earth spin axis, positioned on
    # equatorial plane. resulting errors from these assumptions should be
    # very very small.
    # note that for whatever reason, dtdb wants day fraction in UT.
    delta0 = dtdb(djm0.values, djm.values, day_fraction.values, 0, 0, 0)
    # first part is tt day fraction
    return (djm_tt - djm - day_fraction) * 60 * 60 * 24 + delta0


@timecast
def utc_to_tdb(utc_time: Any):
    """
    convert passed utc time or times to tdb (Horizons' preferred timescale
    for vector queries). does not account for observer position.
    """
    return utc_time + pd.to_timedelta(utc_tdb_offset(utc_time), "second")


@timecast
def tdb_to_et(tdb_time: Any):
    """
    convert time(s) in TDB to ET, 'ephemeris time' -- absolute seconds since
    J2000 -- the timescale preferred by SPICE.
    """
    return (tdb_time - J2000_TDB) / pd.Timedelta("1s")


def utc_to_et(utc_time: Any):
    """
    convert times in UTC to ET, 'ephemeris time' -- absolute seconds since
    J2000 -- the timescale preferred by SPICE.
    """
    return (utc_to_tdb(utc_time) - J2000_TDB) / pd.Timedelta("1s")


def sph2cart(
    lat: Union[float, Array],
    lon: Union[float, Array],
    radius: Union[float, Array] = 1,
    unit: str = "degrees",
    as_df=False
) -> Union[pd.DataFrame, tuple]:
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
    if as_df is True:
        return pd.DataFrame({"x": x0, "y": y0, "z": z0})
    return x0, y0, z0


def cart2sph(
    x0: Union[float, Array],
    y0: Union[float, Array],
    z0: Union[float, Array],
    unit: str = "degrees",
    as_df=False
) -> Union[pd.DataFrame, tuple]:
    """
    convert cartesian to spherical coordinates. returns degrees by default;
    pass unit="radians" to return radians. if passed any arraylike objects,
    returns lat, lon, radius as tuple of ndarrays; otherwise, as tuple of floats.

    caveats:
    1. this assumes a coordinate convention in which latitude runs from -90
        to 90 degrees.
    2. returns longitude in strictly positive coordinates.
    """
    radius = np.sqrt(x0 ** 2 + y0 ** 2 + z0 ** 2)
    longitude = np.arctan2(y0, x0) % (np.pi * 2)
    latitude = np.arcsin(z0 / radius)
    if unit == "degrees":
        latitude, longitude = map(np.degrees, (latitude, longitude))
    if as_df is True:
        return pd.DataFrame({'lat': latitude, 'lon': longitude, 'r': radius})
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
