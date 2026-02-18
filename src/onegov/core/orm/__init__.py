from __future__ import annotations

import psycopg2

from datetime import datetime
from markupsafe import escape, Markup
from onegov.core.orm.cache import orm_cached, request_cached
from onegov.core.orm.observer import observes
from onegov.core.orm.session_manager import SessionManager, query_schemas
from onegov.core.orm.sql import as_selectable, as_selectable_from_path
from sqlalchemy import event, inspect, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import object_session
from sqlalchemy.orm import registry
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Query
from sqlalchemy_utils import TranslationHybrid as BaseTranslationHybrid
from zope.sqlalchemy import mark_changed
from sqlalchemy.exc import InterfaceError, OperationalError
from uuid import UUID as PythonUUID

from .types import JSON
from .types import MarkupText
from .types import UTCDateTime


from typing import overload, Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping
    from sqlalchemy.ext.hybrid import hybrid_property
    from sqlalchemy.orm import Mapped
    from sqlalchemy_utils.i18n import _TranslatableColumn
    from typing import Self

_T = TypeVar('_T')


MISSING = object()

DB_CONNECTION_ERRORS = (
    OperationalError,
    InterfaceError,
    psycopg2.OperationalError,
    psycopg2.InterfaceError,
)


class ModelBase:

    #: set by :class:`onegov.core.orm.cache.OrmCacheDescriptor`, this attribute
    #: indicates if the current model was loaded from cache
    is_cached = False

    @overload
    @classmethod
    def get_polymorphic_class(cls, identity_value: str) -> type[Self]: ...

    @overload
    @classmethod
    def get_polymorphic_class(cls, identity_value: str, default: _T
                              ) -> type[Self] | _T: ...

    @classmethod
    def get_polymorphic_class(
        cls,
        identity_value: str,
        default: _T = MISSING  # type:ignore[assignment]
    ) -> type[Self] | _T:
        """ Returns the polymorphic class if it exists, given the value
        of the polymorphic identity.

        Asserts that the identity is actually found, unless a default is
        provided.

        """
        mapper = inspect(cls).polymorphic_map.get(identity_value)  # type: ignore[union-attr]

        if default is MISSING:
            assert mapper, 'No such polymorphic_identity: {}'.format(
                identity_value
            )

        return mapper and mapper.class_ or default

    @property
    def session_manager(self) -> SessionManager | None:
        # FIXME: Should we assert that there is an active SessionManager
        #        when we access this property? This would allow us not
        #        having to check that there is one everywhere, but there
        #        may some existing code that relies on this possibly
        #        returning `None`, so let's leave it for now
        return SessionManager.get_active()


#: The base for all OneGov Core ORM Models
class Base(DeclarativeBase, ModelBase):

    registry = registry(type_annotation_map={
        datetime: UTCDateTime,
        dict[str, Any]: JSON,
        Markup: MarkupText,
        PythonUUID: UUID(as_uuid=True),
        # NOTE: I'm not happy that we use Text so liberally in OneGov, for
        #       most cases String would work just fine and would be a lot
        #       faster for filtering/searching, but alas, it is what it is
        #       Migrating dozens of columns from Text to String does not
        #       sound fun, but we may tackle it eventually...
        str: Text
    })


class TranslationHybrid(BaseTranslationHybrid):
    # NOTE: This works around the fact that `MappedColumn` does not expose
    #       the column's `key` attribute in the way it exposes its `name`
    #       attribute, so we need to pass the actual column, instead of the
    #       `MappedColumn` to preserve the same API in SQLAlchemy 2.0.
    def __call__(
        self,
        attr: Mapped[Mapping[str, str]] | Mapped[Mapping[str, str] | None]
    ) -> hybrid_property[str | None]:
        return super().__call__(attr.column)  # type: ignore[union-attr]


#: A translation hybrid integrated with OneGov Core. See also:
#: http://sqlalchemy-utils.readthedocs.org/en/latest/internationalization.html
translation_hybrid = TranslationHybrid(
    current_locale=lambda:
        SessionManager.get_active().current_locale,  # type:ignore
    default_locale=lambda:
        SessionManager.get_active().default_locale,  # type:ignore
)


class TranslationMarkupHybrid(TranslationHybrid):
    """ A TranslationHybrid that stores `markupsafe.Markup`. """

    def getter_factory(
        self,
        attr: _TranslatableColumn
    ) -> Callable[[object], Markup | None]:

        original_getter = super().getter_factory(attr)

        def getter(obj: object) -> Markup | None:
            value = original_getter(obj)
            if value is self.default_value and isinstance(value, str):
                # NOTE: The default may be a plain string so we need
                #       to escape it
                return escape(self.default_value)
            # NOTE: Need to wrap in Markup, we may consider sanitizing
            #       this in the future, to guard against stored values
            #       that somehow bypassed the sanitization, but this will
            #       be expensive
            return Markup(value)  # nosec: B704

        return getter

    def setter_factory(
        self,
        attr: _TranslatableColumn
    ) -> Callable[[object, str | None], None]:

        original_setter = super().setter_factory(attr)

        def setter(obj: object, value: str | None) -> None:
            if value is not None:
                value = escape(value)
            original_setter(obj, value)

        return setter

    if TYPE_CHECKING:
        def __call__(  # type: ignore[override]
            self,
            attr: _TranslatableColumn
        ) -> hybrid_property[Markup | None]:
            pass


#: A translation markup hybrid integrated with OneGov Core.
translation_markup_hybrid = TranslationMarkupHybrid(
    current_locale=lambda:
        SessionManager.get_active().current_locale,  # type:ignore
    default_locale=lambda:
        SessionManager.get_active().default_locale,  # type:ignore
)


def find_models(
    base: type[_T],
    is_match: Callable[[type[_T]], bool]
) -> Iterator[type[_T]]:
    """ Finds the ORM models in the given ORM base class that match a filter.

    The filter is called with each class in the instance and it is supposed
    to return True if it matches.

    For example, find all SQLAlchemy models that use
    :class:`~onegov.core.orm.mixins.ContentMixin`::

        from onegov.core.orm.mixins import ContentMixin
        find_models(base, is_match=lambda cls: issubclass(cls, ContentMixin))

    """
    for cls in base.__subclasses__():
        if is_match(cls):
            yield cls

        yield from find_models(cls, is_match)


def configure_listener(
    cls: type[Base],
    key: str,
    instance: Base
) -> None:
    """ The zope.sqlalchemy transaction mechanism doesn't recognize changes to
    cached objects. The following code intercepts all object changes and marks
    the transaction as changed if there was a change to a cached object.

    """

    def mark_as_changed(obj: Base, *args: Any, **kwargs: Any) -> None:
        if obj.is_cached and (session := object_session(obj)):
            mark_changed(session)

    event.listen(instance, 'append', mark_as_changed)
    event.listen(instance, 'remove', mark_as_changed)
    event.listen(instance, 'set', mark_as_changed)
    event.listen(instance, 'init_collection', mark_as_changed)
    event.listen(instance, 'dispose_collection', mark_as_changed)


event.listen(Base, 'attribute_instrument', configure_listener)


def share_session_manager(query: Query[Any]) -> None:
    session_manager = SessionManager.get_active()

    for desc in query.column_descriptions:
        desc['type'].session_manager = session_manager  # type: ignore[union-attr]


event.listen(Query, 'before_compile', share_session_manager, retval=False)


__all__ = [
    'Base',
    'SessionManager',
    'as_selectable',
    'as_selectable_from_path',
    'translation_hybrid',
    'find_models',
    'observes',
    'orm_cached',
    'query_schemas',
    'request_cached'
]
