# TODO: mark this as slow using pytest.mark, only run if specifically indicated
import logging
import math
import random
from itertools import product

import pytest

from lhorizon.base import LHorizon
from lhorizon.lhorizon_utils import default_lhorizon_session
from lhorizon.config import HORIZONS_SERVER
from lhorizon.tests.data.test_cases import TEST_CASES
from lhorizon.tests.utilz import check_against_reference


def test_if_horizons_is_reachable():
    session = default_lhorizon_session()
    response = session.get(HORIZONS_SERVER)
    session.close()
    assert response.status_code == 200


CASES_TO_USE = (
    "SUN_PHOBOS_1999",
    "CERES_2000",
    "CYDONIA_PALM_SPRINGS_1959_TOPO",
)
cases = {case: TEST_CASES[case] for case in CASES_TO_USE}
test_parameters = product(cases.keys(), ("OBSERVER", "VECTORS"))


@pytest.mark.parametrize("case_name,query_type", test_parameters)
def test_full_retrieval(case_name, query_type):
    case = cases[case_name]
    # noinspection PyTypeChecker
    test_lhorizon = LHorizon(
        **case["init_kwargs"],
        query_type=query_type,
        session=default_lhorizon_session()
    )
    test_df = test_lhorizon.dataframe()
    test_table = test_lhorizon.table()
    check_against_reference(case, query_type, test_df, test_table)
    logging.getLogger().info(str(test_lhorizon) + " retrieved")


def test_bad_request():
    apocrypha = LHorizon("Arisia", "Velantia III")
    try:
        apocrypha.table()
        raise RuntimeError("that shouldn't have worked!")
    except ValueError:
        pass


def test_random_reflexive_pointing():
    # is a sub-Cydonia point on the Moon in fact looking back at Cydonia?
    somewhere_in_cydonia = {
        "lon": -350.5 + random.randint(1, 100) / 100,
        "lat": 40.7 + random.randint(1, 100) / 100,
        "elevation": 0,
        "body": "499",
    }
    moon_from_cydonia = LHorizon(
        301,
        somewhere_in_cydonia,
        epochs=random.randint(2440000, 2460000),
    ).table()

    intercept_time, intercept_lon, intercept_lat = tuple(
        moon_from_cydonia[["time", "sub_lon", "sub_lat"]].iloc[0]
    )
    cydonia_from_subcydonian_point = LHorizon(
        somewhere_in_cydonia,
        origin={
            "lon": intercept_lon,
            "lat": intercept_lat,
            "elevation": 0,
            "body": "301",
        },
        epochs=intercept_time.isoformat(),
    ).table()
    lunar_dec = moon_from_cydonia["dec_app_icrf"].iloc[0]
    cydonia_dec = cydonia_from_subcydonian_point["dec_app_icrf"].iloc[0]
    assert math.isclose(abs(lunar_dec), abs(cydonia_dec), rel_tol=0.001)
