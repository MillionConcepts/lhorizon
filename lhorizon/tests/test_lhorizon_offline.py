import datetime as dt
import re
import warnings

import pandas as pd
import pytest

from lhorizon import LHorizon
from lhorizon.lhorizon_utils import dt_to_jd
from lhorizon.tests.data.test_cases import TEST_CASES
from lhorizon.tests.utilz import make_mock_query_from_test_case, numeric_closeness


def test_prepare_request_1():
    case = TEST_CASES["CYDONIA_PALM_SPRINGS_1959_TOPO"]
    test_lhorizon = LHorizon(**case["init_kwargs"])
    test_lhorizon.prepare_request()
    assert test_lhorizon.request.url == case["request_url"]


def test_prepare_request_2():
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
    case = TEST_CASES["SUN_PHOBOS_1999"]
    test_lhorizon = LHorizon(**case["init_kwargs"])
    test_lhorizon.prepare_request()
    assert test_lhorizon.request.url == case["request_url"]


def test_prepare_request_4():
    case = TEST_CASES["WEIRD_OPTIONS"]
    test_lhorizon = LHorizon(**case["init_kwargs"])
    assert test_lhorizon.request.url == case["request_url"]


def test_reject_long_query():
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
    case = TEST_CASES["CYDONIA_PALM_SPRINGS_1959_TOPO"]
    mock_query = make_mock_query_from_test_case(case)
    mocker.patch.object(LHorizon, "query", mock_query)
    test_lhorizon = LHorizon(**case["init_kwargs"])
    table = test_lhorizon.table()
    saved_table = pd.read_csv(case["data_path"] + "_OBSERVER_table.csv")
    assert numeric_closeness(table, saved_table)

