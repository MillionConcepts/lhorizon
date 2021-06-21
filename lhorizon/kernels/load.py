import os

import spiceypy as spice


def load_metakernel():
    """
    convenience wrapper for `spiceypy.furnsh()` and thus SPICE `FURNSH`.
    it's impossible to accurately 'target' paths in a flexible way inside a
    SPICE metakernel; this sweeps directory structure messiness under the rug.
    """
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    spice.furnsh("lhorizon_metakernel.tm")
    os.chdir(cwd)


# TODO: or we could write an extended furnsh() replacement that dynamically
#   assembled a metakernel. maybe.
