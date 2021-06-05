import re
from io import StringIO

import numpy as np
import pandas as pd
from astropy import units as u
from dateutil import parser as dtp

from lhorizon.lhorizon_utils import hunt_csv
from lhorizon.config import POINTING_COLUMN_PATTERNS


def make_horizon_dataframe(raw_horizon_response, get_target_location=False):
    """make a pandas dataframe from a raw horizon response."""

    # delimiters for column and data sections
    # TODO: this only works right if all the columns are selected. maybe
    #  specifying this in a better way would be better.
    horizon_column_search = re.compile(r"Date.*(?=\n\*+)")
    horizon_data_search = re.compile(r"(?<=\$\$SOE\n)(.|\n)*(?=\$\$EOE)")

    # grab these sections and write them into a string buffer
    try:
        columns = re.search(horizon_column_search, raw_horizon_response)[0]
        data = re.search(horizon_data_search, raw_horizon_response)[0]
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


def polish_horizons_table(horizon_frame):
    """
    make a nicely-formatted table from Horizons response text. make
    tractable column names. also convert distance units from AU to m and
    arcseconds to degrees.
    """
    au_to_m = (1 * u.au).to(u.m).value
    horizon_columns = {}
    # we have to use regex here because sometimes they
    # put extra underscores for spacing
    for pattern in POINTING_COLUMN_PATTERNS:
        matches = [
            col for col in horizon_frame.columns if re.match(pattern, col)
        ]
        # did we not ask for this quantity? move on
        if len(matches) == 0:
            continue
        # multiple matches? better fix something
        assert len(matches) == 1
        series = horizon_frame[matches[0]]
        output_name = POINTING_COLUMN_PATTERNS[pattern]
        if pattern == r"Date_+\(UT\)":
            horizon_columns[output_name] = pd.Series(
                [dtp.parse(instant) for instant in series]
            )
        if pattern.startswith(("R.A.", "DEC", "Azi", "Elev", "RA", "NP")):
            try:
                float(series[0])
            except ValueError:
                # generally "n. a." values for locations that apparent az
                # / alt aren't meaningful for, like earth topocenter
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


