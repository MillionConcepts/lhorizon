from collections.abc import Callable, Mapping
from typing import Optional, Union
import warnings

import numpy as np
import pandas as pd

from lhorizon import LHorizon
from lhorizon._type_aliases import Ephemeris
from lhorizon.lhorizon_utils import sph2cart, hats, time_series_to_et
from lhorizon.solutions import make_ray_sphere_lambdas
from lhorizon.targeter_utils import array_reference_shift


class Targeter:
    def __init__(
        self,
        target: Ephemeris,
        solutions: Mapping[str, Callable] = None,
        target_radius: Optional[float] = None,
    ):
        """
        target: LHorizon instance or dataframe; if a dataframe, must
            have columns named 'ra, dec, dist', 'az, alt, dist', or 'x, y, z'
            if the LHorizon instance is an OBSERVER query, uses ra_app_icrf
            and dec_app_icrf, if VECTORS, uses x/y/z

        solutions: mapping of functions that each accept six args -- x1, y1,
            z1, x2, y2, z2 -- and return at least x, y, z position of an
            "intersection" (however defined). for compatibility with other
            functions in this module, should return NaN values for cases in
            which no intersection is found. if this parameter is not passed,
            generates ray-sphere solutions from the passed target radius.

        target_radius: used only if no intersection solutions are
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
    def _coerce_df_cartesian(target: pd.DataFrame) -> pd.DataFrame:
        """
        attempt to produce a dataframe in cartesian coordinates from any
        passed dataframe, inferring the character of spherical coordinates
        from column names. generally should not be called directly.
        """
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
    def _check_solution_arguments(
        solutions: Optional[Mapping[Callable]], target_radius: Optional[float]
    ):
        """
        make ray-sphere lambdas if no solutions are passed, or raise an error,
        or accept solutions.
        """
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
    def _coerce_lhorizon_cartesian(target: LHorizon) -> pd.DataFrame:
        """produce a DataFrame of cartesian coordinates from a LHorizon"""
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

    def find_targets(self, pointings: Union[pd.DataFrame, LHorizon]) -> None:
        """
        find targets using pointing vectors in a passed dataframe or lhorizon.
        time series must match time series in body ephemeris. stores passed
        pointings in self.ephemerides['pointing'] and solutions in
        self.ephemerides['topocentric']

        note that target center vectors and pointing vectors must be in the
        same frame of reference or downstream results will be silly.

        if you pass it a set of pointings without a time field, it will assume
        that their time field is identical to the time field of
        self.ephemerides["body"].

        unless you do something extremely fancy in the solver,
        the intersections will be 'geometric' quantities and thus reintroduce
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

    def find_target_grid(self, raveled_meshgrid: pd.DataFrame) -> None:
        """
        finds targets at a single moment in time for a grid of coordinates
        expressed as an output of lhorizon_utils.make_raveled_meshgrid().
        stores them in self.ephemerides["topocentric"] and the raveled meshgrid
        in self.ephemerides["pointing"].

        all non-time-releated caveats from Targeter.find_targets() apply.
        """
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
        """
        calculate intersections. called by target-finding functions. should
        not be called directly
        """
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
        """
        transform targets from source_frame to body_frame. you must initialize
        self.ephemerides["topocentric"] using find_targets() or
        find_target_grid() before calling this function.
        """
        if self.ephemerides.get("topocentric") is None:
            raise ValueError(
                "Please initialize topocentric targets with find_targets() "
                "or a similar function before attempting a reference shift."
            )
        epochs_et = time_series_to_et(self.ephemerides["body"]["time"])
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

    def _coerce_pointing_ephemeris(
        self, pointings: Union[pd.DataFrame, LHorizon]
    ):
        """
        coerce a pointing ephemeris to a tractable format. should not be
        called directly.
        """
        if isinstance(pointings, LHorizon):
            pointing_ephemeris = self._coerce_lhorizon_cartesian(pointings)
        elif isinstance(pointings, pd.DataFrame):
            pointing_ephemeris = self._coerce_df_cartesian(pointings)
        else:
            raise TypeError
        assert len(self.ephemerides["body"].index) == len(
                pointing_ephemeris.index
            ), (
                "for find_targets(), pointing and body ephemerides must have "
                "equal lengths. "
            )

        if "time" not in pointing_ephemeris.columns:
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
