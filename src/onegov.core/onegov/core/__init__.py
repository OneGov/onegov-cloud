import logging
log = logging.getLogger('onegov.core')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.core.framework import Framework
from onegov.core.filestorage import get_filestorage_file # noqa

# include the filters module so they get picked up by webassets
from onegov.core import filters  # noqa

__all__ = ['Framework', 'log']
