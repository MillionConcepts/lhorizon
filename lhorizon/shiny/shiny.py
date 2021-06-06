import math
from functools import wraps
from typing import Union, Sequence, Callable

import astropy.time as at
import numpy as np
from numpy.linalg import norm
import spiceypy as spice

from lhorizon import LHorizon
from lhorizon.lhorizon_utils import hat


def half_angle_vector(vector_1, vector_2):
    """i.e., pbr's omega_h"""
    return hat(vector_1 + vector_2)


def clipped_function_factory(input_function, lower_bound=None, upper_bound=None):

    @wraps(input_function)
    def clipped_function(*args, **kwargs):
        result = input_function(*args, **kwargs)
        if lower_bound is not None:
            if result < lower_bound:
                return lower_bound
        if upper_bound is not None:
            if result > upper_bound:
                return upper_bound
        return result

    return clipped_function


zero_dot = clipped_function_factory(np.dot, 0)


def angle_between(vector_1, vector_2):
    return math.acos(zero_dot(hat(vector_1), hat(vector_2)))


def constant_function(*_args, **_kwargs):
    return 1


def phong_moon(
    longitudes: np.ndarray,
    latitudes: np.ndarray,
    observer_location: Union[
        int, dict
    ] = 500,  # horizons location code or dict
    illuminator_location: Union[
        int, str
    ] = 10,  # horizons location code or planetographic string
    observation_time: str = None,  # string giving observation time in utc,
    diffusivity: float = 1,
    specularity: float = 1,
    shininess: float = 2,
) -> dict:
    if observation_time is None:
        observation_time = at.Time.now()
    tdb_time = str(at.Time(observation_time).tdb)
    observer_selenocenter_query = LHorizons(
        301, epochs=tdb_time, location=observer_location
    )
    observer_sun_query = LHorizons(
        illuminator_location, epochs=tdb_time, location=observer_location
    )
    # TODO: This should be corrected for light time but it's not an enormous
    # deal
    observer_selenocenter_query.query(query_type="VECTORS")
    observer_sun_query.query(query_type="VECTORS")
    observer_selenocenter_vector = observer_selenocenter_query.table()[
        ["X", "Y", "Z"]
    ].values[0]
    observer_sun_vector = observer_sun_query.table()[["X", "Y", "Z"]].values[0]

    et_time = utc_to_et(observation_time)
    # note that since we are pretending the moon is a sphere, the position
    # vector is in the direction of the surface normal vector.
    selenographic_position_vectors = [
        spice.latrec(LUNAR_RADIUS / 1000, lon, lat)
        for lon, lat in zip(np.radians(longitudes), np.radians(latitudes))
    ]
    surface_position_vectors = [
        reference[0:3]
        for reference in array_reference_shift(
            selenographic_position_vectors,
            [et_time for _ in selenographic_position_vectors],
            "moon_pa",
            "ECLIPJ2000",
        )
    ]  # just discarding the useless latitudinal coordinates
    # todo: probably just flip the sign on these here and later
    observer_surface_vectors = [
        surface_position_vector + observer_selenocenter_vector
        for surface_position_vector in surface_position_vectors
    ]
    surface_sun_vectors = [
        observer_sun_vector - observer_surface_vector
        for observer_surface_vector in observer_surface_vectors
    ]
    unit_normal_vectors = unit_vectors(surface_position_vectors)
    unit_illumination_vectors = unit_vectors(surface_sun_vectors)
    unit_observer_vectors = unit_vectors(observer_surface_vectors)
    diffuse_coefficients = [
        np.dot(illumination_vector, normal_vector)
        for illumination_vector, normal_vector in zip(
            unit_illumination_vectors, unit_normal_vectors
        )
    ]
    reflection_vectors = [
        2 * np.dot(illumination_vector, normal_vector) * normal_vector
        - illumination_vector
        for illumination_vector, normal_vector in zip(
            unit_illumination_vectors, unit_normal_vectors
        )
    ]

    specular_illumination_values = []
    for reflection_vector, diffuse_coefficient, observer_vector in zip(
        reflection_vectors, diffuse_coefficients, unit_observer_vectors
    ):
        if diffuse_coefficient <= 0:
            specular_illumination_values.append(0)
            continue
        reflection_coefficient = np.dot(
            reflection_vector, -1 * observer_vector
        )
        if reflection_coefficient <= 0:
            specular_illumination_values.append(0)
            continue
        specular_illumination_values.append(
            specularity * reflection_coefficient ** shininess
        )
    diffuse_illumination_values = []
    for diffuse_coefficient in diffuse_coefficients:
        if diffuse_coefficient <= 0:
            diffuse_illumination_values.append(0)
        else:
            diffuse_illumination_values.append(
                diffusivity * diffuse_coefficient
            )
    return {
        "specular": specular_illumination_values,
        "diffuse": diffuse_illumination_values,
    }


def microfacet_moon(
    longitudes: np.ndarray,
    latitudes: np.ndarray,
    observer_location: Union[
        int, dict
    ] = 500,  # horizons location code or dict
    illuminator_location: Union[
        int, str
    ] = 10,  # horizons location code or planetographic string
    observation_time: str = None,  # string giving observation time in utc,
    partial_microfacet_function: Callable = constant_function
) -> list:
    if observation_time is None:
        observation_time = at.Time.now()
    tdb_time = str(at.Time(observation_time).tdb)
    observer_selenocenter_query = LHorizons(
        301, epochs=tdb_time, location=observer_location
    )
    observer_sun_query = LHorizons(
        illuminator_location, epochs=tdb_time, location=observer_location
    )
    observer_selenocenter_query.query(query_type="VECTORS")
    observer_sun_query.query(query_type="VECTORS")
    observer_selenocenter_vector = observer_selenocenter_query.table()[
        ["X", "Y", "Z"]
    ].values[0]
    observer_sun_vector = observer_sun_query.table()[["X", "Y", "Z"]].values[0]
    et_time = utc_to_et(observation_time)
    # note that since we are pretending the moon is a sphere, the position
    # vector is in the direction of the surface normal vector.
    selenographic_position_vectors = [
        spice.latrec(LUNAR_RADIUS / 1000, lon, lat)
        for lon, lat in zip(d2r(longitudes), d2r(latitudes))
    ]
    surface_position_vectors = [
        reference[0:3]
        for reference in array_reference_shift(
            selenographic_position_vectors,
            [et_time for _ in selenographic_position_vectors],
            "moon_pa",
            "ECLIPJ2000",
        )
    ]  # just discarding the useless latitudinal coordinates
    surface_observer_vectors = [
        -1 * surface_position_vector - observer_selenocenter_vector
        for surface_position_vector in surface_position_vectors
    ]
    surface_sun_vectors = [
        observer_sun_vector + surface_observer_vector
        for surface_observer_vector in surface_observer_vectors
    ]
    unit_normal_vectors = unit_vectors(surface_position_vectors)
    unit_illumination_vectors = unit_vectors(surface_sun_vectors)
    unit_observer_vectors = unit_vectors(surface_observer_vectors)
    return [
        partial_microfacet_function(normal, observer, illumination)
        for normal, observer, illumination in zip(
            unit_normal_vectors, unit_observer_vectors, unit_illumination_vectors
        )
    ]


# note that infinite tan ** 2 (theta_h) happens at grazing directions and
# should be handled differently,
# i guess, not just give a nan
def beck_spiz_distribution(normal, observer, illumination, alpha=1):
    """
    isotropic beckmann-spizzichino microfacet distribution function.
    baked-in assumption that specular reflection occurs only at
    half-angle vector between light source and observer.
    """

    theta_h = angle_between(half_angle_vector(observer, illumination), normal)
    if abs(theta_h - math.pi/2) < 1E-30:
        return 0
    numerator = math.exp(-1 * math.tan(theta_h) ** 2 / alpha ** 2)
    denominator = math.pi * alpha ** 2 * math.cos(theta_h) ** 4
    return numerator / denominator


def beck_spiz_lambda(normal, omega, alpha=1):
    """visible-to-invisible microfacet ratio function for the isotropic
    beckmann-spizzichino distribution"""
    theta = angle_between(normal, omega)
    a = 1 / (alpha * math.tan(theta))
    return (
        math.erf(a) - 1 + math.exp(-1 * a ** 2) / (a * math.sqrt(math.pi))
    ) / 2


def masking_shadowing_function(
    normal, observer, illumination, lambda_function, **lambda_kwargs
):
    return 1 / (
        1
        + lambda_function(normal, observer, **lambda_kwargs)
        + lambda_function(normal, illumination, **lambda_kwargs)
    )


def torrance_sparrow_brdf(
    normal,
    observer,
    illumination,
    distribution_function,
    lambda_function,
    fresnel_function,
    **kwargs
):
    vectors = [normal, observer, illumination]
    numerator = (
        distribution_function(*vectors, **kwargs)
        * masking_shadowing_function(*vectors, lambda_function, **kwargs)
        * fresnel_function(*vectors, **kwargs)
    )
    denominator = (
        4
        * zero_dot(hat(normal), hat(observer))
        * zero_dot(hat(normal), hat(illumination))
    )
    # return distribution_function(*vectors, **kwargs)
    if denominator == 0:
        return 0
    return numerator / denominator
