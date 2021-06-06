import math

import numpy as np

import lhorizon.tests.data.test_cases as test_cases
from lhorizon.lhorizon_utils import numeric_columns
from lhorizon.tests.utilz import execute_parser_test


cases = (
    test_cases.CERES_2000,
    test_cases.CYDONIA_PALM_SPRINGS_1959_TOPO,
    test_cases.SUN_PHOBOS_1999
)


def test_observer_parsing():
    for case in cases:
        execute_parser_test(case, "OBSERVER")


def test_vectors_parsing():
    for case in cases:
        execute_parser_test(case, "VECTORS")
#
# def test_observer_parsing_1():
#     case = test_cases.CYDONIA_PALM_SPRINGS_1959_TOPO
#     df, table, ref_df, ref_table = parse_test_setup(case, "OBSERVER")
#     assert ",".join(table.columns.to_list()) == case["observer_table_columns"]
#     assert np.allclose(df[numeric_columns(df)], ref_df.values)
#     assert np.allclose(table[numeric_columns(table)], ref_table.values)
#
#
# def test_observer_parsing_2():
#     case = test_cases.SUN_PHOBOS_1999
#     df, table, ref_df, ref_table = parse_test_setup(case, "OBSERVER")
#     assert ",".join(df.columns.to_list()) == case["observer_df_columns"]
#     assert np.allclose(df[numeric_columns(df)], ref_df.values)
#     assert np.allclose(table[numeric_columns(table)], ref_table.values)
#
#
# def test_vectors_parsing_1():
#     case = test_cases.CYDONIA_PALM_SPRINGS_1959_TOPO
#     df, table, ref_df, ref_table = parse_test_setup(case, "VECTORS")
#     assert (
#         ",".join(tuple(table.columns.values)) == case["vectors_table_columns"]
#     )
#     assert np.allclose(df[numeric_columns(df)], ref_df.values)
#     assert np.allclose(table[numeric_columns(table)], ref_table.values)
#
#
# def test_vectors_parsing_2():
#     case = test_cases.SUN_PHOBOS_1999
#     df, table, ref_df, ref_table = parse_test_setup(case, "VECTORS")
#     assert ",".join(tuple(df.columns.values)) == case["vectors_df_columns"]
#     assert np.allclose(df[numeric_columns(df)], ref_df.values)
#     assert np.allclose(table[numeric_columns(table)], ref_table.values)
