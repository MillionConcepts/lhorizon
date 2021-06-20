# Table of Contents

* [lhorizon.lhorizon\_utils](#lhorizon.lhorizon_utils)
  * [listify](#lhorizon.lhorizon_utils.listify)
  * [snorm](#lhorizon.lhorizon_utils.snorm)
  * [hunt\_csv](#lhorizon.lhorizon_utils.hunt_csv)
  * [dt\_to\_jd](#lhorizon.lhorizon_utils.dt_to_jd)
  * [convert\_to\_jd](#lhorizon.lhorizon_utils.convert_to_jd)
  * [numeric\_columns](#lhorizon.lhorizon_utils.numeric_columns)
  * [utc\_to\_et](#lhorizon.lhorizon_utils.utc_to_et)
  * [utc\_to\_jd](#lhorizon.lhorizon_utils.utc_to_jd)
  * [is\_it](#lhorizon.lhorizon_utils.is_it)
  * [sph2cart](#lhorizon.lhorizon_utils.sph2cart)
  * [cart2sph](#lhorizon.lhorizon_utils.cart2sph)
  * [hats](#lhorizon.lhorizon_utils.hats)
  * [make\_raveled\_meshgrid](#lhorizon.lhorizon_utils.make_raveled_meshgrid)
  * [default\_lhorizon\_session](#lhorizon.lhorizon_utils.default_lhorizon_session)

<a name="lhorizon.lhorizon_utils"></a>
# lhorizon.lhorizon\_utils

<a name="lhorizon.lhorizon_utils.listify"></a>
#### listify

```python
listify(thing: Any) -> list
```

Always a list, for things that want lists. use with care.

<a name="lhorizon.lhorizon_utils.snorm"></a>
#### snorm

```python
snorm(thing: Any, minimum: float = 0, maximum: float = 1, m0: Optional[float] = None, m1: Optional[float] = None) -> Union[list[float], float]
```

simple min-max scaler. minimum and maximum are the limits of the range of
the returned sequence. m1 and m2 are optional parameters that specify
floor and ceiling values for the input other than its actual minimum and
maximum. If a single value is passed for thing, returns a float;
otherwise, returns a sequence of floats.

<a name="lhorizon.lhorizon_utils.hunt_csv"></a>
#### hunt\_csv

```python
hunt_csv(regex: Pattern, body: str) -> list
```

finds chunk of csv in a larger string defined as regex, splits it,
and returns as list. really useful only for single lines.
worse than StringIO -> numpy or pandas csv reader in other cases.

<a name="lhorizon.lhorizon_utils.dt_to_jd"></a>
#### dt\_to\_jd

```python
dt_to_jd(time: dt.datetime) -> float
```

convert passed datetimes to julian day number (jd).
algorithm derived from Julian Date article on scienceworld.wolfram.com,
itself based on Danby, J. M., Fundamentals of Celestial Mechanics

<a name="lhorizon.lhorizon_utils.produce_jd_series"></a>
#### convert\_to\_jd

```python
produce_jd_series(epochs: Sequence[Union[str, dt.datetime, float]]) -> list[float]
```

convert passed epochs to julian day number (jd). scale is assumed to be
utc. this may of course produce very slightly spurious results for dates
in the future for which leap seconds have not yet been assigned. floats or
floatlike strings will be interpreted as jd and not modified. inputs of
mixed time formats or scales will likely produce undesired behavior.

<a name="lhorizon.lhorizon_utils.numeric_columns"></a>
#### numeric\_columns

```python
numeric_columns(data: pd.DataFrame) -> list[str]
```

return a list of all numeric columns of a DataFrame

<a name="lhorizon.lhorizon_utils.time_series_to_et"></a>
#### utc\_to\_et

```python
time_series_to_et(utc)
```

convert UTC -> 'seconds since J2000' format preferred by SPICE

<a name="lhorizon.lhorizon_utils.utc_to_jd"></a>
#### utc\_to\_jd

```python
utc_to_jd(utc)
```

convert UTC string -> jd string -- for horizons or whatever

<a name="lhorizon.lhorizon_utils.is_it"></a>
#### is\_it

```python
is_it(*types)
```

partially-evaluated predicate form of isinstance

<a name="lhorizon.lhorizon_utils.sph2cart"></a>
#### sph2cart

```python
sph2cart(lat: Union[float, Array], lon: Union[float, Array], radius: Union[float, Array] = 1, unit: str = "degrees")
```

convert spherical to cartesian coordinates. assumes input is in degrees
by default; pass unit="radians" to specify input in radians. if passed any
arraylike objects, returns a DataFrame, otherwise, returns a tuple of
values.

<a name="lhorizon.lhorizon_utils.cart2sph"></a>
#### cart2sph

```python
cart2sph(x0: Union[float, Array], y0: Union[float, Array], z0: Union[float, Array], unit: str = "degrees") -> Union[pd.DataFrame, tuple]
```

convert cartesian to spherical coordinates. returns degrees by default;
pass unit="radians" to return radians. if passed any arraylike objects,
returns a DataFrame, otherwise, returns a tuple of values.

<a name="lhorizon.lhorizon_utils.hats"></a>
#### hats

```python
hats(vectors: Union[np.ndarray, pd.DataFrame, pd.Series]) -> Union[np.ndarray, pd.DataFrame, pd.Series]
```

convert an array of passed "vectors" (row-wise-stacked sequences of
floats) to unit vectors

<a name="lhorizon.lhorizon_utils.make_raveled_meshgrid"></a>
#### make\_raveled\_meshgrid

```python
make_raveled_meshgrid(axes: Sequence[np.ndarray], axis_names: Optional[Sequence[str, int]] = None)
```

produces a flattened, indexed version of a 'meshgrid' (a cartesian
product of axes standing in for a vector space, conventionally produced
by numpy.meshgrid)

<a name="lhorizon.lhorizon_utils.default_lhorizon_session"></a>
#### default\_lhorizon\_session

```python
default_lhorizon_session() -> requests.Session
```

returns a requests.Session object with default `lhorizon` options

