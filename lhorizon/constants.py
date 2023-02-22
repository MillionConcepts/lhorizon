"""
constants used elsewhere in `lhorizon`.
"""
import datetime as dt
from types import MappingProxyType

import pandas as pd

LUNAR_RADIUS = 1737400
AU_TO_M = 149597870700
HORIZON_TIME_ABBREVIATIONS = MappingProxyType(
    {
        "m": 60,
        "h": 60 * 60,
        "d": 60 * 60 * 24,
        "y": 60 * 60 * 24 * 365,
    }
)

J2000_UTC = pd.Timestamp("2000-01-01 11:58:55.816073")
J2000_TDB = pd.Timestamp("2000-01-01 12:00:00")
