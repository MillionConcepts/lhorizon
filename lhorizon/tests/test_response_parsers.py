from itertools import product

import pytest
from lhorizon._response_parsers import make_lhorizon_dataframe, \
    polish_lhorizon_dataframe
from lhorizon.tests.data.test_cases import TEST_CASES
from lhorizon.tests.utilz import check_against_reference

CASES_TO_USE = (
    "SUN_PHOBOS_1999",
    "CERES_2000",
    "CYDONIA_PALM_SPRINGS_1959_TOPO",
)
cases = {case: TEST_CASES[case] for case in CASES_TO_USE}
test_parameters = product(cases.keys(), ("OBSERVER", "VECTORS"))


@pytest.mark.parametrize("case_name,query_type", test_parameters)
def test_response_parser(case_name: str, query_type: str):
    case = cases[case_name]
    path = case["data_path"] + "_" + query_type
    with open(path, "rb") as file:
        test_text = file.read().decode()
    test_df = make_lhorizon_dataframe(test_text)
    test_table = polish_lhorizon_dataframe(test_df, query_type)
    check_against_reference(case, query_type, test_df, test_table)
