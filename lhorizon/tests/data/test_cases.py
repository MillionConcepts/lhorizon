from pathlib import Path

TEST_CASES = {
    "CYDONIA_PALM_SPRINGS_1959_TOPO": {
        "init_kwargs": {
            "target": {
                "lon": -9.46,
                "lat": 40.75,
                "elevation": 0,
                "body": 499,
            },
            "origin": {
                "lon": -243.46,
                "lat": 33.8,
                "elevation": 0,
                "body": 399,
            },
            "epochs": {
                "start": "1959-01-01T00:00:00",
                "stop": "1959-01-02T01:00:00",
                "step": "10m",
            },
        },
        "request_url": "https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1"
                       "&TABLE_TYPE=OBSERVER&QUANTITIES=%271%2C2%2C4%2C13"
                       "%2C14%2C15%2C17%2C20%2C45%27&COMMAND=%22g%3A-9.46"
                       "%2C40.75%2C0%40499%22&SOLAR_ELONG=%220%2C180%22"
                       "&LHA_CUTOFF=0&CSV_FORMAT=YES&CAL_FORMAT=BOTH"
                       "&ANG_FORMAT=DEG&APPARENT=AIRLESS&REF_SYSTEM=J2000"
                       "&EXTRA_PREC=NO&CENTER=coord%40399&COORD_TYPE"
                       "=GEODETIC&SITE_COORD=%27-243.460000%2C33.800000%2C0"
                       ".000000%27&START_TIME=%221959-01-01T00%3A00%3A00%22"
                       "&STOP_TIME=%221959-01-02T01%3A00%3A00%22&STEP_SIZE"
                       "=%2210m%22&SKIP_DAYLT=NO",
        "data_path": str(
            Path(Path(__file__).parent, "CYDONIA_PALM_SPRINGS_1959_TOPO")
        ),
    },
    "MEUDON_MOON_NOW": {
        "init_kwargs": {
            "target": 301,
            "origin": "5@399",
        },
        "request_url": "https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1"
                       "&TABLE_TYPE=OBSERVER&QUANTITIES=%271%2C2%2C4%2C13"
                       "%2C14%2C15%2C17%2C20%2C45%27&COMMAND=%22301%22"
                       "&SOLAR_ELONG=%220%2C180%22&LHA_CUTOFF=0&CSV_FORMAT"
                       "=YES&CAL_FORMAT=BOTH&ANG_FORMAT=DEG&APPARENT=AIRLESS"
                       "&REF_SYSTEM=J2000&EXTRA_PREC=NO&CENTER=%275%40399%27"
                       "&TLIST=",
    },
    "SUN_PHOBOS_1999": {
        "init_kwargs": {
            "target": "Phobos",
            "origin": "@sun",
            "epochs": "1991-01-01",
        },
        "request_url": "https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1"
                       "&TABLE_TYPE=OBSERVER&QUANTITIES=%271%2C2%2C4%2C13"
                       "%2C14%2C15%2C17%2C20%2C45%27&COMMAND=%22Phobos%22"
                       "&SOLAR_ELONG=%220%2C180%22&LHA_CUTOFF=0&CSV_FORMAT"
                       "=YES&CAL_FORMAT=BOTH&ANG_FORMAT=DEG&APPARENT=AIRLESS"
                       "&REF_SYSTEM=J2000&EXTRA_PREC=NO&CENTER=%27%40sun%27"
                       "&TLIST=2448257.5&SKIP_DAYLT=NO",
        "data_path": str(Path(Path(__file__).parent, "SUN_PHOBOS_1999")),
    },
    "WEIRD_OPTIONS": {
        "init_kwargs": {
            "epochs": {
                "start": "1991-01-01",
                "stop": "1991-01-10",
                "step": "6h",
            },
            "query_options": {
                "airmass_lessthan": 80,
                "solar_elongation": (1, 99),
                "max_hour_angle": 1,
                "rate_cutoff": 5000,
                "skip_daylight": True,
                "refraction": True,
                "closest_apparition": True,
                "no_fragments": True,
                "extra_precision": True,
            },
        },
        "request_url": "https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1"
                       "&TABLE_TYPE=OBSERVER&QUANTITIES=%271%2C2%2C4%2C13"
                       "%2C14%2C15%2C17%2C20%2C45%27&COMMAND=%22301+CAP%3B"
                       "+NOFRAG%3B%22&SOLAR_ELONG=%221%2C99%22&LHA_CUTOFF=1"
                       "&CSV_FORMAT=YES&CAL_FORMAT=BOTH&ANG_FORMAT=DEG"
                       "&APPARENT=REFRACTED&REF_SYSTEM=J2000&EXTRA_PREC=YES"
                       "&CENTER=%27500%40399%27&ANG_RATE_CUTOFF=5000"
                       "&START_TIME=%221991-01-01%22&STOP_TIME=%221991-01-10"
                       "%22&STEP_SIZE=%226h%22&AIRMASS=80&SKIP_DAYLT=YES",
    },
    # a favorite of Michael Mommert
    "CERES_2000": {
        "init_kwargs": {"target": "Ceres", "epochs": 2451544.5},
        "request_url": "https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1"
                       "&TABLE_TYPE=OBSERVER&QUANTITIES=%271%2C2%2C4%2C13"
                       "%2C14%2C15%2C17%2C20%2C45%27&COMMAND=%22Ceres%22"
                       "&SOLAR_ELONG=%220%2C180%22&LHA_CUTOFF=0&CSV_FORMAT"
                       "=YES&CAL_FORMAT=BOTH&ANG_FORMAT=DEG&APPARENT=AIRLESS"
                       "&REF_SYSTEM=J2000&EXTRA_PREC=NO&CENTER=%27500%40399"
                       "%27&TLIST=2451544.5&SKIP_DAYLT=NO",
        "data_path": str(Path(Path(__file__).parent, "CERES_2000")),
    },
    "TRANQUILITY_2021": {
        "data_path": str(Path(Path(__file__).parent, "TRANQUILITY_2021")),
        "frames": ("j2000", "IAU_MOON")
    },
    "MARS_SUN_ANGLE_MINIMAL": {
        "init_kwargs": {
            "target": 10,
            "origin": {
                'lon': -77.5, 'lat': 18.4, 'elevation': 0, 'body': '499'
            },
            "epochs": {
                'start': '2020-01-01T00:00:00',
                'stop': '2023-02-01T00:00:00',
                'step': '5d'
            },
            "chunksize": 50
        },
        "data_path": str(Path(Path(__file__).parent, "MARS_SUN_ANGLE_MINIMAL")),
        "lhorizon_count": 5,
        "use_columns": ["time", "az", "alt"]
    }
}
