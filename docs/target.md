# Table of Contents

* [lhorizon.target](#lhorizon.target)
  * [find\_intersections](#lhorizon.target.find_intersections)
  * [array\_reference\_shift](#lhorizon.target.array_reference_shift)
  * [Targeter](#lhorizon.target.Targeter)
    * [\_\_init\_\_](#lhorizon.target.Targeter.__init__)
    * [find\_targets](#lhorizon.target.Targeter.find_targets)
    * [find\_target\_grid](#lhorizon.target.Targeter.find_target_grid)
    * [transform\_targets\_to\_body\_frame](#lhorizon.target.Targeter.transform_targets_to_body_frame)

<a name="lhorizon.target"></a>
# lhorizon.target

<a name="lhorizon.target.find_intersections"></a>
#### find\_intersections

```python
find_intersections(solutions: Mapping[Callable], ray_direction: Array, target_center: Array) -> dict
```

find intersections between ray_direction and target_center given a mapping
of functions (output of solutions.make_ray_sphere_lambdas(), for instance)

<a name="lhorizon.target.array_reference_shift"></a>
#### array\_reference\_shift

```python
array_reference_shift(positions: Array, time_series: Sequence, origin: str, destination: str, wide: bool = False)
```

using SPICE, transform an array of position vectors from origin (frame) to
destination (frame) at times in time_series. also computes spherical
representation of these coordinates. time_series must be in et (seconds
since J2000)

<a name="lhorizon.target.Targeter"></a>
## Targeter Objects

```python
class Targeter()
```

<a name="lhorizon.target.Targeter.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(target: Ephemeris, solutions: Mapping[Callable] = None, target_radius: Optional[float] = None)
```

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

<a name="lhorizon.target.Targeter.find_targets"></a>
#### find\_targets

```python
 | find_targets(pointings: Union[pd.DataFrame, LHorizon]) -> None
```

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

<a name="lhorizon.target.Targeter.find_target_grid"></a>
#### find\_target\_grid

```python
 | find_target_grid(raveled_meshgrid: pd.DataFrame) -> None
```

finds targets at a single moment in time for a grid of coordinates
expressed as an output of lhorizon_utils.make_raveled_meshgrid().
stores them in self.ephemerides["topocentric"] and the raveled meshgrid
in self.ephemerides["pointing"].

all non-time-releated caveats from Targeter.find_targets() apply.

<a name="lhorizon.target.Targeter.transform_targets_to_body_frame"></a>
#### transform\_targets\_to\_body\_frame

```python
 | transform_targets_to_body_frame(source_frame="j2000", target_frame="j2000")
```

transform targets from source_frame to body_frame. you must initialize
self.ephemerides["topocentric"] using find_targets() or
find_target_grid() before calling this function.

