# The current version set by do/release. Do not edit by hand!
#
# Note that during development this version information is stale. That is to
# say, we do not have a separate development version - the use for this
# version is to create release-dependent urls, artifacts and caches. During
# development these dependencies do not need to be updated in lock-step.
#
__version__ = '2019.4'

import logging
import warnings

log = logging.getLogger('onegov.core')  # noqa
log.addHandler(logging.NullHandler())  # noqa

ignored_warnings = (
    # we will keep using psycopg2 instead of psycogp2-binary
    "The psycopg2 wheel package will be renamed from release 2.8",

    # SQLAlchemy-Utils installs its own array_agg function, which seems fine
    "The GenericFunction 'array_agg' is already registered"
)

for message in ignored_warnings:
    warnings.filterwarnings("ignore", message=message)

from onegov.core.framework import Framework # noqa
from onegov.core.filestorage import get_filestorage_file # noqa

# include the filters module so they get picked up by webassets
from onegov.core import filters  # noqa

__all__ = ['Framework', 'log']
