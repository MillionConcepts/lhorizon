from itertools import repeat
from typing import Sequence, Optional, Iterable, Union

from more_itertools import divide
import numpy as np
import spiceypy as spice

from lhorizon._type_aliases import Array
from lhorizon.lhorizon_utils import cart2sph


def array_reference_shift(
    positions: Array,
    time_series: Sequence[float],
    origin: str,
    destination: str,
    wide: bool = False,
):
    """
    transform an array of position vectors from origin (frame) to destination
    (frame) at times in time_series, using SPICE/SpiceyPy to compute
    coordinate transformation matrices. also computes spherical representation
    of these coordinates.
    time_series must be in et (seconds since J2000).
    Appropriate SPICE kernels must be loaded prior to calling this function
    using `spiceypy.furnsh()` or an even higher-level interface to `FURNSH`
    like `lhorizon.kernels.load_metakernel()`.
    if wide = True, array_reference_shift will use the first time in the
    passed time series to transform all vectors in the array.
    """
    transformation_matrices = generate_transformation_matrices(
        origin, destination, time_series, wide
    )
    return transform_vectors(positions, transformation_matrices)


def generate_transformation_matrices(
    origin, destination, time_series, wide=False
):
    if wide is True:
        transformation_matrices = repeat(
            spice.pxform(origin, destination, next(iter(time_series)))
        )
    else:
        transformation_matrices = [
            spice.pxform(origin, destination, time)
            for time in time_series
        ]
    return transformation_matrices


def transform_vectors(
    positions: np.ndarray, matrices: Union[Iterable[np.ndarray], np.ndarray]
):
    output = []
    for matrix, pos in zip(matrices, positions):
        output.append(np.matmul(matrix, pos))
    output = np.vstack(output)
    lat, lon, _ = cart2sph(output[:, 0], output[:, 1], output[:, 2])
    return np.hstack([output, np.vstack([lon, lat]).T])
