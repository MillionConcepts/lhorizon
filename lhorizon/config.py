"""
configuration options for `lhorizon`. Modifying members of this module will
change the default behavior of `LHorizon` objects.

### options

* OBSERVER_QUANTITIES: default Horizons QUANTITIES columns for OBSERVER queries
* VECTORS_QUANTITIES: default Horizons QUANTITIES columns for VECTORS queries
* TIMEOUT: timeout in seconds for JPL
* HORIZONS_SERVER: address of Horizons CGI gateway
* DEFAULT_HEADERS: default headers for Horizons requests
* TABLE_PATTERNS: tables of regexes used to match Horizons fields and the
    arguably more-readable column names we assign them to
"""

OBSERVER_QUANTITIES = "1,2,4,13,14,15,17,20,45"
VECTORS_QUANTITIES = "3"
TIMEOUT = 30

HORIZONS_SERVER = "https://ssd.jpl.nasa.gov/horizons_batch.cgi"
DEFAULT_HEADERS = {
    "Accept": "text/plain,text/html,application/xhtml+xml,"
              "application/xml;q=0.9,,*/*;q=0.8",
    "Connection": "keep-alive"
}

TABLE_PATTERNS = {
    "VECTORS": {
        r"Calendar Date": "time_tdb",
        r"X": "x",
        r"Y": "y",
        r"Z": "z",
        r"VX": "vx",
        r"VY": "vy",
        r"VZ": "vz",
        r"LT": "light_time",
        r"RG": "dist",
        r"RR": "velocity",
    },
    "OBSERVER": {
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
        r"Illu%": "illum",
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
    },
}
