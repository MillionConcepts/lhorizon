import math
import os
import re

from astropy.time import Time

from lhorizon import LHorizon
import lhorizon.tests.data.test_cases as test_cases
from lhorizon.tests.utilz import make_mock_fetch
from lhorizon._response_parsers import (
    make_horizon_dataframe,
    polish_horizons_table,
)


def test_ephemerides_parsing_1():
    case = test_cases.CYDONIA_PALM_SPRINGS_1959_TOPO
    with open(case["data_path"], "rb") as file:
        test_text = file.read().decode()
    test_df = make_horizon_dataframe(test_text)
    test_table = polish_horizons_table(test_df)
    assert tuple(test_table.columns.values) == case["table_columns"]
    assert tuple(test_table["ra_ast"].values[12:15]) == case["ra_ast_12_15"]


def test_ephemerides_parsing_2():
    case = test_cases.SUN_PHOBOS_1999
    with open(case["data_path"], "rb") as file:
        test_text = file.read().decode()
    test_df = make_horizon_dataframe(test_text)
    test_table = polish_horizons_table(test_df)
    assert ",".join(tuple(test_df.columns.values)) == case["df_columns"]
    assert math.isclose(test_df["App_Lon_Sun"].iloc[0], case["App_Lon_Sun"])
    assert math.isclose(test_table["dist"].iloc[0], case["dist"])
