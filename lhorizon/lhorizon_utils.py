import re
from collections.abc import Sequence
from functools import reduce
from operator import or_
from typing import Any, Optional, Pattern, Union

import astropy.time as at
import dateutil.parser as dtp
import numpy as np
import pandas as pd
import pandas.api.types
import requests
from numpy.linalg import norm
from numpy.typing import ArrayLike

from lhorizon import config as config


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


# TODO: make this better at handling pre-1960 dates
def convert_to_jd(epochs: Sequence) -> list[float]:
    """
    convert passed epochs to jd. may currently raise warnings for dates prior
    to 1960 due to some astropy.Time corner cases involving leap seconds.
    """
    epochs = listify(epochs)
    # # astropy uses a nonstandard iso format with no T separator
    # if isinstance(epochs[0], str):
    #     if "T" in epochs[0]:
    #         epochs = [epoch.replace("T", " ") for epoch in epochs]
    # coerce iterable / scalar iso or dt inputs to jd
    scale = "utc"
    try:
        parsed_epochs = [float(epoch) for epoch in epochs]
        at_format = "jd"
    except ValueError:
        parsed_epochs = [dtp.parse(epoch) for epoch in epochs]
        utc_cutoff = dtp.parse("1960-01-01")
        if any([epoch < utc_cutoff for epoch in parsed_epochs]):
            scale = "tai"
        at_format = "datetime"
    return at.Time(parsed_epochs, format=at_format, scale=scale).jd


def numeric_columns(data: pd.DataFrame) -> list[str]:
    """return a list of all numeric columns of a DataFrame"""
    return [
        col
        for col in data.columns
        if pandas.api.types.is_numeric_dtype(data[col])
    ]


def utc_to_et(utc):
    """convert UTC -> 'seconds since J2000' format preferred by SPICE"""
    return (at.Time(utc) - at.Time("J2000")).sec


def utc_to_jd(utc):
    """convert UTC string -> jd string -- for horizons or whatever"""
    return at.Time(utc).jd


def is_it(*types):
    """partially-evaluated predicate form of isinstance"""

    def it_is(whatever):
        return isinstance(whatever, types)

    return it_is


def sph2cart(
    lat: Union[float, ArrayLike],
    lon: Union[float, ArrayLike],
    radius: Union[float, ArrayLike] = 1,
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
    x0: Union[float, ArrayLike],
    y0: Union[float, ArrayLike],
    z0: Union[float, ArrayLike],
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
