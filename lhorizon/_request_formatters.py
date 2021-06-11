from collections.abc import Mapping

import numpy as np


def format_geodetic_origin(location):
    return {
        "CENTER": "coord@{:s}".format(str(location["body"])),
        "COORD_TYPE": "GEODETIC",
        "SITE_COORD": "'{:f},{:f},{:f}'".format(
            location["lon"],
            location["lat"],
            location["elevation"],
        ),
    }


def format_geodetic_target(location):
    # return 'g:'+str(longitude)+','+str(latitude)+','+\
    #     str(elevation)+'@'+str(target_id)
    return "g:{lon},{lat},{elevation}@{body}".format(**location)


def format_epoch_params(epochs):
    epoch_payload = {}
    # parse epochs into request payload variables
    if isinstance(epochs, (list, tuple, np.ndarray)):
        epoch_payload["TLIST"] = "\n".join([str(epoch) for epoch in epochs])
    elif isinstance(epochs, dict):
        if (
            "start" not in epochs
            or "stop" not in epochs
            or "step" not in epochs
        ):
            raise ValueError("'epochs' must contain start, " + "stop, step")
        epoch_payload["START_TIME"] = (
            '"' + epochs["start"].replace("'", "") + '"'
        )
        epoch_payload["STOP_TIME"] = (
            '"' + epochs["stop"].replace("'", "") + '"'
        )
        epoch_payload["STEP_SIZE"] = (
            '"' + epochs["step"].replace("'", "") + '"'
        )
    else:
        # treat epochs as scalar
        epoch_payload["TLIST"] = str(epochs)
    return epoch_payload


def make_commandline(target, id_type, closest_apparition, no_fragments):
    if isinstance(target, Mapping):
        target = format_geodetic_target(target)
    commandline = str(target)
    if id_type in [
        "designation",
        "name",
        "asteroid_name",
        "comet_name",
    ]:
        commandline = {
            "designation": "DES=",
            "name": "NAME=",
            "asteroid_name": "ASTNAM=",
            "comet_name": "COMNAM=",
        }[id_type] + commandline
    if id_type in [
        "smallbody",
        "asteroid_name",
        "comet_name",
        "designation",
    ]:
        commandline += ";"
        if isinstance(closest_apparition, bool):
            if closest_apparition:
                commandline += " CAP;"
        else:
            commandline += " CAP{:s};".format(closest_apparition)
        if no_fragments:
            commandline += " NOFRAG;"
    return commandline


def assemble_request_params(
    commandline,
    query_type,
    extra_precision,
    max_hour_angle,
    quantities,
    refraction,
    refsystem,
    solar_elongation,
):
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
