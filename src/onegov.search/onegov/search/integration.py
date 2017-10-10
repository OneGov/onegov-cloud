import certifi
import morepath

from elasticsearch import Elasticsearch
from more.transaction.main import transaction_tween_factory
from onegov.search import Search
from onegov.search.indexer import Indexer
from onegov.search.indexer import ORMEventTranslator
from onegov.search.indexer import TypeMappingRegistry
from onegov.search.utils import searchable_sqlalchemy_models


class ElasticsearchApp(morepath.App):
    """ Provides elasticsearch integration for
    :class:`onegov.core.framework.Framework` based applications.

    The application must be connected to a database.

    Usage::

        from onegov.core import Framework

        class MyApp(Framework, ESIntegration):
            pass

    """

    def configure_search(self, **cfg):
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

        if not cfg.get('enable_elasticsearch', True):
            self.es_client = None
            return

        hosts = cfg.get('elasticsearch_hosts', (
            'http://localhost:9200',
            'http://localhost:19200'
        ))

        max_queue_size = int(cfg.get('elasticsarch_max_queue_size', '10000'))
        verify_certs = cfg.get('elasticsearch_verify_certs', True)

        if verify_certs:
            self.es_client = Elasticsearch(
                hosts, verify_certs=True, ca_certs=certifi.where(),
                sniff_on_connection_fail=True, timeout=5
            )
        else:
            self.es_client = Elasticsearch(
                hosts, sniff_on_connection_fail=True, timeout=5
            )

        if self.has_database_connection:
            self.es_mappings = TypeMappingRegistry()

            for base in self.session_manager.bases:
                self.es_mappings.register_orm_base(base)

            self.es_orm_events = ORMEventTranslator(
                self.es_mappings,
                max_queue_size=max_queue_size
            )

            self.es_indexer = Indexer(
                self.es_mappings,
                self.es_orm_events.queue,
                es_client=self.es_client
            )

            self.session_manager.on_insert.connect(
                self.es_orm_events.on_insert)
            self.session_manager.on_update.connect(
                self.es_orm_events.on_update)
            self.session_manager.on_delete.connect(
                self.es_orm_events.on_delete)

    def es_search(self, languages='*', types='*', include_private=False,
                  explain=False):
        """ Returns a search scoped to the current application, with the
        given languages, types and private documents excluded by default.

        """

        search = Search(
            session=self.session(),
            mappings=self.es_mappings,
            using=self.es_client,
            index=self.es_indices(languages, types),
            extra=dict(explain=explain)
        )

        if not include_private:
            search = search.filter("term", es_public=True)

        # by default, do not include any fields (this will still include
        # the id and the type, which is enough for the orm querying)
        search = search.source(excludes=['*'])

        return search

    def es_indices(self, languages='*', types='*'):
        return self.es_indexer.ixmgr.get_external_index_names(
            schema=self.schema,
            languages=languages,
            types=types
        )

    def es_search_by_request(self, request, types='*', explain=False,
                             limit_to_request_language=False):
        """ Takes the current :class:`~onegov.core.request.CoreRequest` and
        returns an elastic search scoped to the current application, the
        requests language and it's access rights.

        """

        if limit_to_request_language:
            languages = [request.locale.split('_')[0]]
        else:
            languages = '*'

        return self.es_search(
            languages=languages,
            types=types,
            include_private=self.es_may_use_private_search(request),
            explain=explain
        )

    def es_suggestions(self, query, languages='*', types='*',
                       include_private=False):
        """ Returns suggestions for the given query. """

        if not query:
            return []

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
                'contexts': {
                    'es_suggestion_context': context
                }
            }
        )

        result = search.execute_suggest()

        suggestions = []

        for suggestion in getattr(result, 'es_suggestion', []):
            for item in suggestion['options']:
                suggestions.append(item['text'])

        return suggestions

    def es_suggestions_by_request(self, request, query, types='*',
                                  limit_to_request_language=False):
        """ Returns suggestions for the given query, scoped to the language
        and the login status of the given requst.

        """
        if limit_to_request_language:
            languages = [request.locale.split('_')[0]]
        else:
            languages = '*'

        return self.es_suggestions(
            query,
            languages=languages,
            types=types,
            include_private=self.es_may_use_private_search(request)
        )

    def es_may_use_private_search(self, request):
        """ Returns True if the given request is allowed to access private
        search results. By default every logged in user has access to those.

        This method may be overwritten if this is not desired.

        """
        return request.is_logged_in

    def es_perform_reindex(self):
        """ Reindexes all content.

        This is a heavy operation and should be run with consideration.

        """

        self.es_indexer.ixmgr.created_indices = set()

        # delete all existing indices for this town
        ixs = self.es_indexer.ixmgr.get_managed_indices_wildcard(self.schema)
        self.es_client.indices.delete(ixs)

        # load all database objects and index them
        session = self.session()

        for base in self.session_manager.bases:
            for model in searchable_sqlalchemy_models(base):
                for obj in session.query(model).all():
                    self.es_orm_events.index(self.schema, obj)
                    self.es_indexer.process()


@ElasticsearchApp.tween_factory(over=transaction_tween_factory)
def process_indexer_tween_factory(app, handler):
    def process_indexer_tween(request):

        if not request.app.es_client:
            return handler(request)

        result = handler(request)
        request.app.es_indexer.process()
        return result

    return process_indexer_tween
