"""
This module contains a number of specialized query constructors and related
helper functions for lhorizon.
"""
import logging
from collections.abc import Mapping, MutableMapping, Sequence
import datetime as dt
import math
import re
import time
from typing import Union, Optional

import dateutil.parser as dtp
import numpy as np
import pandas as pd
import requests
from more_itertools import chunked

from lhorizon import LHorizon
from lhorizon.constants import HORIZON_TIME_ABBREVIATIONS
from lhorizon.lhorizon_utils import (
    default_lhorizon_session,
    have_telnet_conversation,
    open_noninteractive_jpl_telnet_connection,
)


def estimate_line_count(
    horizons_dt: MutableMapping[str, dt.datetime], seconds_per_step: float
):
    """
    estimate number of lines that will be returned by _Horizons_ for a given
    query. Cannot give correct answers for cases in which airmass, hour
    angle, or other restrictive options are set. Used by bulk query
    constructors to help split large queries across multiple `LHorizon`s.
    """
    return math.ceil(
        (horizons_dt["stop"] - horizons_dt["start"]).total_seconds()
        / seconds_per_step
    )


def chunk_time(epochs: MutableMapping, chunksize: int) -> list[dict]:
    """
    chunk time into a series of intervals that will return at most `chunksize`
    lines from _Horizons_.
    """
    horizons_dt = datetime_from_horizon_epochs(**epochs)
    # interpret stepsize-with-units as time and use it to calculate number of
    # lines in requested interval
    if horizons_dt["step"][-1].isalpha():
        seconds_per_step = HORIZON_TIME_ABBREVIATIONS[
            horizons_dt["step"][-1]
        ] * int(horizons_dt["step"][:-1])
        lines = estimate_line_count(horizons_dt, seconds_per_step)
    # interpret stepsize-without-units as number of lines in requested
    # interval and use it to calculate stepsize in time
    else:
        lines = horizons_dt["step"]
        seconds_per_step = (
            horizons_dt["stop"] - horizons_dt["start"]
        ).total_seconds() / lines
    # chunk interval into as many sub-intervals as necessary
    chunks = tuple(chunked(range(lines), chunksize))
    # divide unitless steps by number of chunks
    if not horizons_dt["step"][-1].isalpha():
        horizons_dt["step"] = math.ceil(int(horizons_dt["step"]) / len(chunks))
    times = []
    # set specific time bounds of queries and return them
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


def datetime_from_horizon_epochs(start: str, stop: str, step: Union[int, str]):
    """convert epoch dict to datetime in order to estimate response length."""
    return {"start": dtp.parse(start), "stop": dtp.parse(stop), "step": step}


def construct_lhorizon_list(
    epochs: MutableMapping,
    target: Union[int, str, MutableMapping] = "301",
    origin: Union[int, str, MutableMapping] = "500@399",
    session: Optional[requests.Session] = None,
    query_type: str = "OBSERVER",
    query_options: Optional[Mapping] = None,
    chunksize=85000,
) -> list[LHorizon]:
    """
    construct a list of `LHorizon`s. Intended for queries that will
    return over 90000 lines, currently the hard limit of the _Horizons_
    CGI. this function takes most of the same arguments as `LHorizon`, but
    epochs must be specified as a dictionary with times in ISO format.

    NOTE: this function does not support chunking long lists of
    explicitly-defined individual epochs. queries of this type are extremely
    inefficient for _Horizons_ and delivering many of them in quick succession
    typically causes it to tightly throttle the requester.
    """
    return [
        LHorizon(
            target,
            origin,
            query_type=query_type,
            session=session,
            epochs=chunk,
            query_options=query_options,
        )
        for chunk in chunk_time(epochs, chunksize)
    ]


def query_all_lhorizons(
    lhorizons: Sequence[LHorizon],
    delay_between=2,
    delay_retry=8,
    max_retries=5,
):
    """
    queries a sequence of `LHorizon`s using a shared
    session, carefully closing sockets and pausing between them, regenerating
    session and pausing for a longer interval if _Horizons_ rejects a query
    """
    # TODO, maybe: add an attractive progress bar of some type
    session = default_lhorizon_session()
    for ix, lhorizon in enumerate(lhorizons):
        lhorizon.session = session
        lhorizon.prepare_request()
        logging.info(
            f"querying Horizons for LHorizon {ix+1} of {len(lhorizons)}"
        )
        lhorizon.query()
        retries = 0
        while lhorizon.response.status_code != 200:
            if retries > max_retries:
                raise TimeoutError(
                    f"exceeded {max_retries}; retries aborting request."
                )
            logging.info(
                f"response code {lhorizon.response.status_code}, "
                f"pausing before retrying request"
            )
            lhorizon.session.close()
            time.sleep(delay_retry)
            logging.info("retrying request")
            session = default_lhorizon_session()
            lhorizon.session = default_lhorizon_session()
            lhorizon.prepare_request()
            lhorizon.query(refetch=True)
            retries += 1
        logging.info(
            f"collected data from {lhorizon.epochs['start']} "
            f"to {lhorizon.epochs['stop']}"
        )
        # pausing for politeness
        if ix != len(lhorizons) - 1:
            logging.info("pausing before next request")
            time.sleep(delay_between)


def list_sites(center_body: int = 399) -> pd.DataFrame:
    """
    query _Horizons_ for all named sites recognized on the specified body and
    format this response as a DataFrame. if no body is specified, uses Earth
    (399).
    """
    # the choice of '500' is totally arbitrary -- Horizons just dooesn't have
    # a generalized 'search' command; you must give it some arbitrary table
    # request along with a center string it will interpret as a search
    response = requests.get(
        "https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1&COMMAND=500"
        "&CENTER=%22*@{}%22&CSV_FORMAT=YES".format(str(center_body))
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


def list_majorbodies() -> pd.DataFrame:
    """
    query Horizons for all currently-recognized major bodies and format the
    response into a DataFrame.
    """
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
    return pd.DataFrame(data_values, columns=["id", "name"]).dropna(axis=0)


def get_observer_quantity_codes() -> str:
    """
    retrieve observer quantity code table from HORIZONS telnet interface"""
    jpl = open_noninteractive_jpl_telnet_connection()
    conversation_structure = (
        (b"499\n", b" <cr>:"),
        (b"E\n", b" : "),
        (b"o\n", b" : "),
        (b"301\n", b"--> "),
        (b"\n", b" : "),
        (b"\n", b" : "),
        (b"\n", b" : "),
        (b"\n", b" : "),
        (b"n\n", b" : "),
        (b"?\n", b"Spacecraft \r\n"),
    )
    conversation = have_telnet_conversation(conversation_structure, jpl)
    quantity_response = conversation[-1].decode("ascii")
    return re.search(r"1\..*Spacecraft", quantity_response, re.DOTALL).group()


# TODO: de-deprecate this
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
