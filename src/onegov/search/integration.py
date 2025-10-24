from __future__ import annotations

import morepath

from concurrent.futures import ThreadPoolExecutor
from functools import cached_property
from more.transaction.main import transaction_tween_factory
from onegov.search import index_log, Searchable
from onegov.search.indexer import Indexer
from onegov.search.indexer import ORMEventTranslator
from onegov.search.indexer import TypeMappingRegistry
from onegov.search.utils import (
    apply_searchable_polymorphic_filter,
    get_polymorphic_base,
    language_from_locale,
    searchable_sqlalchemy_models,
)
from sqlalchemy.orm import undefer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.orm import Base, SessionManager
    from onegov.core.request import CoreRequest
    from sqlalchemy.orm import Session
    from webob import Response


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
        def session(self) -> Callable[[], Session]: ...
        @property
        def has_database_connection(self) -> bool: ...
        @cached_property
        def locales(self) -> set[str]: ...

    def configure_search(self, **cfg: Any) -> None:
        """ Configures the postgres fulltext search integration.

        The following configuration options are accepted:

        :enable_search:
            If True, postgres fulltext search is enabled (defaults to True).
        """

        if not self.has_database_connection:
            self.fts_search_enabled = False
            return

        self.fts_search_enabled = cfg.get('enable_search', True)
        if not self.fts_search_enabled:
            return

        max_queue_size = int(cfg.get(
            'elasticsarch_max_queue_size', '20000'))

        self.fts_mappings = TypeMappingRegistry()

        for base in self.session_manager.bases:
            self.fts_mappings.register_orm_base(base)

        self.fts_orm_events = ORMEventTranslator(
            self.fts_mappings,
            max_queue_size=max_queue_size
        )

        self.fts_indexer = Indexer(
            self.fts_mappings,
            self.fts_orm_events.queue,
            self.session_manager.engine,
            self.fts_languages
        )

        self.session_manager.on_insert.connect(
            self.fts_orm_events.on_insert)

        self.session_manager.on_update.connect(
            self.fts_orm_events.on_update)

        self.session_manager.on_delete.connect(
            self.fts_orm_events.on_delete)

    def fts_may_use_private_search(self, request: CoreRequest) -> bool:
        """ Returns True if the given request is allowed to access private
        search results. By default every logged in user has access to those.

        This method may be overwritten if this is not desired.

        """
        return request.is_logged_in

    @cached_property
    def fts_languages(self) -> set[str]:
        return {
            language_from_locale(locale)
            for locale in self.locales
        } or {'simple'}

    def indexable_base_models(self) -> set[type[Searchable | Base]]:
        return {
            get_polymorphic_base(model)
            for base in self.session_manager.bases
            for model in searchable_sqlalchemy_models(base)
        }

    def perform_reindex(self, fail: bool = False) -> None:
        """ Re-indexes all content.

        This is a heavy operation and should be run with consideration.

        By default, all exceptions during reindex are silently ignored.

        """
        if not self.fts_search_enabled:
            return

        schema = self.schema
        index_log.info(f'Indexing schema {schema}..')

        # psql delete table search_index
        self.fts_indexer.delete_search_index(schema)

        # have no queue limit for reindexing (that we're able to change
        # this here is a bit of a CPython implementation detail) - we can't
        # necessarily always rely on being able to change this property
        original_queue_size = self.fts_orm_events.queue.maxsize
        self.fts_orm_events.queue.maxsize = 0

        def reindex_model(model: type[Base]) -> None:
            """ Load all database objects and index them. """
            session = self.session()
            try:
                query = session.query(model).options(undefer('*'))
                query = apply_searchable_polymorphic_filter(query, model)

                for obj in query:
                    self.fts_orm_events.index(schema, obj)

                self.fts_indexer.process()
            except Exception:
                index_log.info(
                    f"Error psql indexing model '{model.__name__}'",
                    exc_info=True
                )
            finally:
                session.invalidate()
                session.bind.dispose()

        with ThreadPoolExecutor() as executor:
            results = executor.map(reindex_model, self.indexable_base_models())
            if fail:
                index_log.info('Failed reindexing:', tuple(results))
        try:
            self.fts_indexer.process()
        finally:
            self.fts_orm_events.queue.maxsize = original_queue_size


@SearchApp.tween_factory(over=transaction_tween_factory)
def process_indexer_tween_factory(
    app: SearchApp,
    handler: Callable[[CoreRequest], Response]
) -> Callable[[CoreRequest], Response]:
    def process_indexer_tween(request: CoreRequest) -> Response:
        app: SearchApp = request.app  # type:ignore[assignment]

        if not app.fts_search_enabled:
            return handler(request)

        result = handler(request)
        app.fts_indexer.process()
        return result

    return process_indexer_tween
