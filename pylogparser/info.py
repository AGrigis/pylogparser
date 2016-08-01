##########################################################################
# pylogparser - Copyright (C) AGrigis, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Current version
version_major = 0
version_minor = 1
version_micro = 0

# Expected by setup.py: string of form "X.Y.Z"
__version__ = "{0}.{1}.{2}".format(version_major, version_minor, version_micro)

# Expected by setup.py: the status of the project
CLASSIFIERS = ["Development Status :: 5 - Production/Stable",
               "Environment :: Console",
               "Environment :: X11 Applications :: Qt",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Scientific/Engineering",
               "Topic :: Utilities"]

# Project descriptions
description = """
[pylogparser] A Python project that provides common parser for log files.
It is also connected with ElasticSearch in order to centralize the data and
to provide a sophisticated RESTful API to request the data.
"""
long_description = """
[pylogparser] A Python project that provides common parser for log files.
It is also connected with ElasticSearch in order to centralize the data and
to provide a sophisticated RESTful API to request the data.
"""

# Main setup parameters
NAME = "pyLogParser"
ORGANISATION = "CEA"
MAINTAINER = "Antoine Grigis"
MAINTAINER_EMAIL = "antoine.grigis@cea.fr"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "https://github.com/AGrigis/pylogparser"
DOWNLOAD_URL = "https://github.com/AGrigis/pylogparser"
LICENSE = "CeCILL-B"
CLASSIFIERS = CLASSIFIERS
AUTHOR = "pyLogParser developers"
AUTHOR_EMAIL = "antoine.grigis@cea.fr"
PLATFORMS = "OS Independent"
ISRELEASE = True
VERSION = __version__
PROVIDES = ["pylogparser"]
REQUIRES = [
    "elasticsearch>=2.3.0",
    "python-dateutil>=1.5"
]
EXTRA_REQUIRES = {}
