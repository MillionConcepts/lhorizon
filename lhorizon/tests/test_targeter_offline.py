import warnings

import numpy as np
import pandas as pd

from lhorizon.constants import LUNAR_RADIUS
from lhorizon.lhorizon_utils import make_raveled_meshgrid
from lhorizon.solutions import make_ray_sphere_lambdas
from lhorizon.target import Targeter
from lhorizon.tests.data.test_cases import TEST_CASES
from lhorizon.kernels import load_metakernel

load_metakernel()
lunar_solutions = make_ray_sphere_lambdas(LUNAR_RADIUS)


def test_find_targets_long():
    path = TEST_CASES["TRANQUILITY_2021"]["data_path"]
    targeter = Targeter(
        pd.read_csv(path + "_CENTER.csv"), solutions=lunar_solutions
    )
    targeter.find_targets(pd.read_csv(path + "_TARGET.csv"))
    targeter.transform_targets_to_body_frame("j2000", "IAU_MOON")
    assert np.allclose(
        targeter.ephemerides["pointing"]["geo_lon"],
        targeter.ephemerides["bodycentric"]["lon"],
        rtol=0.002,
    )
    assert np.allclose(
        targeter.ephemerides["pointing"]["geo_lat"],
        targeter.ephemerides["bodycentric"]["lat"],
        rtol=0.002,
    )


def test_find_targets_wide():
    path = TEST_CASES["TRANQUILITY_2021"]["data_path"]
    targeter = Targeter(
        pd.read_csv(path + "_CENTER.csv").loc[0:0], solutions=lunar_solutions
    )

    grid_len = 5
    ra_center_value = targeter.ephemerides["body"]["ra_app_icrf"].iloc[0]
    ra_delta = 0.1
    dec_center_value = targeter.ephemerides["body"]["dec_app_icrf"].iloc[0]
    dec_delta = 0.1
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

    assert pd.isna(targeter.ephemerides["bodycentric"].iloc[0]["x"])
    assert pd.isna(targeter.ephemerides["bodycentric"].iloc[24]["y"])

    assert (
        abs(
            targeter.ephemerides["bodycentric"]["lon"].iloc[12]
            - targeter.ephemerides["body"]["sub_lon"].iloc[0]
        )
        < 0.005
    )
    assert (
        abs(
            targeter.ephemerides["bodycentric"]["lat"].iloc[12]
            - targeter.ephemerides["body"]["sub_lat"].iloc[0]
        )
        < 0.005
    )
