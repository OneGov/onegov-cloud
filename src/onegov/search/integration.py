import certifi
import morepath
import ssl

from concurrent.futures import ThreadPoolExecutor
from elasticsearch import ConnectionError  # shadows a python builtin!
from elasticsearch import Elasticsearch
from elasticsearch import Transport
from elasticsearch import TransportError
from elasticsearch.connection import create_ssl_context
from more.transaction.main import transaction_tween_factory

from onegov.search import Search, log, index_log
from onegov.search.errors import SearchOfflineError
from onegov.search.indexer import Indexer, PostgresIndexer
from onegov.search.indexer import ORMEventTranslator
from onegov.search.indexer import TypeMappingRegistry
from onegov.search.utils import (searchable_sqlalchemy_models,
                                 filter_non_base_models)
from sortedcontainers import SortedSet
from sedate import utcnow
from sqlalchemy import inspect
from sqlalchemy.orm import undefer
from urllib3.exceptions import HTTPError


from typing import Any, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from datetime import datetime
    from onegov.core.orm import Base, SessionManager
    from onegov.core.request import CoreRequest
    from onegov.search.mixins import Searchable
    from sqlalchemy.orm import Session
    from webob import Response


class TolerantTransport(Transport):
    """ A transport class that is less eager to rejoin connections when there's
    a failure. Additionally logs all Elasticsearch transport errors in one
    location.

    """

    failure_time: 'datetime | None'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.failure_time = None
        self.failures = 0

    @property
    def skip_request(self) -> bool:
        """ Returns True if the request should be skipped. """

        if not self.failures:
            return False

        if not self.seconds_remaining:
            return False

        return True

    @property
    def seconds_remaining(self) -> int:
        """ Returns the seconds remaining until the next try or 0.

        For each failure we wait an additional 10s (10s, then 20s, 30s, etc),
        up to a maximum of 300s (5 minutes).
        """

        assert self.failure_time is not None
        timeout = min((self.failures * 10), 300)
        elapsed = (utcnow() - self.failure_time).total_seconds()

        return int(max(timeout - elapsed, 0))

    def perform_request(self, *args: Any, **kwargs: Any) -> Any:
        if self.skip_request:
            log.info(f'Elasticsearch down, retry in {self.seconds_remaining}s')
            raise SearchOfflineError()

        try:
            response = super().perform_request(*args, **kwargs)
        except (TransportError, HTTPError) as exception:
            # transport errors might be caused by bugs (for example, when we
            # refer to a non-existant index) -> we are only tolerant of
            # connection errors
            if (
                isinstance(exception, TransportError)
                and not isinstance(exception, ConnectionError)
                and not is_5xx_error(exception)
            ):
                raise

            self.failures += 1
            self.failure_time = utcnow()

            log.exception('Elasticsearch cluster is offline')
            raise SearchOfflineError() from exception

        else:
            self.failures = 0
            return response


def is_5xx_error(error: TransportError) -> bool:
    if error.status_code:
        return str(error.status_code).startswith('5')
    return False


class SearchApp(morepath.App):
    """ Provides elasticsearch and postgres integration for
    :class:`onegov.core.framework.Framework` based applications.

    The application must be connected to a database.

    Usage::

        from onegov.core import Framework

        class MyApp(Framework, ESIntegration):
            pass

    """

    if TYPE_CHECKING:
        # forward declare required attributes
        schema: str
        session_manager: SessionManager

        @property
        def session(self) -> 'Callable[[], Session]': ...
        @property
        def has_database_connection(self) -> bool: ...

    es_client: Elasticsearch | None

    def configure_search(self, **cfg: Any) -> None:
        """ Configures the elasticsearch client, leaving it as a property
        on the class::

            app.es_client

        The following configuration options are accepted:

        :enable_elasticsearch:
            If True, elasticsearch is enabled (defaults to True).

        :elasticsearch_hosts:
            A list of elasticsearch clusters, including username, password,
            protocol and port.

            For example: ``https://user:secret@localhost:443``

            By default the client connects to the localhost on port 9200
            (the default), and on port 19200 (the default of boxen).

            At least one host in the list of servers must be up at startup.

        :elasticsearch_may_queue_size:
            The maximum queue size reserved for documents to be indexed. This
            queue is filling up if the elasticsearch cluster cannot be reached.

            Once the queue is full, warnings are emitted.

            Defaults to 10'000

        :elasticsearch_verify_certs:
            If true, the elasticsearch client verifies the certificates of
            the ssl connection. Defaults to true. Do not disable, unless you
            are in testing!

        :elasticsearch_languages:
            The languages supported by onegov.search. Defaults to:
                - en
                - de
                - fr
        """

        # TODO: set default to False once fully switched to psql (or remove
        # es stuff entirely)
        if not cfg.get('enable_elasticsearch', True):
            self.es_client = None
            return

        self.es_hosts = cfg.get('elasticsearch_hosts', (
            'http://localhost:9200',
        ))

        self.es_verify_certs = cfg.get('elasticsearch_verify_certs', True)

        if cfg.get('elasticsearch_verify_certs', True):
            self.es_extra_params = {
                'verify_certs': True,
                'ca_certs': certifi.where()
            }
        else:
            ssl_context = create_ssl_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            self.es_extra_params = {
                'verify_certs': False,
                'ssl_context': ssl_context
            }

        self.es_configure_client(usage='default')

        if self.has_database_connection:
            max_queue_size = int(cfg.get(
                'elasticsarch_max_queue_size', '10000'))

            self.es_mappings = TypeMappingRegistry()

            for base in self.session_manager.bases:
                self.es_mappings.register_orm_base(base)

            self.es_orm_events = ORMEventTranslator(
                self.es_mappings,
                max_queue_size=max_queue_size
            )

            assert self.es_client is not None
            self.es_indexer = Indexer(
                self.es_mappings,
                self.es_orm_events.es_queue,
                self.es_client
            )
            self.psql_indexer = PostgresIndexer(
                self.es_orm_events.psql_queue,
                self.session_manager.engine,
            )

            self.session_manager.on_insert.connect(
                self.es_orm_events.on_insert)

            self.session_manager.on_update.connect(
                self.es_orm_events.on_update)

            self.session_manager.on_delete.connect(
                self.es_orm_events.on_delete)

    def es_configure_client(
        self,
        usage: Literal['default', 'reindex'] = 'default'
    ) -> None:

        usages = {
            'default': {
                'timeout': 3,
                'max_retries': 1
            },
            'reindex': {
                'timeout': 10,
                'max_retries': 3
            }
        }

        self.es_client = Elasticsearch(
            hosts=self.es_hosts,
            transport_class=TolerantTransport,
            **usages[usage],
            **self.es_extra_params
        )

    def es_search(
        self,
        languages: 'Iterable[str]' = '*',
        types: 'Iterable[str]' = '*',
        include_private: bool = False,
        explain: bool = False
    ) -> Search:
        """ Returns a search scoped to the current application, with the
        given languages, types and private documents excluded by default.

        """

        search = Search(
            session=self.session(),
            mappings=self.es_mappings,
            using=self.es_client,
            index=self.es_indices(languages, types),
            extra={'explain': explain}
        )

        if not include_private:
            search = search.filter('term', es_public=True)

        # by default, do not include any fields (this will still include
        # the id and the type, which is enough for the orm querying)
        search = search.source(excludes=['*'])

        return search

    def es_indices(
        self,
        languages: 'Iterable[str]' = '*',
        types: 'Iterable[str]' = '*'
    ) -> str:
        return self.es_indexer.ixmgr.get_external_index_names(
            schema=self.schema,
            languages=languages,
            types=types
        )

    def es_search_by_request(
        self,
        request: 'CoreRequest',
        types: 'Iterable[str]' = '*',
        explain: bool = False,
        limit_to_request_language: bool = False
    ) -> Search:
        """ Takes the current :class:`~onegov.core.request.CoreRequest` and
        returns an elastic search scoped to the current application, the
        requests language and it's access rights.

        """

        languages: Iterable[str]
        if limit_to_request_language:
            assert request.locale is not None
            languages = [request.locale.split('_')[0]]
        else:
            languages = '*'

        return self.es_search(
            languages=languages,
            types=types,
            include_private=self.es_may_use_private_search(request),
            explain=explain
        )

    def es_suggestions(
        self,
        query: str,
        languages: 'Iterable[str]' = '*',
        types: 'Iterable[str]' = '*',
        include_private: bool = False
    ) -> tuple[str, ...]:
        """ Returns suggestions for the given query. """

        if not query:
            return ()

        if include_private:
            context = ['public', 'private']
        else:
            context = ['public']

        search = self.es_search(
            languages=languages,
            types=types,
            include_private=include_private
        )

        search = search.suggest(
            name='es_suggestion',
            text=query,
            completion={
                'field': 'es_suggestion',
                'skip_duplicates': True,
                'contexts': {
                    'es_suggestion_context': context
                }
            }
        )

        result = search.execute()

        # if there's no matching index, no suggestions are returned, which
        # happens if the Elasticsearch cluster is being rebuilt
        if not hasattr(result, 'suggest'):
            return ()

        suggestions: SortedSet[str] = SortedSet()

        for suggestion in getattr(result.suggest, 'es_suggestion', []):
            for item in suggestion['options']:
                suggestions.add(item['text'].strip())

        return tuple(suggestions)

    def es_suggestions_by_request(
        self,
        request: 'CoreRequest',
        query: str,
        types: 'Iterable[str]' = '*',
        limit_to_request_language: bool = False
    ) -> tuple[str, ...]:
        """ Returns suggestions for the given query, scoped to the language
        and the login status of the given requst.

        """
        languages: Iterable[str]
        if limit_to_request_language:
            assert request.locale is not None
            languages = [request.locale.split('_')[0]]
        else:
            languages = '*'

        return self.es_suggestions(
            query,
            languages=languages,
            types=types,
            include_private=self.es_may_use_private_search(request)
        )

    def es_may_use_private_search(self, request: 'CoreRequest') -> bool:
        """ Returns True if the given request is allowed to access private
        search results. By default every logged in user has access to those.

        This method may be overwritten if this is not desired.

        """
        return request.is_logged_in

    def get_searchable_models(self) -> list[type['Searchable']]:
        return [
            model
            for base in self.session_manager.bases
            for model in searchable_sqlalchemy_models(base)
        ]

    def perform_reindex(self, fail: bool = False) -> None:
        """ Re-indexes all content.

        This is a heavy operation and should be run with consideration.

        By default, all exceptions during reindex are silently ignored.

        """
        # prevent tables get re-indexed twice
        index_done: list[str] = []
        schema = self.schema
        index_log.info(f'Indexing schema {schema}..')

        self.es_configure_client(usage='reindex')
        self.es_indexer.ixmgr.created_indices = set()

        # es delete all existing indices
        assert self.es_client is not None
        ixs = self.es_indexer.ixmgr.get_managed_indices_wildcard(schema)
        self.es_client.indices.delete(index=ixs)

        # have no queue limit for reindexing (that we're able to change
        # this here is a bit of a CPython implementation detail) - we can't
        # necessarily always rely on being able to change this property
        self.es_orm_events.es_queue.maxsize = 0
        self.es_orm_events.psql_queue.maxsize = 0

        def reindex_model(model: type['Base']) -> None:
            """ Load all database objects and index them. """
            if model.__name__ in index_done:
                return

            index_done.append(model.__name__)

            session = self.session()
            try:
                q = session.query(model).options(undefer('*'))
                i = inspect(model)

                if i.polymorphic_on is not None:
                    q = q.filter(i.polymorphic_on == i.polymorphic_identity)

                for obj in q:
                    self.es_orm_events.index(schema, obj)

            except Exception as e:
                print(f"Error psql indexing model '{model}': {e}")
            finally:
                session.invalidate()
                session.bind.dispose()

        models = (model for base in self.session_manager.bases
                  for model in searchable_sqlalchemy_models(base))
        with ThreadPoolExecutor() as executor:
            results = executor.map(
                reindex_model, (
                    model for model in filter_non_base_models(set(models)))
            )
            if fail:
                print(tuple(results))

        self.es_indexer.bulk_process()
        self.psql_indexer.bulk_process()


@SearchApp.tween_factory(over=transaction_tween_factory)
def process_indexer_tween_factory(
    app: SearchApp,
    handler: 'Callable[[CoreRequest], Response]'
) -> 'Callable[[CoreRequest], Response]':
    def process_indexer_tween(request: 'CoreRequest') -> 'Response':

        app: SearchApp = request.app  # type:ignore[assignment]

        if not app.es_client:
            return handler(request)

        result = handler(request)
        app.es_indexer.process()
        # FIXME: This should work even without the es_client although
        #        we may want to be able to toggle it on or off, just
        #        like with `enable_elasticsearch` so we don't waste
        #        CPU cycles on applications that don't use this search
        # NOTE: Since we install ourselves over the transaction tween
        #       the transaction has already been comitted at this point
        #       so we don't need to pass in the current session
        app.psql_indexer.bulk_process()
        return result

    return process_indexer_tween
