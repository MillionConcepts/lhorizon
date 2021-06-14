"""specialized query helpers for lhorizon"""

import datetime as dt
import math
import re
import time
from types import MappingProxyType

import dateutil.parser as dtp
import numpy as np
import pandas as pd
import requests
from more_itertools import chunked

from lhorizon import LHorizon
from lhorizon.lhorizon_utils import default_lhorizon_session


def estimate_line_count(horizons_dt, seconds_per_step):

    return math.ceil(
        (horizons_dt["stop"] - horizons_dt["start"]).total_seconds()
        / seconds_per_step
    )


HORIZON_TIME_ABBREVIATIONS = MappingProxyType(
    {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
        "d": 60 * 60 * 24,
        "y": 60 * 60 * 24 * 365,
    }
)


def datetime_from_horizons_epochs(start, stop, step):
    return {"start": dtp.parse(start), "stop": dtp.parse(stop), "step": step}


def chunk_time(epochs, chunksize):
    horizons_dt = datetime_from_horizons_epochs(**epochs)
    if not horizons_dt["step"][-1].isalpha():
        raise ValueError(
            "times passed to this function must include an explicit time unit: "
            "s, m, h, d, y"
        )
    seconds_per_step = HORIZON_TIME_ABBREVIATIONS[
        horizons_dt["step"][-1]
    ] * int(horizons_dt["step"][:-1])
    chunks = chunked(
        range(estimate_line_count(horizons_dt, seconds_per_step)), chunksize
    )
    times = []
    for chunk in chunks:
        start = horizons_dt["start"] + dt.timedelta(
            seconds=seconds_per_step * chunk[0]
        )
        stop = horizons_dt["start"] + dt.timedelta(
            seconds=seconds_per_step * chunk[-1]
        )
        times.append(
            {
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "step": horizons_dt["step"],
            }
        )
    return times


def construct_lhorizon_list(
    target,
    origin,
    epochs,
    query_type="OBSERVER",
    chunksize=85000,
    id_type="majorbody",
    query_options=None,
):
    """
    this function does not support chunking long lists of explicitly-defined
    individual epochs. queries of this type are extremely inefficient for
    the Horizons backend and delivering many of them in quick succession
    typically causes it to tightly throttle the requester.
    """
    return [
        LHorizon(
            target,
            origin,
            id_type=id_type,
            query_type=query_type,
            epochs=chunk,
            query_options=query_options,
        )
        for chunk in chunk_time(epochs, chunksize)
    ]


def query_all_lhorizons(lhorizons, delay_between=2, delay_retry=8):
    """
    TODO, maybe: add an attractive progress bar of some type
    """
    session = default_lhorizon_session()
    for ix, lhorizon in enumerate(lhorizons):
        lhorizon.session = session
        lhorizon.prepare_request(**lhorizon.query_options)
        print(
            "querying Horizons for LHorizon "
            + str(ix + 1)
            + " of "
            + str(len(lhorizons))
        )
        lhorizon.query()
        # lhorizon = partial_lhorizon(session=session)
        while lhorizon.response.status_code != 200:
            print(
                "response code "
                + str(lhorizon.response.status_code)
                + ", pausing before re-request"
            )
            lhorizon.session.close()
            time.sleep(delay_retry)
            print("retrying request")
            session = default_lhorizon_session()
            lhorizon.session = default_lhorizon_session()
            lhorizon.prepare_request()
            lhorizon.query(refetch=True)
        print(
            "collected data from "
            + lhorizon.epochs["start"]
            + " to "
            + lhorizon.epochs["stop"]
        )
        # pausing for politeness
        if ix != len(lhorizons) - 1:
            print("pausing before next request")
            time.sleep(delay_between)


def list_sites(center_body=399):
    """make a pandas dataframe from a raw horizon response."""
    # the choice of '500' is totally arbitrary -- Horizons just dooesn't have
    # a generalized 'search' command; you must give it some arbitrary table
    # request along with a center string it will interpret as a search
    response = requests.get(
        "https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1&COMMAND=500"
        "&CENTER=%22*@{}%22&CSV_FORMAT=YES".format(
            str(center_body)
        )
    )

    observatory_header_regex = re.compile(r".*Observatory Name.*\n")
    observatory_data_regex = re.compile(r"(?<=------\n)(.|\n)*?(?=Multiple)")
    column_text = re.search(observatory_header_regex, response.text).group(0)
    columns = re.split("  +", column_text.strip())
    data_text = re.search(observatory_data_regex, response.text).group(0)
    data_values = []
    for line in data_text.splitlines():
        split = re.split(" +", line.strip(), maxsplit=4)
        # generally, sites on non-Earth bodies do not have id codes, but there
        # may still be a site or two (even if only the body center) with an id
        # code, so we cannot simply reduce the number of columns in the df and
        # expect acceptable parsing
        if "." in str(split[0]):
            split = [np.nan] + re.split(" +", line.strip(), maxsplit=3)
        data_values.append(split)
    return pd.DataFrame(data_values, columns=columns).rename(
        columns={"#": "id"}
    )

def list_majorbodies():
    response = requests.get(
        "https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1&COMMAND=MB"
        "&CSV_FORMAT=%22YES%22 "
    )

    majorbody_data_regex = re.compile(r"(?<=---- \n) +(.|\n)*?(?=Number)")
    data_text = re.search(majorbody_data_regex, response.text).group(0)
    data_values = []
    for line in data_text.splitlines():
        strip = re.sub(" +", " ", line.strip())
        split = re.split(" +", strip, maxsplit=1)
        data_values.append(split)
    return pd.DataFrame(data_values, columns= ["id", "name"]).dropna(axis=0)

#
# def get_lhorizon_moon(
#     lunar_coords,
#     time_series,
#     observer_location=-1,
#     query_options=None,
#     session=None,
# ):
#     """
#     TODO: cut or improve
#
#     convenience method. gets lunar ephemerides from Horizons for arbitrary
#     selenographic
#     coordinates, observer location, and input time series. unlike
#     get_horizon_moon_list(), this uses JPL Horizons' bulk epoch functionality
#     to get ephemerides at many times in a single response. this is much, much
#     faster, because JPL Horizons hates receiving hundreds of separate queries
#     in quick succession. however, has the downside that it evenly spaces the
#     sampled times across the interval defined by the time series, so there may
#     be quantization errors if the series is also not evenly spaced. JPL
#     will also reject epochs that space samples by fewer than 0.5 seconds.
#     """
#
#     if query_options is None:
#         query_options = {}
#
#     # format the selenographic position coordinate for horizons
#     # 301 is horizons code for the moon
#     # g: latitude, longitude, elevation is the prefix for planetodetic coords
#     # @ is the separator between coordinates and body
#     if lunar_coords is not None:
#         lunar_location = "g: " + str(lunar_coords)[1:-1] + " @ 301"
#     else:
#         lunar_location = "301"
#
#     # format time parameters for horizons:
#     # start / stop are beginning and end as y-m-d h:m:s:mmm
#     # step is number of samples, evenly spaced
#
#     epochs = {
#         "start": time_series[0],
#         "stop": time_series[len(time_series) - 1],
#         "step": str(len(time_series) - 1),
#     }
#
#     moon = LHorizon(
#         target_id=lunar_location,
#         id_type="id",
#         origin=observer_location,
#         epochs=epochs,
#         session=session,
#     )
#     moon.query(**query_options)
#
#     return moon.pointing()
#
#
#
# def fetch_bulk_generic(bulk_horizon_query):
#     for horizon_query in bulk_horizon_query:
#         horizon_query.query()
#         print(
#             "collected data from "
#             + horizon_query.epochs["start"]
#             + " to "
#             + horizon_query.epochs["stop"]
#         )
#     print("concatenating all data")
#     return pd.concat(
#         [horizon_query.table() for horizon_query in bulk_horizon_query]
#     )
#
#
# def moon_phase(moontime):
#     """
#     Time (in any astropy.time-parseable format) -> float giving moon phase in
#     degrees at that time.
#     """
#     moontime = at.Time(moontime)
#     epochs = {
#         "start": str(moontime.utc),
#         "stop": str((moontime + 1 * u.min).utc),
#         "step": "1",
#     }
#     phased_moon = LHorizon(target_id=301, id_type="id", epochs=epochs)
#     phased_moon.query(quantities=10)
#     illum = phased_moon.table()
#     # translate percentage to degrees
#     phase = snorm(illum.iloc[0, 2], 0, 180, 0, 100)
#     # are we before or after the full moon?
#     if illum.iloc[0, 0] > illum.iloc[1, 0]:
#         phase = 360 - phase
#     return phase
