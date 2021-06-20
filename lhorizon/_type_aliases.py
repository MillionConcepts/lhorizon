import datetime as dt
from typing import Union

import numpy as np
import pandas as pd

# type aliases
Array = Union[pd.DataFrame, pd.Series, np.ndarray]
Ephemeris = Union[pd.DataFrame, "LHorizon"]
Timelike = Union[str, dt.datetime, float]