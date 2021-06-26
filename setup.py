from setuptools import setup, find_packages

setup(name="lhorizon", version="0.5.0a0", packages=find_packages())

setup(
    name="lhorizon",
    version="1.0.0",
    url="https://github.com/millionconcepts/lhorizon.git",
    author="Million Concepts",
    author_email="mstclair@millionconcepts.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy",
        "more-itertools",
        "sympy",
        "jupyter",
        "pytest",
        "pytest-mock",
        "requests",
        "pandas",
        "spiceypy",
    ],
    package_data={
        "": ["kernels/*.*", "tests/data/*.*"],
    },
)
