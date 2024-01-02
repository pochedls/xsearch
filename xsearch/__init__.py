"""
xsearch utility for searching for CMIP data at LLNL.

"""

# imports
from .search import getGroupValues
from .search import retainDataByFacetValue
from .search import natural_sort
from .search import findPaths
from .search import getValuesForFacet
from .search import addAttribute
import os

# version
__version__ = "0.0.8"

# since this software is installed centrally and may be updated
# this section of code stores the xsearch version in a hidden
# directory (~/.xsearch/version).
# If xsearch is updated, this will alert the user.
xsearchversion = os.getenv("HOME") + '/.xsearch/version'
directory = os.path.dirname(xsearchversion)
# if version file is not present, create it
# if it is present, check it and updated it if need be
# if the versions do not match, warn the user
if not os.path.exists(directory):
    os.makedirs(directory)
    with open(xsearchversion, 'w') as f:
        f.write(__version__)
else:
    with open(xsearchversion) as f:
        lastversion = f.readline()
        if __version__ != lastversion:
            print()
            print('Note that xsearch has been updated to version ' + __version__ + '.')
            print('You were last using version ' + lastversion + '.')
            print()
            with open(xsearchversion, 'w') as f:
                f.write(__version__)
