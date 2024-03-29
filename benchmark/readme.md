# `lhorizon` benchmarks

## introduction

`lhorizon` is a strongly divergent fork of `astroquery.jplhorizons`.
When compared to `jplhorizons`, it offers:
* fuller coverage of many Horizons API areas
* a wide array of helper functions
* an optional targeting module that provides SPICE integration and bodycentric coordinate transformations
* a more consistent, modular, and extensible interface, and
* increased performance.

Notebooks/scripts in this directory illustrate several performance differences between 
`jplhorizons` and `lhorizon`.

## installation

_all instructions assume that you are in a console in the `benchmarks` directory with a working installation of 
`conda`._

1. Extra files not distributed with this repository are necessary to run these benchmarks.
You can retrieve these files by running `curl -o samples.tar.xz "https://zenodo.org/record/5484287/files/samples.tar.xz"`
and subsequently decompressing them with `tar -xf samples.tar.xz`.

If you don't have access to `curl`, `tar`, or the xzip libraries, you can also download these files from Zenodo through 
a browser and unzip them with a GUI program such as 7-Zip.

2. Additional dependencies are also necessary to run these benchmarks. Run `conda env create -f bench-environment.yml`
to get a minimal working `conda` env. If you'd rather not use `conda`, you can also simply inspect
[bench-environment.yml](bench-environment.yml) and install the dependencies however you'd like.

3. Activate this env by running `conda activate lh-bench` and install `lhorizon` into the env by running
`pip install -e ../`

4. Run Jupyter: `jupyter notebook`.  Then, from the Jupyter interface, open the performance_notes.ipynb Notebook.  

You can also try the memory-profiling scripts by running `python profile_jplhorizons_memory.py` and 
`python profile_lhorizon_memory.py`.
