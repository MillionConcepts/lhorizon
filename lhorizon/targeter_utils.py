from itertools import repeat
from typing import Sequence

import numpy as np
import spiceypy as spice

from lhorizon._type_aliases import Array


def array_reference_shift(
    positions: Array,
    time_series: Sequence,
    origin: str,
    destination: str,
    wide: bool = False,
):
    """
    using SPICE / SpiceyPy, transform an array of position vectors from origin
    (frame) to destination (frame) at times in time_series. also computes
    spherical representation of these coordinates. time_series must be in et
    (seconds since J2000). Appropriate SPICE kernels must be loaded
    prior to calling this function using `spiceypy.furnsh()` or an
    even higher-level interface to `FURNSH` like
    `lhorizon.kernels.load_metakernel()`
    """
    output_positions = []
    if wide is True:
        transformation_matrices = repeat(
            spice.pxform(origin, destination, time_series[0])
        )
    else:
        transformation_matrices = iter(
            [spice.pxform(origin, destination, time) for time in time_series]
        )
    for coordinate in positions:
        transformation_matrix = next(transformation_matrices)
        # some common numpy workflows that might call this array create strided
        # arrays that the cspice backend chokes on. copying them makes them
        # contiguous in memory again.
        if np.isnan(coordinate).any():
            output_positions.append(np.array(np.repeat(np.nan, 5)))
            continue
        output_coord = spice.mxv(transformation_matrix, coordinate.copy())
        [_, lon, lat] = spice.reclat(output_coord)
        output_coord = np.append(
            output_coord, [lon * spice.dpr(), lat * spice.dpr()]
        )
        output_positions.append(output_coord)
    # feeding nan values to spice.reclat results in 0s; we want those values
    # to be nan as well
    try:
        return np.vstack(output_positions)
    except ValueError:
        return ValueError
