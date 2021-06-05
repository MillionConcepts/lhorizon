"""
some of these tests are near versions of ones in astroquery, some written by
me and some preexisting.
"""

import re

from astropy.time import Time

from lhorizon import LHorizon
import lhorizon.tests.data.test_cases as test_cases
from lhorizon.tests.utilz import make_mock_fetch

# files in data/ for different query types

# DATA_FILES = {
#     "ephemerides": "ceres_ephemerides.txt",
#     "elements": "ceres_elements.txt",
#     "vectors": "ceres_vectors.txt",
#     '"2010 NY104;"': "no_H.txt",
# }

#
# def data_path(filename):
#     data_dir = os.path.join(os.path.dirname(__file__), "data")
#     return os.path.join(data_dir, filename)
#

# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
# @pytest.fixture
# def patch_request(request):
#     monkeypatch = request.getfixturevalue("monkeypatch")
#     monkeypatch.setattr(LHorizon, "response", nonremote_request)
#     return monkeypatch


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


# note that pd.read_csv behaves differently under test in PyCharm, for reasons
# that must be horrible
def test_make_table_1(mocker):
    case = test_cases.CYDONIA_PALM_SPRINGS_1959_TOPO
    mock_fetch = make_mock_fetch(case)
    mocker.patch.object(LHorizon, "fetch", mock_fetch)
    test_lhorizon = LHorizon(**case["init_kwargs"])
    test_table = test_lhorizon.table()
    assert tuple(test_table.columns.values) == case["table_columns"]
    assert tuple(test_table['ra_ast'].values[12:15]) == case['ra_ast_12_15']