import numpy as np
import pandas as pd

from lhorizon.constants import LUNAR_RADIUS
from lhorizon.target import Targeter
from lhorizon.tests.data.test_cases import TEST_CASES
from lhorizon.kernels import load_metakernel

load_metakernel()


def test_find_targets_long():
    path = TEST_CASES["TRANQUILITY_2021"]["data_path"]
    targeter = Targeter(
        pd.read_csv(path + "_CENTER.csv"), target_radius=LUNAR_RADIUS
    )
    targeter.find_targets(
        pd.read_csv(path + "_TARGET.csv"), "j2000", "IAU_MOON"
    )
    assert np.allclose(
        targeter.target_ephemeris["geo_lon"],
        targeter.target_ephemeris["lon"],
        rtol=0.002
    )
    assert np.allclose(
        targeter.target_ephemeris["geo_lat"],
        targeter.target_ephemeris["lat"],
        rtol=0.002
    )
