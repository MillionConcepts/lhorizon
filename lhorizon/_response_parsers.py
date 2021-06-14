import re
from io import StringIO

import numpy as np
import pandas as pd
from astropy import units as u
from dateutil import parser as dtp

from lhorizon.lhorizon_utils import hunt_csv
from lhorizon.config import TABLE_PATTERNS


def make_horizon_dataframe(raw_horizon_response, get_target_location=False):
    """make a pandas dataframe from a raw horizon response."""

    # delimiters for column and data sections
    # 'JDTDB' begins the vectors columns; 'Date' begins the observer columns
    horizon_column_search = re.compile(r"(Date|JDTDB).*(?=\n\*+)")
    horizon_data_search = re.compile(
        r"(?<=\$\$SOE\n)(.|\n)*?(\d\d\d\d(.|\n)*)(?=\$\$EOE)"
    )

    # grab these sections and write them into a string buffer
    try:
        columns = re.search(horizon_column_search, raw_horizon_response)[0]
        data = re.search(horizon_data_search, raw_horizon_response).group(2)
    except TypeError:
        raise ValueError(
            "Horizons didn't return a table of data or it couldn't be parsed "
            "as CSV; check the contents of the response to see why."
        )
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


def clean_up_vectors_series(pattern, series):
    # convert km to m
    if pattern in (r"X", r"Y", r"Z", r"VX", r"VY", r"VZ", r"RG", r"RR"):
        return pd.Series(series.astype(np.float64) * 1000)
    # parse ISO dates
    if pattern == r"Calendar Date":
        # they put AD/BC on these
        return pd.Series([dtp.parse(instant[3:]) for instant in series])


def clean_up_observer_series(pattern, series):
    if pattern == r"Date_+\(UT\)":
        return pd.Series([dtp.parse(instant) for instant in series])
    if pattern.startswith(("R.A.", "DEC", "Azi", "Elev", "RA", "NP")):
        if isinstance(series.iloc[0], str):
            # generally "n. a." values for locations that apparent az
            # / alt aren't meaningful for, like earth topocenter
            if "n" in series.iloc[0]:
                return
        try:
            return series.astype(np.float64)
        except ValueError:
            # generally random spaces added after a minus sign
            return series.str.replace(" ", "").astype(np.float64)

    if pattern == "delta":
        au_to_m = (1 * u.au).to(u.m).value
        return pd.Series(
            [au_to_m * delta for delta in series.astype(np.float64)]
        )
    if pattern in ["ObsSub-LON", "ObsSub-LAT"]:
        return series.astype(np.float64)
    if pattern == "Ang-diam":
        # convert from arcseconds to degree
        return series.astype(np.float64) / 3600
    # only present for lunar ephemerides with selenographic coords
    # specified
    if pattern == "T-O-M":
        return series.astype(np.float64)
    # only present for ephemerides with planetographic coords specified
    if pattern in ["geo_lat", "geo_lon", "geo_el"]:
        return series.astype(np.float64)


def clean_up_series(query_type, pattern, series):
    if query_type == "OBSERVER":
        return clean_up_observer_series(pattern, series)
    if query_type == "VECTORS":
        return clean_up_vectors_series(pattern, series)


def polish_horizons_table(horizon_frame, query_type):
    """
    make a nicely-formatted table from Horizons response text. make
    tractable column names. also convert distance units from AU or km to m and
    arcseconds to degrees.
    """
    horizon_columns = {}
    # we have to use regex here because sometimes they
    # put extra underscores for spacing
    patterns = TABLE_PATTERNS[query_type]
    for pattern in patterns.keys():
        matches = [
            col for col in horizon_frame.columns if re.match(pattern, col)
        ]
        # did we not ask for this quantity? move on
        if len(matches) == 0:
            continue
        # multiple matches? better fix something
        assert len(matches) == 1
        series = horizon_frame[matches[0]]
        output_name = patterns[pattern]
        cleaned_result = clean_up_series(query_type, pattern, series)
        if cleaned_result is None:
            continue
        horizon_columns[output_name] = cleaned_result

    return pd.DataFrame(horizon_columns)
