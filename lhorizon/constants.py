"""
constants used elsewhere in `lhorizon`.
"""
from types import MappingProxyType

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