from __future__ import annotations

import morepath

from concurrent.futures import ThreadPoolExecutor
from functools import cached_property
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
from sqlalchemy import text
from sqlalchemy.orm import undefer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.orm import Base, SessionManager
    from onegov.core.request import CoreRequest
    from sqlalchemy.orm import Session


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

        max_queue_size = cfg.get('search_max_queue_size', 20000)

        self.fts_mappings = TypeMappingRegistry()

        for base in self.session_manager.bases:
            self.fts_mappings.register_orm_base(base)

        self.fts_indexer = Indexer(
            self.fts_mappings,
            self.fts_languages
        )

        self.fts_orm_events = ORMEventTranslator(
            self.fts_indexer,
            max_queue_size=max_queue_size
        )

        self.session_manager.on_insert.connect(
            self.fts_orm_events.on_insert)

        self.session_manager.on_update.connect(
            self.fts_orm_events.on_update)

        self.session_manager.on_delete.connect(
            self.fts_orm_events.on_delete)

        self.session_manager.on_transaction_join.connect(
            self.fts_orm_events.on_transaction_join
        )

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

    def perform_reindex(self) -> None:
        """ Re-indexes all content.

        This is a heavy operation and should be run with consideration.

        By default, all exceptions during reindex are silently ignored.

        """
        if not self.fts_search_enabled:
            return

        schema = self.schema
        session = self.session()
        self.fts_indexer.delete_search_index(session)

        def reindex_model(model: type[Base]) -> None:
            """ Load all database objects and index them. """
            session = self.session()
            try:
                query = session.query(model).options(undefer('*'))
                query = apply_searchable_polymorphic_filter(
                    query,
                    model,
                    order_by_polymorphic_identity=True
                )

                # NOTE: we bypass the normal transaction machinery for speed
                self.fts_indexer.process((
                    task
                    for obj in query
                    if (
                        task := self.fts_orm_events.index_task(schema, obj)
                    ) is not None
                ), session)
                session.execute(text('COMMIT'))

            except Exception:
                index_log.info(
                    f"Error indexing model '{model.__name__}' "
                    f"in schema {schema}",
                    exc_info=True
                )
            finally:
                session.invalidate()
                session.bind.dispose()

        with ThreadPoolExecutor() as executor:
            executor.map(reindex_model, self.indexable_base_models())

        session.invalidate()
        session.bind.dispose()
