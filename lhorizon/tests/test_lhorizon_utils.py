import math
import re

import numpy as np
import pandas as pd
from more_itertools import chunked

from lhorizon.lhorizon_utils import (
    hats,
    is_it,
    sph2cart,
    hunt_csv,
    snorm,
    listify, cart2sph,
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


def test_roundtrip_transform():
    cart = rng.integers(0, 10, 3)
    assert np.allclose(cart, sph2cart(*cart2sph(*cart)))
    sph = np.array([
        rng.integers(-90, 90), rng.integers(0, 359), rng.integers(1, 100)
    ])
    assert np.allclose(sph, cart2sph(*sph2cart(*sph)))


def test_hunt_csv_1():
    raining = re.compile(r"(?<=cats).*(?=dogs)")
    some_csv = "catssomething,something_else,1,2dogs"
    assert hunt_csv(raining, some_csv) == [
        "something",
        "something_else",
        "1",
        "2",
    ]


def test_hunt_csv_2():
    ints = rng.integers(0, 100, 8)
    breaks = rng.choice(("\r", "\n", "\r\n"), 3)
    block = (
        f"alpha{ints[0]},{ints[1]}{breaks[0]}"
        f"{ints[2]},{ints[3]}{breaks[1]}{ints[4]},{ints[5]}{breaks[2]}"
        f"{ints[6]},{ints[7]}beta"
    )
    table = hunt_csv(re.compile(r"(?<=alpha).*(?=beta)", re.M + re.S), block)
    table = list([list(map(int, line)) for line in table])
    assert list(map(sum, table)) == list(map(sum, chunked(ints, 2)))


def test_snorm_1():
    thing = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    normed = snorm(thing, 0, 1, 2, 9)
    assert math.isclose(normed[1], 0)
    assert math.isclose(normed[8], 1)


def test_snorm_2():
    thing = rng.normal(rng.integers(-1000, 1000), rng.integers(1, 100), 100000)
    # this will fail about one in ten million times.
    assert abs(np.mean(snorm(thing)) - 0.5) < 0.11


def test_snorm_3():
    number = rng.integers(-1000, 1000)
    assert math.isclose(snorm(number, 0, 1, 0, number * 2), 0.5)


def test_listify():
    assert isinstance(listify("asdfasdf"), list)
    assert isinstance(listify([1, 2, 3, 4]), list)
    assert isinstance(listify(1), list)
    assert isinstance(listify(map(sum, [(1, 2, 3), (1, 2, 3)])), list)

