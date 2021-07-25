"""
constants used elsewhere in `lhorizon`.
"""
import datetime as dt
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
LEAP_SECOND_THRESHOLDS = [
    dt.datetime(1972, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1972, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1973, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1974, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1975, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1976, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1977, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1978, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1979, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1981, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1982, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1983, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1985, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1987, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1989, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1990, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1992, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1993, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1994, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1995, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(1997, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(1998, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(2005, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(2008, 12, 31, tzinfo=dt.timezone.utc),
    dt.datetime(2012, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(2015, 6, 30, tzinfo=dt.timezone.utc),
    dt.datetime(2016, 12, 31, tzinfo=dt.timezone.utc),
]
DT_J2000_UTC = dt.datetime(2000, 1, 1, 11, 58, 55, 816000)
DT_J2000_TDB = dt.datetime(2000, 1, 1, 12, 0, 0, 0)
