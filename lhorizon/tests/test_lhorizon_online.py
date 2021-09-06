"""
test LHorizon functionality using data retrieved live from the JPL Horizons
CGI endpoint
"""

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
    """
    can JPL Horizons be reached at all from this host? if this test fails, you
    should also expect many other tests to fail, and no resolution can
    probably be found inside `lhorizon`.
    """
    session = default_lhorizon_session()
    response = session.get(HORIZONS_SERVER)
    session.close()
    assert response.status_code == 200


# define a set of queries to send to JPL Horizons
CASES_TO_USE = (
    "SUN_PHOBOS_1999",
    "CERES_2000",
    "CYDONIA_PALM_SPRINGS_1959_TOPO",
)
cases = {case: TEST_CASES[case] for case in CASES_TO_USE}
test_parameters = product(cases.keys(), ("OBSERVER", "VECTORS"))


@pytest.mark.parametrize("case_name,query_type", test_parameters)
def test_full_retrieval(case_name, query_type):
    """
    end-to-end test of LHorizon functionality. check that attributes
    of a LHorizon object with a predefined set of parameters match cached
    CSV tables from JPL Horizons.
    """
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
    """
    Test that LHorizon raises a ValueError -- as intended -- when it receives a
    'not found'-type response from JPL Horizons
    """
    apocrypha = LHorizon("Arisia", "Velantia III")
    try:
        apocrypha.table()
        raise RuntimeError("that shouldn't have worked!")
    except ValueError:
        pass


def test_random_reflexive_pointing():
    """
    end-to-end 'reasonableness' test of LHorizon functionality:
    is a sub-Cydonia point on the Moon in fact looking back at Cydonia?
    """
    # select a random location in Cydonia
    somewhere_in_cydonia = {
        "lon": -350.5 + random.randint(1, 100) / 100,
        "lat": 40.7 + random.randint(1, 100) / 100,
        "elevation": 0,
        "body": "499",
    }
    # select a random time between ~1968 and ~2023, and query JPL Horizons for
    # the corresponding sub-observer point on the Moon at that time.
    moon_from_cydonia = LHorizon(
        301,
        somewhere_in_cydonia,
        epochs=random.randint(2440000, 2460000),
    ).table()

    intercept_time, intercept_lon, intercept_lat = tuple(
        moon_from_cydonia[["time", "sub_lon", "sub_lat"]].iloc[0]
    )
    # now query JPL Horizons for that point's sub-Mars point at that time.
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
    # check that the declinations of these two rays are additively inverse,
    # or nearly so, as one would hope they would be
    lunar_dec = moon_from_cydonia["dec_app_icrf"].iloc[0]
    cydonia_dec = cydonia_from_subcydonian_point["dec_app_icrf"].iloc[0]
    assert math.isclose(abs(lunar_dec), abs(cydonia_dec), rel_tol=0.001)
