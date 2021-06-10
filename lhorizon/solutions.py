import sympy as sp

# sympy symbols for ray-sphere equations
x, y, z, x0, y0, z0, mx, my, mz, d = sp.symbols(
    "x,y,z,x0,y0,z0,m_x,m_y,m_z,d", real=True
)


def ray_sphere_equations(radius):
    """
    simple system of equations for intersections between:
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


def get_ray_sphere_solution(radius, farside=False):
    # by default we take the nearside solution, which sp.solve()
    # returns first in the list
    selected_solution = 0
    if farside:
        selected_solution = 1
    general_solution = sp.solve(ray_sphere_equations(radius), [x, y, z, d])[
        selected_solution
    ]
    return general_solution


def make_ray_sphere_lambdas(radius, farside=False):
    return lambdify_system(
        get_ray_sphere_solution(radius, farside),
        ["x", "y", "z", "d"],
        [x0, y0, z0, mx, my, mz],
    )


def lambdify_system(expressions, expression_names, variables):
    """
    list of sympy expressions, list of strings, list of sympy symbols
        -> dict of numpy lambda functions
    returns a dict of numpy functions that substitute the symbols
    in 'variables' into the expressions in 'expressions'.
    'expression_names' serve as the keys of the dict.
    """
    return {
        expression_name: sp.lambdify(variables, expression, "numpy")
        for expression, expression_name in zip(expressions, expression_names)
    }

