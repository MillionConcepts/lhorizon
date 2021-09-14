from setuptools import setup, find_packages
long_description = "lhorizon helps you find things in the Solar System. It is built around a thick Python wrapper for the Jet Propulsion Laboratory (JPL) Horizons service. Horizons, provided by JPL's Solar System Dynamics Group (SSD), is one of the only sources in the world that offers no-assembly-required high-precision data on the relative positions and velocities of almost every known body in the Solar System. lhorizon offers tools to query Horizons for data, parse its responses into useful Python objects, and smoothly incorporate them into bulk calculation and transformation workflows."
setup(
    name="lhorizon",
    version="1.1.2",
    description="lhorizon helps you find things in the solar system",
    long_description=long_description,
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
        "benchmarks": ["memory-profiler", "pympler", "astroquery"]
    },
    package_data={
        "": ["kernels/*.*", "tests/data/*.*"],
    },
)
