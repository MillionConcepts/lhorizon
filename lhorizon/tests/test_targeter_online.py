import datetime as dt
import math
import warnings

import numpy as np
import pandas as pd
import pytest
pytest.importorskip("sympy")

from lhorizon import LHorizon
from lhorizon.constants import LUNAR_RADIUS
from lhorizon.lhorizon_utils import make_raveled_meshgrid
from lhorizon.solutions import make_ray_sphere_lambdas
from lhorizon.target import Targeter
from lhorizon.kernels import load_metakernel

load_metakernel()
lunar_solutions = make_ray_sphere_lambdas(LUNAR_RADIUS)
rng = np.random.default_rng()


def test_targeter_long_online():
    start = rng.integers(2441318, 2460000)
    epochs = [start + ix / 10 for ix in range(10)]
    targeter = Targeter(
        LHorizon(301, epochs=epochs), solutions=lunar_solutions
    )
    reference = LHorizon({"lat": 10, "lon": 10, "body": 301}, epochs=epochs)
    targeter.find_targets(reference.table())
    targeter.transform_targets_to_body_frame("j2000", "IAU_MOON")
    assert np.allclose(
        targeter.ephemerides["pointing"]["geo_lon"],
        targeter.ephemerides["bodycentric"]["lon"],
        rtol=0.001,
    )
    assert np.allclose(
        targeter.ephemerides["pointing"]["geo_lat"],
        targeter.ephemerides["bodycentric"]["lat"],
        rtol=0.001,
    )


def test_targeter_wide_online():
    now = dt.datetime.now().isoformat()
    targeter = Targeter(LHorizon(301, epochs=now), solutions=lunar_solutions)

    grid_len = 5
    ra_center_value = targeter.ephemerides["body"]["ra_app_icrf"].iloc[0]
    ra_delta = 0.17
    dec_center_value = targeter.ephemerides["body"]["dec_app_icrf"].iloc[0]
    dec_delta = 0.17

    ra_axis = np.array([ix * ra_delta for ix in np.arange(grid_len)])
    dec_axis = np.array([ix * dec_delta for ix in np.arange(grid_len)])
    ra_axis += ra_center_value - (grid_len - 1) / 2 * ra_delta
    dec_axis += dec_center_value - (grid_len - 1) / 2 * dec_delta
    raveled = make_raveled_meshgrid((ra_axis, dec_axis), ("ra", "dec"))
    raveled["dist"] = 1

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        targeter.find_target_grid(raveled)
    targeter.transform_targets_to_body_frame("j2000", "IAU_MOON")

    central_target = targeter.ephemerides["bodycentric"].iloc[12]
    sub_lon = targeter.ephemerides["body"]["sub_lon"].iloc[0]
    assert math.isclose(
        (central_target["lon"] + 360) % 360,
        (sub_lon + 360) % 360,
        abs_tol=0.008,
    )
    assert (
        abs(
            central_target["lat"]
            - targeter.ephemerides["body"]["sub_lat"].iloc[0]
        )
        < 0.008
    )
    assert pd.isna(targeter.ephemerides["bodycentric"].iloc[0]["x"])
    assert pd.isna(targeter.ephemerides["bodycentric"].iloc[24]["x"])
