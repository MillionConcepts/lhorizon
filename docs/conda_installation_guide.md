# `lhorizon` installation guide

## step 1: install conda

*If you already have Anaconda or Miniconda installed on your computer, you can
skip this step. If it's very old or not working well, you should uninstall it first.
We **definitely** don't recommend installing multiple versions of `conda`
unless you have a strong and specific reason to do so.*

[You can get `conda` here as part of the Miniconda distribution of Python](https://docs.conda.io/projects/continuumio-conda/en/latest/user-guide/install/index.html).
Download the appropriate version of the installer for your operating system and 
processor architecture (in most cases 64-bit) and follow the instructions on that 
website to set up your environment. Make sure you download Miniconda3, not 
Miniconda2. `lhorizon` is not compatible with Python 2.

## step 2: create conda environment

Now that you have `conda` installed, you can set up a Python environment
to use `lhorizon`. Open a terminal window: Anaconda Prompt on Windows, Terminal on macOS,
or your console emulator of choice on Linux. Navigate to the directory where
you put the repository and run the command:

`conda env create -f environment.yml`

Say yes at the prompts and let the installation finish. Then run:

`conda env list`

You should see `lhorizon` in the list of environments. Now run:

`conda activate lhorizon`

and you will be in a Python environment that contains all the packages
`lhorizon` needs. 

**Important:** now that you've created this environment, you should 
always have it active whenever you work with `lhorizon`.

If you can't activate the environment, see 'common gotchas' below.

## step 3: install `lhorizon` as a site package

With the "lhorizon" environment active, run `python setup.py install`.
Now `lhorizon` can be imported in any code you run using the "lhorizon"
environment.

Now go try the example Jupyter Notebooks by running `jupyter notebook` and
navigating to the /lhorizon/examples directory!

## common gotchas

* If you get error messages when running a Notebook or other `lhorizon` code, 
  make sure you have activated the`conda` environment by running `conda activate lhorizon`.
* If you use multiple shells on macOS or Linux, `conda` will only 
  automatically set up the one it detects as your system default. If you can't 
  activate the environment, check a different shell or explicitly run `conda init NAME_OF_YOUR_SHELL`
* If you've already got an installed version of `conda` on your system, installing 
  an additional version without uninstalling the old one may make environment setup very 
  challenging. We do not recommend installing multiple versions of `conda` at once 
  unless you really need to.