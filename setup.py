from setuptools import setup, find_packages

setup(
    name="lhorizon",
    version="1.1.1",
    description="lhorizon helps you things in the solar system",
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
