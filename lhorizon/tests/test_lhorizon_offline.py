"""
tests of `LHorizon` functionality using locally-cached HTTP responses from
_Horizons_
"""

import datetime as dt
import re
import warnings

import pandas as pd
import pytest

from lhorizon import LHorizon
from lhorizon.lhorizon_utils import dt_to_jd
from lhorizon.tests.data.test_cases import TEST_CASES
from lhorizon.tests.utilz import (
    make_mock_query_from_test_case, numeric_closeness
)


def test_prepare_request_1():
    """
    test for consistency of URL-formatting behavior: is the LHorizon
    instance producing the URL we think it should? this case has topocentric
    coordinates.
    """
    case = TEST_CASES["CYDONIA_PALM_SPRINGS_1959_TOPO"]
    test_lhorizon = LHorizon(**case["init_kwargs"])
    test_lhorizon.prepare_request()
    assert test_lhorizon.request.url == case["request_url"]


def test_prepare_request_2():
    """
    test for consistency of URL-formatting behavior: is the LHorizon
    instance producing the URL we think it should? this is an "instantaneous"
    request that has no defined time field, so also check that the
    timestamp in this URL corresponds to the time of the system clock
    (converted to jd).
    """
    case = TEST_CASES["MEUDON_MOON_NOW"]
    test_lhorizon = LHorizon(**case["init_kwargs"])
    test_lhorizon.prepare_request()
    assert test_lhorizon.request.url.startswith(case["request_url"])
    assert round(dt_to_jd(dt.datetime.utcnow()), 4) == round(
        float(
            re.search(r"TLIST=([\d.]+)", test_lhorizon.request.url).group(1)
        ),
        4,
    )


def test_prepare_request_3():
    """
    test for consistency of URL-formatting behavior: is the LHorizon
    instance producing the URL we think it should?
    """
    case = TEST_CASES["SUN_PHOBOS_1999"]
    test_lhorizon = LHorizon(**case["init_kwargs"])
    test_lhorizon.prepare_request()
    assert test_lhorizon.request.url == case["request_url"]


def test_prepare_request_4():
    """
    test for consistency of URL-formatting behavior: is the LHorizon
    instance producing the URL we think it should? includes correct output
    from a lot of 'unusual' options.
    """
    case = TEST_CASES["WEIRD_OPTIONS"]
    test_lhorizon = LHorizon(**case["init_kwargs"])
    assert test_lhorizon.request.url == case["request_url"]


def test_reject_long_query():
    """
    LHorizon should fail if we naively attempt to initialize it with an
    extremely long query. This test attempts to make it fail in that way.
    """
    with pytest.raises(ValueError):
        LHorizon(epochs=[2459371 + i / 100 for i in range(10000)])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        LHorizon(
            epochs=[2459371 + i / 100 for i in range(10000)],
            allow_long_queries=True,
        )


# note that pd.read_csv behaves differently under test in PyCharm, for reasons
# that must be horrible
def test_make_table_1(mocker):
    """
    e2e test comparing attributes of LHorizon created by parsing
    cached HTTP response to values in saved CSV table
    """
    case = TEST_CASES["CYDONIA_PALM_SPRINGS_1959_TOPO"]
    mock_query = make_mock_query_from_test_case(case)
    mocker.patch.object(LHorizon, "query", mock_query)
    test_lhorizon = LHorizon(**case["init_kwargs"])
    table = test_lhorizon.table()
    saved_table = pd.read_csv(case["data_path"] + "_OBSERVER_table.csv")
    assert numeric_closeness(table, saved_table)
