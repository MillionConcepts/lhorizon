import math

import numpy as np

import lhorizon.tests.data.test_cases as test_cases
from lhorizon.tests.utilz import parse_test_setup


def test_observer_parsing_1():
    case = test_cases.CYDONIA_PALM_SPRINGS_1959_TOPO
    df, table = parse_test_setup(case, "OBSERVER")
    assert ",".join(table.columns.to_list()) == case["observer_table_columns"]
    assert np.allclose(
        table["ra_ast"].iloc[12:15], np.array(case["ra_ast_12_15"])
    )


def test_observer_parsing_2():
    case = test_cases.SUN_PHOBOS_1999
    df, table = parse_test_setup(case, "OBSERVER")
    assert ",".join(df.columns.to_list()) == case["observer_df_columns"]
    assert math.isclose(df["App_Lon_Sun"].iloc[0], case["App_Lon_Sun"])
    assert math.isclose(table["dist"].iloc[0], case["dist"])


def test_vectors_parsing_1():
    case = test_cases.CYDONIA_PALM_SPRINGS_1959_TOPO
    df, table = parse_test_setup(case, "VECTORS")
    assert ",".join(table.columns.to_list()) == case["vectors_table_columns"]
    assert np.allclose(
        table["vz"].iloc[10:13].values, np.array(case["vz_10_13"])
    )


def test_vectors_parsing_2():
    case = test_cases.SUN_PHOBOS_1999
    df, table = parse_test_setup(case, "VECTORS")
    assert ",".join(tuple(df.columns.values)) == case["vectors_df_columns"]
    assert df["JDTDB"].iloc[0] == case["JDTDB"]
    assert math.isclose(table["x"].iloc[0], case["x"])
