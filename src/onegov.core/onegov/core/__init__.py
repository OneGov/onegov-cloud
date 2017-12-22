import logging
log = logging.getLogger('onegov.core')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.core.framework import Framework
from onegov.core.filestorage import get_filestorage_file # noqa

# include the filters module so they get picked up by webassets
from onegov.core import filters  # noqa

# deprected, this will be removed in the next release
from onegov.core.custom import custom_json

__all__ = ['Framework', 'log', 'custom_json']
