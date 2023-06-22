import logging
log = logging.getLogger('onegov.search')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.search.mixins import Searchable, ORMSearchable, SearchableContent
from onegov.search.dsl import Search
from onegov.search.integration import ElasticsearchApp
# from onegov.search.integration import PostgresqlSearchApp
from onegov.search.errors import SearchOfflineError

__all__ = [
    'ElasticsearchApp',
    # 'PostgresqlSearchApp',
    'ORMSearchable',
    'Search',
    'Searchable',
    'SearchableContent',
    'SearchOfflineError',
]
