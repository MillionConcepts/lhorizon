# `lhorizon` installation guide

## step 1: install conda

*If you already have another version of `conda` installed on your computer, you can
skip this step. If it's very old or not working well, you should uninstall it first.
We **definitely** don't recommend installing multiple versions of `conda`
unless you have a strong and specific reason to do so.*

[You can get `conda` here as part of the Miniforge distribution of Python](https://github.com/conda-forge/miniforge).
Download the appropriate version of the installer for your operating system and 
processor architecture (in most cases 64-bit) and follow the instructions on that 
website to set up your environment.

## step 2: install `lhorizon` from conda-forge

Create a new conda environment and install `lhorizon` into it:
`conda create -n lhorizon lhorizon`.

If you are using a different version of `conda` rather than the Miniforge version
linked above, you may need to specify the conda-forge channel, like:
`conda create -c conda-forge -n lhorizon lhorizon`.

## step 3: use the `lhorizon` environment

Now you have a Python environment that contains `lhorizon` and all its dependencies.
 Open a terminal window: Anaconda Prompt on Windows, Terminal on macOS,
or your console emulator of choice on Linux. Navigate to the directory where
you put the repository and run the command:

`conda activate lhorizon`. Now you can download the example Notebooks from
GitHub and run them, or write whatever other code you like using `lhorizon`

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
