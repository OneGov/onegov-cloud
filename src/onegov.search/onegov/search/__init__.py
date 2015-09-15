import logging
log = logging.getLogger('onegov.search')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.search.mixins import Searchable, ORMSearchable
from onegov.search.core import ElasticsearchApp

__all__ = ['ElasticsearchApp', 'Searchable', 'ORMSearchable']
