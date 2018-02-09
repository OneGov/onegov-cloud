import logging
import warnings

log = logging.getLogger('onegov.core')  # noqa
log.addHandler(logging.NullHandler())  # noqa

ignored_warnings = (
    # we will keep using psycopg2 instead of psycogp2-binary
    "The psycopg2 wheel package will be renamed from release 2.8",
)

for message in ignored_warnings:
    warnings.filterwarnings("ignore", message=message)

from onegov.core.framework import Framework # noqa
from onegov.core.filestorage import get_filestorage_file # noqa

# include the filters module so they get picked up by webassets
from onegov.core import filters  # noqa

__all__ = ['Framework', 'log']
