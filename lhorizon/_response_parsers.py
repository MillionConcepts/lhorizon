"""
helper functions for parsing response text from the JPL Horizons API.
these functions are intended to be called by LHorizon methods and should
generally not be called directly.
"""
import json
import re
import warnings
from io import StringIO
from typing import Optional

import numpy as np
import pandas as pd
from dateutil import parser as dtp
from pandas._libs import OutOfBoundsDatetime

from lhorizon.config import TABLE_PATTERNS, VISIBILITY_FLAG_NAMES
from lhorizon.constants import AU_TO_M
from lhorizon.lhorizon_utils import hunt_csv, \
    convert_horizons_date_spec_to_strftime
from lhorizon._type_aliases import Array

# delimiters for column and data sections
# 'JDTDB' begins the vectors columns; 'Date' begins the observer columns
HORIZON_COLUMN_SEARCH = re.compile(r"(Date|JDTDB).*(?=\n\*+)")
HORIZON_DATA_SEARCH = re.compile(r"\$\$SOE\n(.*)\$\$EOE", re.DOTALL)
GEODETIC_SEARCH = re.compile(r"(?<=Target geodetic : )\.?\d.*(?= {)")


class HorizonsReturnedError(ValueError):
    pass


def make_lhorizon_dataframe(
    jpl_response: str, topocentric_target: bool = False
) -> pd.DataFrame:
    """
    make a DataFrame from Horizons API response JSON.
    """
    data = None
    try:
        # load JSON and extract result section
        jpl_result = json.loads(jpl_response)['result']
        # grab these sections and write them into a string buffer:
        # find bounds of column / data in response & strip spaces from columns
        data = re.search(HORIZON_DATA_SEARCH, jpl_result).group(1)
        columns = re.search(
            HORIZON_COLUMN_SEARCH, jpl_result
        )[0].replace(" ", "")
    except (TypeError, AttributeError):
        if data is not None:
            raise HorizonsReturnedError(data)
        raise ValueError(
            "Couldn't parse either usable data or error an message from "
            "Horizons response."
        )
    data_buffer = StringIO()
    data_buffer.write(columns + "\n" + data)
    data_buffer.seek(0)
    # read this buffer as csv
    horizon_dataframe = pd.read_csv(
        data_buffer, sep=",", engine="c", low_memory=False
    )
    # horizons ends lines w/commas, so pandas creates an empty trailing column
    horizon_dataframe = horizon_dataframe.iloc[:, :-1]
    horizon_dataframe = clean_visibility_flags(horizon_dataframe)
    # if appropriate, add target's geodetic coordinates
    if topocentric_target:
        target_geodetic_coords = hunt_csv(GEODETIC_SEARCH, jpl_result)
        horizon_dataframe["geo_lon"] = target_geodetic_coords[0]
        horizon_dataframe["geo_lat"] = target_geodetic_coords[1]
        horizon_dataframe["geo_el"] = target_geodetic_coords[2]
    for c in horizon_dataframe.columns:
        if ('(ut)' in c.lower()) or ('(tdb)' in c.lower()):
            horizon_dataframe[c] = horizon_dataframe[c].str.strip()
    return horizon_dataframe


def clean_visibility_flags(horizon_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    assign names to unlabeled 'visibility flag' columns -- solar presence,
    lunar/interfering body presence, is-target-on-near-side-of-parent-body,
    is-target-illuminated; drop then if empty
    """
    flag_mapping = {
        unlabeled_flag: flag_name
        for unlabeled_flag, flag_name in zip(
            [c for c in horizon_dataframe.columns if 'Unnamed' in c],
            VISIBILITY_FLAG_NAMES
        )
    }
    horizon_dataframe = horizon_dataframe.rename(mapper=flag_mapping, axis=1)
    empty_flags = []
    for flag_column in flag_mapping.values():
        if horizon_dataframe[flag_column].isin([' ', '']).all():
            empty_flags.append(flag_column)
    return horizon_dataframe.drop(empty_flags, axis=1)


def clean_up_vectors_series(pattern: str, series: Array) -> pd.Series:
    """
    regularize units, format text, and parse dates in a VECTORS table column
    """
    # convert km to m
    if pattern in ("X", "Y", "Z", "VX", "VY", "VZ", "RG", "RR", "LT"):
        return pd.Series(series.astype(np.float64) * 1000)
    # parse ISO dates
    if pattern == r"Calendar":
        # they put AD/BC on these
        return pd.Series([dtp.parse(instant[5:]) for instant in series])
    warnings.warn(f"unhandled VECTORS column {pattern}")


class OOBTimeWarning(UserWarning):
    pass


def clean_up_observer_series(
    pattern: str, series: Array
) -> Optional[pd.Series]:
    """
    regularize units, format text, and parse dates in an OBSERVER table column
    """
    if pattern in VISIBILITY_FLAG_NAMES:
        return series
    if pattern == r"Date_+\(UT\)":
        try:
            return pd.to_datetime(
                series,
                format=convert_horizons_date_spec_to_strftime(series.name)
            )
        except (ValueError, OutOfBoundsDatetime) as err:
            if (
                not isinstance(err, OutOfBoundsDatetime)
                and 'time data "b' not in str(err)
            ):
                raise
            warnings.warn(
                "This result contains dates outside of Pandas's "
                "supported Timestamp range, so the 'time' column of the "
                "output of table() will contain strings rather than "
                "Timestamps. Pass ignore_oob_time=True to the LHorizon "
                "constructor to suppress this warning.",
                OOBTimeWarning
            )
            return series
    if pattern == "delta":
        return pd.Series(
            [AU_TO_M * delta for delta in series.astype(np.float64)]
        )
    if pattern == "Ang-diam":
        # convert from arcseconds to degrees
        return series.astype(np.float64) / 3600
    # generic behavior
    if isinstance(series.iloc[0], str):
        # "n. a." values for locations that this quantity is not
        # meaningful or calculable wrt this query
        if "n." in series.iloc[0]:
            return
    try:
        return series.astype(np.float64)
    except ValueError:
        # generally random spaces added after a minus sign
        return series.str.replace(" ", "").astype(np.float64)


def clean_up_series(query_type: str, pattern: str, series: Array) -> pd.Series:
    """
    dispatch function for Horizons column cleanup functions
    """
    if query_type == "OBSERVER":
        return clean_up_observer_series(pattern, series)
    if query_type == "VECTORS":
        return clean_up_vectors_series(pattern, series)


def polish_lhorizon_dataframe(
    horizon_frame: pd.DataFrame, query_type: str
) -> pd.DataFrame:
    """
    make a nicely-formatted table from a dataframe generated by
    make_lhorizon_dataframe. make tractable column names. also convert
    distance units from AU or km to m and arcseconds to degrees.
    """
    horizon_columns = {}
    # we have to use regex here because sometimes Horizons adds extra
    # underscores for visual spacing, using what appears to be a pretty
    # complicated decision tree
    for pattern, repl in TABLE_PATTERNS[query_type].items():
        matches = [
            col for col in horizon_frame.columns if re.match(pattern, col)
        ]
        # did we not ask for this quantity? move on
        if len(matches) == 0:
            continue
        # multiple matches? better fix something
        assert len(matches) == 1
        series = horizon_frame[matches[0]]
        cleaned_result = clean_up_series(query_type, pattern, series)
        if cleaned_result is None:
            continue
        horizon_columns[repl] = cleaned_result
    return pd.DataFrame(horizon_columns)
