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
from lhorizon.tests.utilz import numeric_closeness, make_mock_failing_query

CASES_TO_USE = [
    "MARS_SUN_ANGLE_MINIMAL",
]

cases = {case: TEST_CASES[case] for case in CASES_TO_USE}
test_parameters = cases.keys()


@pytest.mark.parametrize("case_name", test_parameters)
def test_bulk_retrieval(case_name):
    case = cases[case_name]
    lhorizons = construct_lhorizon_list(**case["init_kwargs"])
    assert len(lhorizons) == case["lhorizon_count"]
    query_all_lhorizons(lhorizons)
    test_table = pd.concat([lhorizon.table() for lhorizon in lhorizons])[
        case["use_columns"]
    ]
    ref_table = pd.read_csv(case["data_path"] + ".csv")
    assert numeric_closeness(ref_table, test_table)


def test_retry_request_behavior(mocker):
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
    sites = list_sites()
    assert (
        sites.loc[sites["id"] == "-1"]["Observatory Name"].iloc[0] == "Arecibo"
    )
    assert ",".join(sites.columns) == "id,E. Lon,DXY,DZ,Observatory Name"


def test_list_majorbodies():
    bodies = list_majorbodies()
    assert (
        bodies.loc[bodies["id"] == "1"]["name"].iloc[0] == "Mercury Barycenter"
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
    codes = get_observer_quantity_codes()
    assert 'Astrometric' in codes
    assert '10. ' in codes