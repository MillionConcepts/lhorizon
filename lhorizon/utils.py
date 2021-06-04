from collections.abc import Sequence
from typing import Any

from astropy.utils import isiterable


def listify(thing: Any) -> list:
    """Always a list, for things that want lists"""
    if isinstance(thing, str) or (not isinstance(Sequence, thing)):
        return [thing]
    return list(thing)


def snorm(thing, minimum=0, maximum=1, m0=None, m1=None):
    """simple min-max scaler"""
    if not isiterable(thing):
        thing = listify(thing)
    if m0 is None:
        m0 = min(thing)
    if m1 is None:
        m1 = max(thing)
    scale = (maximum - minimum) / (m1 - m0)
    shift = minimum - m0 * scale
    scaled = [x * scale + shift for x in thing]
    if len(scaled) == 1:
        return scaled[0]
    return scaled
