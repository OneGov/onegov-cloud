import certifi
import morepath

from elasticsearch import Elasticsearch
from more.transaction.main import transaction_tween_factory
from onegov.search import Search
from onegov.search.indexer import (
    Indexer,
    ORMEventTranslator,
    TypeMappingRegistry
)


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
                hosts, verify_certs=True, ca_certs=certifi.where())
        else:
            self.es_client = Elasticsearch(hosts)

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

    def es_search(self, languages='*', types='*', include_private=False):
        """ Returns a search scoped to the current application, with the
        given languages, types and private documents excluded by default.

        """

        search = Search(
            session=self.session(),
            mappings=self.es_mappings,
            using=self.es_client,
            index=self.es_indices(languages, types)
        )

        if not include_private:
            search = search.filter("term", es_public=True)

        # by default, do not include any fields (this will still include
        # the id and the type, which is enough for the orm querying)
        search = search.fields([])

        return search

    def es_indices(self, languages='*', types='*'):
        return self.es_indexer.ixmgr.get_external_index_names(
            schema=self.schema,
            languages=languages,
            types=types
        )

    def es_search_by_request(self, request, types='*'):
        """ Takes the current :class:`~onegov.core.request.CoreRequest` and
        returns an elastic search scoped to the current application, the
        requests language and it's access rights.

        """

        return self.es_search(
            languages=[request.locale],
            types=types,
            include_private=request.is_logged_in
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

        result = self.es_client.suggest(
            index=self.es_indices(languages=languages, types=types),
            body={
                'suggestions': {
                    'text': query,
                    'completion': {
                        'field': 'es_suggestion',
                        "context": {
                            "es_public_categories": context
                        }
                    },
                }
            }
        )

        suggestions = []

        for suggestion in result.get('suggestions', []):
            for item in suggestion['options']:
                suggestions.append(item['text'])

        return suggestions

    def es_suggestions_by_request(self, request, query, types='*'):
        """ Returns suggestions for the given query, scoped to the language
        and the login status of the given requst.

        """
        return self.es_suggestions(
            query,
            languages=[request.locale],
            types=types,
            include_private=request.is_logged_in
        )


@ElasticsearchApp.tween_factory(over=transaction_tween_factory)
def process_indexer_tween_factory(app, handler):
    def process_indexer_tween(request):

        if not request.app.es_client:
            return handler(request)

        result = handler(request)
        request.app.es_indexer.process()
        return result

    return process_indexer_tween
