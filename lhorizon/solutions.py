"""
functionality for solving body-intersection problems. used by
`lhorizon.targeter`. currently contains only ray-sphere intersection solutions
but could also sensibly contain expressions for bodies of different shapes.
"""
from collections.abc import Callable, Sequence

import sympy as sp

# sympy symbols for ray-sphere equations
x, y, z, x0, y0, z0, mx, my, mz, d = sp.symbols(
    "x,y,z,x0,y0,z0,m_x,m_y,m_z,d", real=True
)


def ray_sphere_equations(radius: float) -> list[sp.Eq]:
    """
    generate a simple system of equations for intersections between
    a ray with origin at (0, 0, 0) and direction vector [x, y, z]
    and a sphere with radius == 'radius' and center (mx, my, mz).
    """
    x_constraint = sp.Eq(x, x0 * d)
    y_constraint = sp.Eq(y, y0 * d)
    z_constraint = sp.Eq(z, z0 * d)
    sphere_bound_constraint = sp.Eq(
        ((x - mx) ** 2 + (y - my) ** 2 + (z - mz) ** 2) ** (1 / 2), radius
    )
    return [x_constraint, y_constraint, z_constraint, sphere_bound_constraint]


def get_ray_sphere_solution(
    radius: float, farside: bool = False
) -> tuple[sp.Expr]:
    """
    produce a solution to the generalized ray-sphere equation for a body of
    radius `radius`. by default, take the nearside solution. this produces a
    tuple of sympy expressions objects, which are fairly slow to evaluate;
    unless you are planning to further manipulate them, you would probably
    rather call make_ray_sphere_lambdas().
    """
    # sp.solve() returns the nearside solution first
    selected_solution = 0
    if farside:
        selected_solution = 1
    general_solution = sp.solve(ray_sphere_equations(radius), [x, y, z, d])[
        selected_solution
    ]
    return general_solution


def lambdify_system(
    expressions: Sequence[sp.Expr],
    expression_names: Sequence[str],
    variables: Sequence[sp.Symbol],
) -> dict[str, Callable]:
    """
    returns a dict of functions that substitute the symbols in 'variables'
    into the expressions in 'expressions'. 'expression_names' serve as the
    keys of the dict.
    """
    return {
        expression_name: sp.lambdify(variables, expression, "numpy")
        for expression, expression_name in zip(expressions, expression_names)
    }


def make_ray_sphere_lambdas(
    radius: float, farside=False
) -> dict[str, Callable]:
    """
    produce a dict of functions that return solutions for the ray-sphere
    equation for a sphere of radius `radius`.
    """
    return lambdify_system(
        get_ray_sphere_solution(radius, farside),
        ["x", "y", "z", "d"],
        [x0, y0, z0, mx, my, mz],
    )
