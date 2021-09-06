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

_all instructions assume that you are in a console at the repository root directory with a working 
installation of `conda`._

1. [Extra files not distributed with this repository are necessary to run these benchmarks.](https://drive.google.com/file/d/1o3R7EEZt06mbqhh8sAoH6TgFsIcvAIov/)
You can retrieve these files by running `curl -o samples.tar.xz "https://doc-10-c4-docs.googleusercontent.com/docs/securesc/ha0ro937gcuc7l7deffksulhg5h7mbp1/ud4g6lsmjd169r3efib020e3ns0rmbn4/1630885275000/08679527114843416328/*/1o3R7EEZt06mbqhh8sAoH6TgFsIcvAIov?e=download"`
and subsequently decompressing them with `tar -xf samples.tar.xz`. Them move them to the correct location by running 
`mv samples benchmark/samples`.

If you don't have access to `curl`, `tar`, or the xzip libraries, you can also download these files through a browser
and unzip them with a GUI program such as 7-Zip.

2. Additional dependencies are also necessary to run these benchmarks. Run `conda env create -f bench-environment.yml`
to get a minimal working `conda` env. If you'd rather not use `conda`, you can also simply inspect
[bench-environment.yml](bench-environment.yml) and install the dependencies however you'd like.

3. Activate this env by running `conda activate lh-bench` and install `lhorizon` into the env by running `pip install -e .`

4. Switch to the 'benchmark' directory and run Jupyter:
`cd benchmark`
`jupyter notebook`
Then, from the Jupyter interface, open the performance_notes.ipynb Notebook.  

You can also try the memory-profiling scripts by running `python profile_jplhorizons_memory.py` and 
`python profile_lhorizon_memory.py`.
