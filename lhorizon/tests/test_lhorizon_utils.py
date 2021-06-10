import math

import numpy as np
import pandas as pd

from lhorizon.lhorizon_utils import (
    hats,
    is_it,
    sph2cart,
    hunt_csv,
    snorm,
    listify,
)

rng = np.random.default_rng()


def test_hats_1():
    length = rng.integers(2, 1000)
    vector = np.ones(length)
    normed = hats(vector)
    assert math.isclose(normed.sum(), math.sqrt(length))


def test_hats_2():
    raining = pd.DataFrame(
        {"cats": rng.integers(1, 100, 100), "dogs": rng.integers(1, 10, 100)}
    )
    norm_raining = hats(raining)
    test_row = norm_raining.iloc[49]
    assert math.isclose(test_row["cats"] ** 2 + test_row["dogs"] ** 2, 1)


def test_is_it():
    this_range = range(100)
    is_rangelike = is_it(range, list, tuple)
    assert is_rangelike(this_range)
    assert is_rangelike(list(this_range))
    assert not is_rangelike("asdfasdfasdf")


def test_sph2cart():
    up = sph2cart(90, 90, 1)
    assert math.isclose(up[0], 0, abs_tol=1e-9)
    assert math.isclose(up[1], 0, abs_tol=1e-9)
    assert math.isclose(up[2], 1, abs_tol=1e-9)


def test_hunt_csv():
    raining = r"(?<=cats).*(?=dogs)"
    some_csv = "catssomething,something_else,1,2dogs"
    assert hunt_csv(raining, some_csv) == [
        "something",
        "something_else",
        "1",
        "2",
    ]


def test_snorm():
    thing = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    normed = snorm(thing, 0, 1, 2, 9)
    assert math.isclose(normed[1], 0)
    assert math.isclose(normed[8], 1)


def test_listify():
    assert isinstance(listify("asdfasdf"), list)
    assert isinstance(listify([1, 2, 3, 4]), list)
    assert isinstance(listify(1), list)
    assert isinstance(listify(map(sum, [(1, 2, 3), (1, 2, 3)])), list)
