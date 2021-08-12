from setuptools import setup, find_packages

setup(
    name="lhorizon",
    version="1.0.1a.2",
    description="lhorizon helps you find where things are in the solar "
    "system. It is built around a thick Python wrapper for the "
    "Jet Propulsion Laboratory (JPL) Horizons service. Horizons, "
    "provided by JPL's Solar System Dynamics Group (SSD), is the "
    "only service in the world that offers no-assembly-required "
    "high-precision geometry data for almost every known body in "
    "the solar system. lhorizon offers tools to query Horizons "
    "for data, parse its responses into useful Python objects, "
    "and smoothly incorporate them into bulk calculation and "
    "transformation workflows.",
    url="https://github.com/millionconcepts/lhorizon.git",
    author="Million Concepts",
    author_email="mstclair@millionconcepts.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy",
        "more-itertools",
        "requests",
        "pandas",
    ],
    extras_require={
        "tests": ["pytest", "pytest-mock", "pytest-cov"],
        "target": ["spiceypy", "sympy"],
        "examples": ["jupyter"],
    },
    package_data={
        "": ["kernels/*.*", "tests/data/*.*"],
    },
)
