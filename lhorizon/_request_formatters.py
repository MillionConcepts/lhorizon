"""
formatters to translate various parameters and options into URL parameters
that can be parsed by JPL Horizons' CGI. These are mostly intended to be used
by LHorizon methods and should probably not be called directly.
"""

from collections.abc import Mapping, Sequence
from typing import Union

import numpy as np
import pandas as pd


def format_geodetic_origin(location: Mapping) -> dict:
    """
    creates dict of URL parameters for a geodetic coordinate origin
    """
    return {
        "CENTER": "coord@{:s}".format(str(location["body"])),
        "COORD_TYPE": "GEODETIC",
        "SITE_COORD": "'{:f},{:f},{:f}'".format(
            float(location["lon"]),
            float(location["lat"]),
            float(location["elevation"]),
        ),
    }


def format_geodetic_target(location: Mapping) -> str:
    """creates command string for a geodetic target"""
    return "g:{lon},{lat},{elevation}@{body}".format(**location)


def format_epoch_params(epochs: Union[Sequence, Mapping]) -> dict:
    """creates dict of URL parameters from epochs"""
    epoch_payload = {}
    if isinstance(epochs, (pd.Series, list, tuple, np.ndarray)):
        epoch_payload["TLIST"] = "\n".join([str(epoch) for epoch in epochs])
    elif isinstance(epochs, dict):
        if (
            "start" not in epochs
            or "stop" not in epochs
            or "step" not in epochs
        ):
            raise ValueError("'epochs' must contain start, " + "stop, step")
        epoch_payload["START_TIME"] = '"' + str(epochs["start"]) + '"'
        epoch_payload["STOP_TIME"] = '"' + str(epochs["stop"]) + '"'
        epoch_payload["STEP_SIZE"] = '"' + str(epochs["step"]) + '"'
    else:
        # treat epochs as scalar
        epoch_payload["TLIST"] = str(epochs)
    return epoch_payload


def make_commandline(
    target: Union[str, int, Mapping],
    closest_apparition: Union[bool, str],
    no_fragments: bool,
):
    """makes 'primary' command string for Horizons CGI request'"""
    if isinstance(target, Mapping):
        target = format_geodetic_target(target)
    commandline = str(target)
    if isinstance(closest_apparition, bool):
        if closest_apparition:
            commandline += " CAP;"
    else:
        commandline += " CAP{:s};".format(closest_apparition)
    if no_fragments:
        commandline += " NOFRAG;"
    return commandline


def assemble_request_params(
    commandline: str,
    query_type: str,
    extra_precision: bool,
    max_hour_angle: float,
    quantities: str,
    refraction: bool,
    refsystem: str,
    solar_elongation: Sequence[float],
) -> dict[str]:
    """final-stage assembler for Horizons CGI URL parameters"""
    return {
        "batch": 1,
        "TABLE_TYPE": query_type,
        "QUANTITIES": "'" + str(quantities) + "'",
        "COMMAND": '"' + commandline + '"',
        "SOLAR_ELONG": '"'
        + str(solar_elongation[0])
        + ","
        + str(solar_elongation[1])
        + '"',
        "LHA_CUTOFF": str(max_hour_angle),
        "CSV_FORMAT": "YES",
        "CAL_FORMAT": "BOTH",
        "ANG_FORMAT": "DEG",
        "APPARENT": {False: "AIRLESS", True: "REFRACTED"}[refraction],
        "REF_SYSTEM": refsystem,
        "EXTRA_PREC": {True: "YES", False: "NO"}[extra_precision],
    }
