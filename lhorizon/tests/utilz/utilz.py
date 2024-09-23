"""utilities for `lhorizon` tests"""

import json

import numpy as np
import pandas as pd

from lhorizon.lhorizon_utils import numeric_columns


class MockResponse:
    """
    a mock requests response
    """

    def __init__(
        self,
        content=None,
        text=None,
        url=None,
        headers=None,
        content_type=None,
        auth=None,
        status_code=200,
    ):
        assert content is None or hasattr(content, "decode")
        self.content = content
        if (text is None) and (content is not None):
            text = self.content.decode()
        self.text = text
        self.raw = content
        if headers is None:
            headers = {}
        self.headers = headers
        if content_type is not None:
            self.headers["Content-Type"] = content_type
        self.url = url
        self.auth = auth
        self.status_code = status_code

    def iter_lines(self):
        lines = self.content.split(b"\n")
        for line in lines:
            yield line

    def raise_for_status(self):
        pass

    def json(self):
        try:
            return json.loads(self.content)
        except TypeError:
            return json.loads(self.content.decode("utf-8"))


def make_mock_failing_query(status_code):
    """mock wrapper for LHorizon.query() that returns status codes only"""

    def mock_query(self, *args, **kwargs):
        self.response = MockResponse(status_code=status_code)

    return mock_query


def make_mock_query_from_test_case(test_case, query_type_suffix="OBSERVER"):
    """mock wrapper for LHorizon.query()"""

    def mock_query(self, *args, **kwargs):
        with open(
            test_case["data_path"] + "_" + query_type_suffix, "rb"
        ) as file:
            self.response = MockResponse(content=file.read())

    return mock_query


def raise_badness(bad_table, bad_df=None):
    bad_table_str = ", ".join(f"{k}: (max {v})" for k, v in bad_table.items())
    if bad_df is not None:
        bad_df_str = ", ".join(f"{k}: (max {v})" for k, v in bad_df.items())
    else:
        bad_df_str = ""
    if len(bad_df_str) + len(bad_table_str) > 0:
        errstring = f"value mismatches. table: {bad_table_str}."
        if bad_df is not None:
            errstring += f"df: {bad_df_str}."
        raise ValueError(errstring)


def check_against_reference(case, query_type, test_df, test_table):
    """
    skeleton test function for comparing the output of a response parser with
    a saved table
    """
    path = case["data_path"] + "_" + query_type
    ref_df = pd.read_csv(path + "_df.csv")
    ref_table = pd.read_csv(path + "_table.csv")
    # chop off columns that are produced after response
    for frame in (test_df, ref_df, test_table, ref_table):
        frame.drop(
            columns=["geo_lon", "geo_lat", "geo_el"],
            errors="ignore",
            inplace=True
        )
    assert set(ref_df.columns.values) == set(test_df.columns.values)
    bad_df = check_numeric_closeness(ref_df, test_df)
    bad_table = check_numeric_closeness(ref_table, test_table)
    raise_badness(bad_table, bad_df)


def check_numeric_closeness(ref_table, test_table, round_to=6):
    bad = {}
    for c in numeric_columns(test_table):
        if np.allclose(test_table[c], ref_table[c]):
            continue
        bad[c] = round(max(abs(test_table[c] - ref_table[c])), round_to)
    return bad


def make_sure_this_fails(
    procedure, args=None, kwargs=None, expected_error_type=ValueError
):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    try:
        procedure(*args, **kwargs)
        raise RuntimeError("that shouldn't have worked!")
    except Exception as e:
        assert isinstance(
            e, expected_error_type
        ), "that should have failed differently!"


class PointlessTargeter:
    def __init__(self):
        self.ephemerides = {}
