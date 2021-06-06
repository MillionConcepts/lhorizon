import json
import logging

import numpy as np
import pandas as pd
from lhorizon import LHorizon
from lhorizon._response_parsers import (
    make_horizon_dataframe,
    polish_horizons_table,
)
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


def make_mock_query(test_case, query_type_suffix="OBSERVER"):
    def mock_query(self, *args, **kwargs):
        with open(
            test_case["data_path"] + "_" + query_type_suffix, "rb"
        ) as file:
            self.response = MockResponse(content=file.read())

    return mock_query


def check_against_reference(case, query_type, test_df, test_table):
    path = case["data_path"] + "_" + query_type
    ref_df = pd.read_csv(path + "_df.csv")
    ref_table = pd.read_csv(path + "_table.csv")
    if query_type.lower() + "_table_columns" in case.keys():
        assert (
                ",".join(test_table.columns.to_list())
                == case[query_type.lower() + "_table_columns"]
        )
    if query_type.lower() + "_df_columns" in case.keys():
        assert (
                ",".join(test_df.columns.to_list())
                == case[query_type.lower() + "_df_columns"]
        )
    assert np.allclose(test_df[numeric_columns(test_df)], ref_df.values)
    assert np.allclose(
        test_table[numeric_columns(test_table)], ref_table.values
    )


def execute_parser_test(case, query_type):
    path = case["data_path"] + "_" + query_type
    with open(path, "rb") as file:
        test_text = file.read().decode()
    test_df = make_horizon_dataframe(test_text)
    test_table = polish_horizons_table(test_df, query_type)
    check_against_reference(case, query_type, test_df, test_table)
    logging.getLogger().info(path + " parsed")






