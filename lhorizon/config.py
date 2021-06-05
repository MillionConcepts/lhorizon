"""configuration options for lhorizon"""

# get all Horizons columns by default
from types import MappingProxyType

EPH_QUANTITIES = "A"

# timeout for connecting to jpl server
TIMEOUT = 30

HORIZONS_SERVER = "https://ssd.jpl.nasa.gov/horizons_batch.cgi"

# table of regexes used to match Horizons fields and the arguably-more-readable
# column names we assign them to
POINTING_COLUMN_PATTERNS = MappingProxyType(
    {
        r"Date_+\(UT\)": "time",
        r"Date_+JDUT": "jd",
        r"R.A.*\(ICRF\)": "ra_ast",  # astrometric ra
        r"DEC.*\(ICRF\)": "dec_ast",  # astrometric dec
        r"R.A.*\(rfct-app\)": "ra_app_r",
        # refracted apparent ra in weird frame?
        r"DEC.*\(rfct-app\)": "dec_app_r",
        # refracted apparent dec in weird frame?
        r"R.A.*\(a-app\)": "ra_app",  # airless apparent ra in weird frame?
        r"DEC.*\(a-app\)": "dec_app",
        # airless apparent dec in weird frame?
        r"RA.*\(ICRF-a-app\)": "ra_app_icrf",
        r"DEC.*\(ICRF-a-app\)": "dec_app_icrf",
        r"RA.*\(ICRF-r-app\)": "ra_app_icrf_r",
        r"DEC.*\(ICRF-r-app\)": "dec_app_icrf_r",
        r"Azi.*\(a-app\)": "az",
        r"Elev.*\(a-app\)": "alt",
        r"Azi.*\(r-appr\)": "az_r",
        r"Elev.*\(r-appr\)": "alt_r",
        "delta": "dist",
        "ObsSub-LON": "sub_lon",
        "ObsSub-LAT": "sub_lat",
        "SunSub-LON": "sub_lon",
        "SunSub-LAT": "sub_lat",
        "Ang-diam": "ang_diam",
        "T-O-M": "t_o_m",
        r"NP\.ang": "npa",
        "geo_lat": "geo_lat",
        "geo_lon": "geo_lon",
        "geo_el": "geo_el",
    }
)

KNOWN_ID_TYPES = (
    "smallbody",
    "majorbody",
    "designation",
    "name",
    "asteroid_name",
    "comet_name",
    "id",
)

KNOWN_QUERY_TYPES = ("OBSERVER", "VECTORS", "ELEMENTS")