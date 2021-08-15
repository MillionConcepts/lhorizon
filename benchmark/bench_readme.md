`lhorizon` is a strongly divergent fork of `astroquery.jplhorizons`.
When compared to `jplhorizons`, it offers:
* fuller coverage of many Horizons API areas
* a wide array of helper functions
* an optional targeting module that provides SPICE integration and bodycentric coordinate transformations
* a more consistent, modular, and extensible interface, and
* increased performance.

Notebooks/scripts in this directory illustrate several performance differences between 
`jplhorizons` and `lhorizon`.

[Extra files not distributed with this repository are necessary to run these benchmarks.](https://drive.google.com/file/d/1o3R7EEZt06mbqhh8sAoH6TgFsIcvAIov/)
Please grab and decompress the file at that link, creating a directory named 'samples', and place that 'samples' 
directory in this directory ('benchmark').

Additional dependencies are also necessary to run these benchmarks. See [bench-environment.yml](bench-environment.yml) 
for a minimal working `conda` environment.
