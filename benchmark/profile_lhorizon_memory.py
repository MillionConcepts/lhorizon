from pathlib import Path

from memory_profiler import profile
import pandas as pd

from lhorizon import LHorizon
from lhorizon.tests.utilz import MockResponse

# grab cached http responses from JPL Horizons
def make_mock_response(cached_response_fn):
    def respond_mockingly(*args, **kwargs):
        with open(cached_response_fn, 'rb') as mock_response_stream:
            mock_response_bytes = mock_response_stream.read()
        return MockResponse(content=mock_response_bytes)
    return respond_mockingly


cached_responses = {
    r.name.split("_")[-1]: r
    for r in Path('../examples/').iterdir()
    if 'response' in r.name
}


# insert these responses into lhorizon.LHorizon objects
mocked_lhorizons = []
for response_ix in sorted(cached_responses.keys()):
    mock_response = make_mock_response(cached_responses[response_ix])
    lhorizon = LHorizon()
    lhorizon.response = mock_response()
    mocked_lhorizons.append(lhorizon)


@profile
def assemble_mocked_lhorizons(mocked_lhorizons_list):
    lhorizon_dataframes = [
        lh.dataframe() for lh in mocked_lhorizons_list
    ]
    return pd.concat(lhorizon_dataframes)


assemble_mocked_lhorizons(mocked_lhorizons)