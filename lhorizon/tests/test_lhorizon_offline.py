import re
import warnings

from astropy.time import Time
import numpy as np
import pytest

from lhorizon import LHorizon
import lhorizon.tests.data.test_cases as test_cases
from lhorizon.tests.utilz import make_mock_query


def test_prepare_request_1():
    case = test_cases.CYDONIA_PALM_SPRINGS_1959_TOPO
    test_lhorizon = LHorizon(**case["init_kwargs"])
    test_lhorizon._prepare_request()
    assert test_lhorizon.request.url == case["request_url"]


def test_prepare_request_2():
    case = test_cases.MEUDON_MOON_NOW
    test_lhorizon = LHorizon(**case["init_kwargs"])
    test_lhorizon._prepare_request()
    assert test_lhorizon.request.url.startswith(case["request_url"])
    assert round(Time.now().jd, 4) == round(
        float(
            re.search(r"TLIST=([\d.]+)", test_lhorizon.request.url).group(1)
        ),
        4,
    )


def test_prepare_request_3():
    case = test_cases.SUN_PHOBOS_1999
    test_lhorizon = LHorizon(**case["init_kwargs"])
    test_lhorizon._prepare_request()
    assert test_lhorizon.request.url == case["request_url"]


def test_prepare_request_4():
    case = test_cases.WEIRD_OPTIONS
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
    case = test_cases.CYDONIA_PALM_SPRINGS_1959_TOPO
    mock_query = make_mock_query(case)
    mocker.patch.object(LHorizon, "query", mock_query)
    test_lhorizon = LHorizon(**case["init_kwargs"])
    test_table = test_lhorizon.table()
    assert (
        ",".join(tuple(test_table.columns.values))
        == case["observer_table_columns"]
    )
    assert np.allclose(
        test_table["ra_ast"].values[12:15], np.array(case["ra_ast_12_15"])
    )
