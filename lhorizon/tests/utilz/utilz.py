import json

from lhorizon._response_parsers import (
    make_horizon_dataframe,
    polish_horizons_table,
)


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


def parse_test_setup(case, query_type):
    with open(case["data_path"] + "_" + query_type, "rb") as file:
        test_text = file.read().decode()
    test_df = make_horizon_dataframe(test_text)
    test_table = polish_horizons_table(test_df, query_type)
    return test_df, test_table
