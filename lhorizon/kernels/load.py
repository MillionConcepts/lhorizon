import os

import spiceypy as spice

def load_metakernel():
    """
    it's impossible to accurately 'target' paths in a flexible way inside a
    SPICE metakernel, so we do it here
    TODO: or we could write an extended furnsh() replacement that dynamically
     assembled a metakernel. maybe.
    """
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    spice.furnsh("lhorizon_metakernel.tm")
    os.chdir(cwd)
