"""specialized query helpers for lhorizon"""

import datetime as dt
from functools import partial
import math
from types import MappingProxyType

import astropy.time as at
import astropy.units as u
import dateutil.parser as dtp
import pandas as pd
import requests
from more_itertools import chunked

from lhorizon import LHorizon
from lhorizon_utils import snorm

HORIZON_TIME_ABBREVIATIONS = MappingProxyType({
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "y": 60 * 60 * 24 * 365,
})


def datetime_from_horizons_syntax(start, stop, step):
    return {
        "start": dtp.parse(start),
        "stop": dtp.parse(stop),
        "step size": HORIZON_TIME_ABBREVIATIONS[step[-1]] * int(step[:-1]),
    }


def estimate_line_count(start, stop, step):
    horizons_dt = datetime_from_horizons_syntax(start, stop, step)
    return math.ceil(
        (horizons_dt["stop"] - horizons_dt["start"]).total_seconds()
        / horizons_dt["step size"]
    )


def get_lhorizon_moon(
    lunar_coords,
    time_series,
    observer_location=-1,
    query_options=None,
    session=None,
):
    """
    TODO: cut or improve

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
        origin=observer_location,
        epochs=epochs,
        session=session,
    )
    moon.query(**query_options)

    return moon.pointing()


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
