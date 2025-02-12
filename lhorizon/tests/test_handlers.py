"""
tests for lhorizon.handlers, using both mocked responses and data retrieved
live from the JPL Horizons CGI and telnet endpoints
"""

import time

import pandas as pd
import pytest

from lhorizon import LHorizon
from lhorizon.handlers import (
    query_all_lhorizons,
    construct_lhorizon_list,
    list_sites,
    list_majorbodies, get_observer_quantity_codes,
)
from lhorizon.tests.data.test_cases import TEST_CASES
from lhorizon.tests.utilz import (
    check_numeric_closeness, make_mock_failing_query, raise_badness
)

CASES_TO_USE = [
    "MARS_SUN_ANGLE_MINIMAL",
]

cases = {case: TEST_CASES[case] for case in CASES_TO_USE}
test_parameters = cases.keys()


@pytest.mark.parametrize("case_name", test_parameters)
def test_bulk_retrieval(case_name):
    """
    construct a "bulk" query from a defined set of parameters, and verify that
    a table produced from the concatenated responses matches a cached CSV file
    from Horizons.
    """
    case = cases[case_name]
    lhorizons = construct_lhorizon_list(**case["init_kwargs"])
    assert len(lhorizons) == case["lhorizon_count"]
    query_all_lhorizons(lhorizons)
    test_table = pd.concat([lhorizon.table() for lhorizon in lhorizons])
    test_table = test_table[case["use_columns"]].reset_index(drop=True)
    ref_table = pd.read_csv(case["data_path"] + ".csv")
    raise_badness(check_numeric_closeness(ref_table, test_table))


def test_retry_request_behavior(mocker):
    """
    networking behavior unit test. make sure query_all_lhorizons responds in
    the ways we would like to 503 responses.
    """
    failed_query = make_mock_failing_query(503)
    mocker.patch.object(LHorizon, "query", failed_query)
    futile_lhorizon = [LHorizon()]
    start = time.time()
    try:
        query_all_lhorizons(futile_lhorizon, delay_retry=0.1, max_retries=2)
    except TimeoutError:
        assert time.time() - start > 0.3
        return

    raise ValueError("did not correctly halt on multiple retries")


def test_list_sites():
    """
    simple test of the list_sites function. make sure the dataframe it
    produces from JPL's response has some expected features.
    """
    sites = list_sites()
    assert (
        sites.loc[sites["id"] == -1]["name"].iloc[0]
        == "Arecibo (300-m, 1963 to 2020)"
    )
    assert ",".join(sites.columns) == (
        "id,east long,cyl_rho,z,epoch,name"
    )


def test_list_majorbodies():
    """
    simple test of the list_majorbodies function. make sure the dataframe it
    produces from JPL's response has some expected features.
    """
    bodies = list_majorbodies()
    assert (
        bodies.loc[bodies["id"] == 1]["name"].iloc[0] == "Mercury Barycenter"
    )
    assert all(
        [
            bodies["name"].str.contains(unimportant_body).any()
            for unimportant_body in (
                "Earth",
                "Venus",
                "Phobos",
                "Pluto",
                "Sol",
                "Sycorax",
                "Chandrayaan",
            )
        ]
    )


def test_get_observer_quantity_codes():
    """
    simple test of the get_observer_quantity_codes function. make sure the
    string it produces from JPL's telnet response has some expected features.
    """
    codes = get_observer_quantity_codes()
    assert 'Astrometric' in codes
    assert '10. ' in codes
