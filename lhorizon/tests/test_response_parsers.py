from itertools import product

import pytest
from lhorizon._response_parsers import make_horizon_dataframe, \
    polish_horizons_table
from lhorizon.tests.data.test_cases import TEST_CASES
from lhorizon.tests.utilz import check_against_reference

CASES_TO_USE = (
    "CERES_2000",
    "CYDONIA_PALM_SPRINGS_1959_TOPO",
    "SUN_PHOBOS_1999",
)
cases = {k: v for k, v in TEST_CASES.items() if k in CASES_TO_USE}
test_parameters = product(cases.keys(), ("OBSERVER", "VECTORS"))


@pytest.mark.parametrize("case_name,query_type", test_parameters)
def test_response_parser(case_name, query_type):
    case = cases[case_name]
    path = case["data_path"] + "_" + query_type
    with open(path, "rb") as file:
        test_text = file.read().decode()
    test_df = make_horizon_dataframe(test_text)
    test_table = polish_horizons_table(test_df, query_type)
    check_against_reference(case, query_type, test_df, test_table)
