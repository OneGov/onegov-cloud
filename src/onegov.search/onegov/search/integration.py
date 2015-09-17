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

        :elasticsearch_hosts:
            A list of elasticsearch clusters, including username, password,
            protocol and port.

            For example: ``https://user:secret@localhost:443``

            By default the client connects to the localhost on port 9200
            (the default), and on port 19200 (the default of boxen).

            At least one host in the list of servers must be up at startup.

        """

        hosts = cfg.get('elasticsearch_hosts', (
            'http://localhost:9200',
            'http://localhost:19200'
        ))

        max_queue_size = int(cfg.get('elasticsarch_max_queue_size', '10000'))

        self.es_client = Elasticsearch(hosts, sniff_on_start=True)

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
            index=self.es_indexer.ixmgr.get_external_index_names(
                schema=self.schema,
                languages=languages,
                types=types
            )
        )

        if not include_private:
            search = search.filter("term", es_public=True)

        return search

    def es_search_by_request(self, request, types=None):
        """ Takes the current :class:`~onegov.core.request.CoreRequest` and
        returns an elastic search scoped to the current application, the
        requests language and it's access rights.

        """

        return self.es_search(
            languages=[request.locale],
            types=types,
            include_private=request.is_logged_in
        )


@ElasticsearchApp.tween_factory(over=transaction_tween_factory)
def process_indexer_tween_factory(app, handler):
    def process_indexer_tween(request):

        result = handler(request)
        request.app.es_indexer.process()
        return result

    return process_indexer_tween
