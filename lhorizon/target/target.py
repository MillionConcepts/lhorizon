import warnings

import numpy as np
import spiceypy as spice
from numpy.linalg import norm

from lhorizon.lhorizon_utils import sph2cart, hat
from lhorizon.target.solutions import make_ray_sphere_lambdas


def array_reference_shift(positions, time_series, origin, destination):
    """
    using SPICE, transform an array of position vectors from origin (frame) to
    destination (frame) at times in time_series. also computes spherical
    representation of these coordinates. time_series must be in et (seconds
    since J2000)
    """
    output_positions = []
    for index, coordinate in enumerate(positions):
        time_at_index = time_series[index]
        transformation_matrix = spice.pxform(
            origin, destination, time_at_index
        )
        # some common numpy workflows that might call this array create strided
        # arrays that the cspice backend chokes on. copying them makes them
        # contiguous in memory again.
        output_coord = spice.mxv(transformation_matrix, coordinate.copy())
        [_, lon, lat] = spice.reclat(output_coord)
        output_coord = np.append(
            output_coord, [lon * spice.dpr(), lat * spice.dpr()]
        )
        output_positions.append(output_coord)
    try:
        return np.vstack(output_positions)
    except ValueError:
        return ValueError

    # @param intersection_solver: function that, given target_shape_properties
    #     as kwargs, must return a mapping of functions that each accept six args
    #     -- x1, y1, z1, x2, y2, z2 -- and return at least x, y, z position of
    #     an "intersection" (however defined). for compatibility with other
    #     functions in this module, should return NaN values for cases in which
    #     no intersection is found.


    # solutions = intersection_solver(**target_shape_properties)
    # @param target_shape_properties: any target shape properties (radius,
    #     obliquity, etc.) required by the solver

def find_intersections(
    target_center,
    origin_direction_vector,
    intersection_solutions=None,
    representation="spherical",
    target_radius=None,
):
    """
    note that target center vector and pointing vectors must be in the same
    frame of reference or downstream results will be silly.
    @param target_center: vector giving location of target center relative to
        origin

    @param origin_direction_vector: vector giving boresight pointing /
        direction of ray from origin
    @param intersection_solutions: mapping of functions that each accept six
        args -- x1, y1, z1, x2, y2, z2 -- and return at least x, y, z position
        of an "intersection" (however defined). for compatibility with other
        functions in this module, should return NaN values for cases in which
        no intersection is found. if this parameter is not passed, generates
        ray-sphere solutions from the passed target radius.
    @param representation: representation type of passed coordinates --
        either sph/spherical or cart/cartesian, default spherical
    """
    # mapping of equations, one for each relevant coordinate, giving location
    # of intersection b/w ray and body
    if (intersection_solutions is None) and (target_radius is None):
        raise ValueError(
            "find_intersections() requires either an explicit system of "
            "solutions or a target radius (in which case it will assume the "
            "target is spherical)"
        )
    elif intersection_solutions is None:
        intersection_solutions = make_ray_sphere_lambdas(target_radius)
    if not representation.startswith("sph") or representation.startswith(
        "cart"
    ):
        raise ValueError(
            "find_intersections() accepts only sph/spherical or "
            "cart/cartesian vector representations"
        )
    # unit vector giving pointing from origin
    if representation.startswith("sph"):
        origin_direction_vector = sph2cart(*origin_direction_vector)
    ray_direction = hat(origin_direction_vector)
    # vector giving location of target center
    if representation.startswith("sph"):
        target_center = sph2cart(*target_center)
    # suppress irrelevant warnings about imaginary values
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return {
            coordinate: solution(*ray_direction, *target_center)
            for coordinate, solution in intersection_solutions.items()
        }



    # TODO: break this out into a special case
    # # center pixel space at the origin
    # dec_grid, ra_grid = np.meshgrid(dec_axis, ra_axis)
    # dec_grid += dec_center_value
    # ra_grid += ra_center_value
    # unit vectors giving pointing directions for each pixel
    # pointing_grid = np.array(sph2cart(dec_grid, ra_grid, 1))

    # system of equations for ray-body intersection problem
