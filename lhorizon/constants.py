"""
constants used elsewhere in `lhorizon`.
"""
from types import MappingProxyType as MPt

import pandas as pd

LUNAR_RADIUS = 1737400
AU_TO_M = 149597870700
HORIZON_TIME_ABBREVIATIONS = MPt(
    {
        "m": 60,
        "h": 60 * 60,
        "d": 60 * 60 * 24,
        "y": 60 * 60 * 24 * 365,
    }
)
J2000_UTC = pd.Timestamp("2000-01-01 11:58:55.816073")
J2000_TDB = pd.Timestamp("2000-01-01 12:00:00")
HORIZONS_QUANTITY_NAMES = MPt(
    {
        "OBSERVER": {
            1: "Astrometric RA & DEC",
            2: "Apparent RA & DEC",
            3: "Rates: RA & DEC",
            4: "Apparent azimuth & elevation (AZ-EL) :",
            5: "Rates: azimuth and elevation (AZ-EL))",
            6: "X & Y satellite offset & position angle",
            7: "Local Apparent Sidereal Time",
            8: "Airmass & visual magnitude extinction",
            9: "Visual magnitude & surface brightness",
            10: "Illuminated fraction",
            11: "Defect of illumination",
            12: "Angular separation/visibility",
            13: "Target angular diameter",
            14: "Observer sub-longitude & sub-latitude",
            15: "Solar sub-longitude & sub-latitude",
            16: "Sub-solar position angle & distance from disc center",
            17: "North pole position angle & distance from disc center",
            18: "Heliocentric ecliptic longitude & latitude",
            19: "Solar range & range-rate (relative to target)",
            20: "Target range & range rate (relative to observer)",
            21: "Down-leg light-time",
            22: "Speed with respect to Sun & observer",
            23: "Sun-Observer-Target (apparent solar elongation) angle",
            24: "Sun-Target-Observer angle",
            25: "Target-Observer-Moon angle and illuminated fraction",
            26: "Observer-Primary-Target angle",
            27: "Position angles of heliocentric radius & -velocity vector",
            28: "Orbit plane angle",
            29: "Constellation ID",
            30: "TDB-UT",
            31: "Observer ecliptic longitude & latitude",
            32: "Target north-pole RA & DEC",
            33: "Galactic longitude & latitude",
            34: "Local Apparent Solar Time",
            35: "Earth to site light-time",
            36: "Plane-of-sky RA and DEC pointing uncertainty",
            37: "Plane-of-sky error ellipse",
            38: "Plane-of-sky ellipse RSS pointing uncertainty",
            39: "Uncertainties in plane-of-sky radial direction",
            40: "Radar uncertainties (plane-of-sky radial direction)",
            41: "True anomaly angle",
            42: "Local apparent hour angle",
            43: "Phase angle and bisector",
            44: "Apparent target-centered longitude of the Sun (apparent L_s)",
            45: "Inertial apparent RA & Dec",
            46: "Rate: Inertial RA & DEC",
            47: "Sky motion: angular rate, direction position angle, and path "
            "angle",
            48: "Sky brightness and target visual signal-to-noise ratio (SNR)",
        },
        "VECTORS": {
            1: "Position components {x,y,z} only",
            2: "State vector {x,y,z,vx,vy,vz}",
            3: "State vector + 1-way light-time + range + range-rate",
            4: "Position + 1-way light-time + range + range-rate",
            5: "Velocity components {vx, vy, vz} only",
            6: "1-way light-time + range + range-rate",
        },
    }
)
