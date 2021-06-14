import warnings
from itertools import repeat

import numpy as np
import pandas as pd
import spiceypy as spice

from lhorizon import LHorizon
from lhorizon.lhorizon_utils import sph2cart, hats, utc_to_et
from lhorizon.solutions import make_ray_sphere_lambdas


def find_intersection(solutions, ray_direction, target_center):
    # suppress irrelevant warnings about imaginary values
    return {
        coordinate: solution(*ray_direction, *target_center)
        for coordinate, solution in solutions.items()
    }


def array_reference_shift(
    positions, time_series, origin, destination, wide=False
):
    """
    using SPICE, transform an array of position vectors from origin (frame) to
    destination (frame) at times in time_series. also computes spherical
    representation of these coordinates. time_series must be in et (seconds
    since J2000)
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

    # @param intersection_solver: function that, given
    # target_shape_properties as kwargs, must return a mapping of functions
    # that each accept six args -- x1, y1, z1, x2, y2, z2 -- and return at
    # least x, y, z position of an "intersection" (however defined). for
    # compatibility with other functions in this module, should return NaN
    # values for cases in which no intersection is found.

    # solutions = intersection_solver(**target_shape_properties)
    # @param target_shape_properties: any target shape properties (radius,
    #     obliquity, etc.) required by the solver


#         @param target_centers: vectors giving locations of target center
#             relative to origin
#         @param direction_vectors: vectors giving directions of rays from
#         origin
#             (perhaps boresight pointings, etc.)


class Targeter:
    def __init__(
        self,
        target,
        solutions=None,
        target_radius=None,
    ):
        """
        @param target: LHorizon instance or dataframe; if a dataframe, must
            have columns named 'ra, dec, dist', 'az, alt, dist', or 'x, y, z'
            if the LHorizon instance is an OBSERVER query, uses ra_app_icrf
            and dec_app_icrf, if VECTORS, uses x/y/z
        @param solutions: solutions: mapping of
        functions that each accept six args -- x1, y1, z1, x2, y2, z2 -- and
        return at least x, y, z position of an "intersection" (however
        defined). for compatibility with other functions in this module,
        should return NaN values for cases in which no intersection is
        found. if this parameter is not passed, generates ray-sphere
        solutions from the passed target radius.
        @param target_radius: used only if no intersection solutions are
            passed; generates a system of ray-sphere intersection solutions for
            a target body of this radius.
        """
        self.solutions = self._check_solution_arguments(
            solutions, target_radius
        )
        self.ephemerides = {}
        if isinstance(target, pd.DataFrame):
            self.ephemerides["body"] = self._coerce_df_cartesian(target)
            self.ephemerides["body"]["time"] = target["time"]
        elif isinstance(target, LHorizon):
            self.ephemerides["body"] = self._coerce_lhorizon_cartesian(target)
        else:
            raise ValueError(
                "Targeter must be initialized with a dataframe or a lhorizon."
            )

    @staticmethod
    def _coerce_df_cartesian(target):
        if {"x", "y", "z"}.issubset(set(target.columns)):
            return target
        else:
            if "dist" not in target.columns:
                target["dist"] = 1
            for lat, lon, radius in (
                ("dec_app_icrf", "ra_app_icrf", "dist"),
                ("dec", "ra", "dist"),
                ("alt", "az", "dist"),
            ):
                if {lat, lon, radius}.issubset(set(target.columns)):
                    coordinates = sph2cart(
                        target[lat], target[lon], target[radius]
                    )
                    return pd.concat([coordinates, target], axis=1)
        raise ValueError(
            "a passed dataframe must have columns named 'dec, ra', "
            "'alt, az', 'dec_app_icrf, ra_app_icrf' (and optionally 'dist'), "
            "or 'x, y, z'"
        )

    @staticmethod
    def _check_solution_arguments(solutions, target_radius):
        if (solutions is None) and (target_radius is None):
            raise ValueError(
                "this function requires either an explicit system of "
                "solutions or a target radius (in which case it will "
                "assume the target is spherical)"
            )
        elif solutions is None:
            solutions = make_ray_sphere_lambdas(target_radius)
        return solutions

    @staticmethod
    def _coerce_lhorizon_cartesian(target):
        table = target.table()
        if target.query_type == "VECTORS":
            return table
        elif target.query_type == "OBSERVER":
            coordinates = sph2cart(
                table["dec_app_icrf"],
                table["ra_app_icrf"],
                table["dist"],
            )
            return pd.concat([coordinates, table], axis=1)
        raise ValueError(
            "Only VECTORS and OBSERVER JPL Horizons queries can be used "
            "as a basis for a Targeter."
        )

    def find_targets(self, pointings):
        """
        note that target center vector and pointing vectors must be in the same
        frame of reference (source_frame) or downstream results will be silly.

        if you pass it a set of pointings without a time field, it will assume
        that their time field is identical to the time field of the target
        ephemeris.

        unless you do something extremely fancy in the solver,
        the _intersections_ will be 'geometric' quantities and thus reintroduce
        some error due to light-time, rotation, aberration, etc. between target
        body surface and target body center -- but considerably less error than
        if you don't have a corrected vector from origin to target body center.
        """
        pointing_ephemeris = self._coerce_pointing_ephemeris(pointings)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.ephemerides["topocentric"] = self._calculate_intersections(
                pointing_ephemeris
            )
        self.ephemerides["pointing"] = pointing_ephemeris

    def find_target_grid(self, raveled_meshgrid):
        if not isinstance(raveled_meshgrid, pd.DataFrame):
            raise ValueError("find_target_grid() must be passed a DataFrame.")
        if len(self.ephemerides["body"]) != 1:
            warnings.warn(
                "body ephemeris has length > 1, calculating grid targets only "
                "for first entry in ephemeris"
            )
        # not really an ephemeris
        pointings = self._coerce_df_cartesian(raveled_meshgrid)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.ephemerides["topocentric"] = self._calculate_intersections(
                pointings, wide=True
            )
        self.ephemerides["pointing"] = pointings

    def _calculate_intersections(self, pointing_ephemeris, wide=False):
        # breaking these out beforehand is a performance step to avoid
        # slicing every row on very large ephemerides, which can be
        # surprisingly expensive in some cases
        pointing_rows = pointing_ephemeris[["x", "y", "z"]].values.T
        body_rows = self.ephemerides["body"][["x", "y", "z"]].values.T
        if wide is True:
            body_rows = np.tile(body_rows, len(pointing_ephemeris))
        intersections = {
            coordinate: solution(*pointing_rows, *body_rows)
            for coordinate, solution in self.solutions.items()
        }
        intersections = pd.DataFrame(intersections)
        intersections.index = pointing_ephemeris.index
        return intersections

    def transform_targets_to_body_frame(
        self, source_frame="j2000", target_frame="j2000"
    ):
        if self.ephemerides.get("topocentric") is None:
            raise ValueError(
                "Please initialize topocentric targets with find_targets() "
                "or a similar function before attempting a reference shift."
            )

        try:
            epochs_et = utc_to_et(self.ephemerides["body"]["time"])
        except ValueError:
            epochs_et = utc_to_et(
                self.ephemerides["body"]["time"].astype("datetime64")
            )
        # implicitly handling wide/grid case
        if (len(epochs_et) == 1) and (
            len(self.ephemerides["topocentric"]) != 1
        ):
            wide = True
            body_to_target_vectors = (
                self.ephemerides["topocentric"][["x", "y", "z"]]
                - self.ephemerides["body"][["x", "y", "z"]].iloc[0]
            )

        else:
            wide = False
            body_to_target_vectors = (
                self.ephemerides["topocentric"][["x", "y", "z"]]
                - self.ephemerides["body"][["x", "y", "z"]]
            )
        body_to_target_vectors[
            ["x", "y", "z", "lon", "lat"]
        ] = array_reference_shift(
            body_to_target_vectors[["x", "y", "z"]].values,
            epochs_et,
            source_frame,
            target_frame,
            wide,
        )
        self.ephemerides["bodycentric"] = body_to_target_vectors

    def make_intersection_row(self, ix, pointing_row, body_row):
        intersection = find_intersection(
            self.solutions,
            pointing_row[["x", "y", "z"]],
            body_row[["x", "y", "z"]],
        )
        intersection["ix"] = ix
        return intersection

    def _coerce_pointing_ephemeris(self, pointings):
        if isinstance(pointings, LHorizon):
            pointing_ephemeris = self._coerce_lhorizon_cartesian(pointings)
        elif isinstance(pointings, pd.DataFrame):
            pointing_ephemeris = self._coerce_df_cartesian(pointings)
        else:
            raise TypeError
        if "time" not in pointing_ephemeris.columns:
            assert len(self.ephemerides["body"].index) == len(
                pointing_ephemeris.index
            ), (
                "for find_targets(), pointing and body ephemerides must have "
                "equal lengths. "
            )

            pointing_ephemeris["time"] = self.ephemerides["body"]["time"]
        else:
            if not (
                pointing_ephemeris["time"] == self.ephemerides["body"]["time"]
            ).all():
                raise ValueError(
                    "pointings and target positions must not have mismatched "
                    "time values. "
                )
        pointing_ephemeris[["x", "y", "z"]] = hats(
            pointing_ephemeris[["x", "y", "z"]]
        ).astype(float)
        return pointing_ephemeris