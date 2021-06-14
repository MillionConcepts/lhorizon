import re
from collections.abc import Sequence
from functools import reduce
from operator import or_
from typing import Any, Union

import astropy.time as at
import numpy as np
import pandas as pd
import pandas.api.types
import requests
from numpy.linalg import norm

from lhorizon import config as config


def listify(thing: Any) -> list:
    """Always a list, for things that want lists"""
    if isinstance(thing, str) or (not isinstance(thing, Sequence)):
        return [thing]
    return list(thing)


def snorm(thing, minimum=0, maximum=1, m0=None, m1=None):
    """simple min-max scaler"""
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


def hunt_csv(regex, body):
    """
    finds chunk of csv in a larger text file defined as regex, splits it,
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


def convert_to_jd(epochs):
    epochs = listify(epochs)
    # astropy uses a nonstandard iso format with no T separator
    if isinstance(epochs[0], str):
        if "T" in epochs[0]:
            epochs = [epoch.replace("T", " ") for epoch in epochs]
    # coerce iterable / scalar iso or dt inputs to jd
    is_not_jd = True
    formats = ["jd", "iso", "datetime"]
    while is_not_jd:
        try:
            form = formats.pop()
            epochs = at.Time(epochs, format=form).jd
            is_not_jd = False
        except (ValueError, TypeError, ArithmeticError) as ex:
            if len(formats) == 0:
                raise ex
    return epochs


def numeric_columns(data: pd.DataFrame) -> list[str]:
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


def sph2cart(latitude, longitude, radius=1, unit="degrees"):
    if unit == "degrees":
        latitude = np.radians(latitude)
        longitude = np.radians(longitude)
    x0 = radius * np.cos(latitude) * np.cos(longitude)
    y0 = radius * np.cos(latitude) * np.sin(longitude)
    z0 = radius * np.sin(latitude)

    if reduce(
        or_, map(is_it(pd.DataFrame, pd.Series), [latitude, longitude, radius])
    ):
        return pd.DataFrame({"x": x0, "y": y0, "z": z0})
    return x0, y0, z0


def is_it(*types):
    def it_is(whatever):
        return isinstance(whatever, types)

    return it_is


def cart2sph(x0, y0, z0, unit="degrees"):
    radius = np.sqrt(x0 ** 2 + y0 ** 2 + z0 ** 2)
    longitude = np.arctan(y0 / x0)
    latitude = np.arcsin(z0 / np.sqrt(x0 ** 2 + y0 ** 2 + z0 ** 2))
    if unit == "degrees":
        latitude = np.degrees(latitude)
        longitude = np.degrees(longitude)
    if reduce(or_, map(is_it(pd.DataFrame, pd.Series), [x0, y0, z0])):
        return pd.DataFrame({"lat": latitude, "lon": longitude, "r": radius})
    return latitude, longitude, radius


def hats(vectors: Union[np.ndarray, pd.DataFrame]):
    norms = np.linalg.norm(vectors, axis=-1)
    return vectors / np.array(norms)[..., None]


def make_raveled_meshgrid(axes, axis_names):
    assert len(axes) == len(axis_names)
    axis_len = axes[0].shape[0]
    index_mesh = np.meshgrid(*[np.arange(axis_len) for _ in axes])
    meshgrid = np.meshgrid(*[axis for axis in axes])
    indices = {
        axis_names[ix] + "_ix": np.ravel(index_mesh[ix]) for ix, _ in enumerate(axes)
    }
    grids = {
        axis_names[ix]: np.ravel(grid) for ix, grid in enumerate(meshgrid)
    }
    return pd.DataFrame(grids | indices)


def default_lhorizon_session():
    session = requests.Session()
    session.headers = config.DEFAULT_HEADERS
    session.stream = False
    return session
