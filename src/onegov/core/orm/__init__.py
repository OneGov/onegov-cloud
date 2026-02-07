from __future__ import annotations

import psycopg2

from markupsafe import escape, Markup
from onegov.core.orm.cache import orm_cached, request_cached
from onegov.core.orm.observer import observes
from onegov.core.orm.session_manager import SessionManager, query_schemas
from onegov.core.orm.sql import as_selectable, as_selectable_from_path
from sqlalchemy import event, inspect
from sqlalchemy.orm import object_session
from sqlalchemy.orm import Query
from sqlalchemy_utils import TranslationHybrid
from zope.sqlalchemy import mark_changed
from sqlalchemy.exc import InterfaceError, OperationalError


from typing import overload, Any, ClassVar, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from sqlalchemy import Column
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy_utils.i18n import _TranslatableColumn
    from typing import Self
else:
    # TODO: Move this import back out
    from sqlalchemy.orm import declarative_base

_T = TypeVar('_T')


MISSING = object()

DB_CONNECTION_ERRORS = (
    OperationalError,
    InterfaceError,
    psycopg2.OperationalError,
    psycopg2.InterfaceError,
)


#: The base for all OneGov Core ORM Models
class ModelBase:

    #: set by :class:`onegov.core.orm.cache.OrmCacheDescriptor`, this attribute
    #: indicates if the current model was loaded from cache
    is_cached = False

    # FIXME: These are temporary and help mypy know that these attributes
    #        exist on the Base ORM class
    __tablename__: ClassVar[str]

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
        mapper = inspect(cls).polymorphic_map.get(identity_value)

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


Base = declarative_base(cls=ModelBase)

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
        # FIXME: In SQLAlchemy 2.0 this should return a hybrid_property
        def __call__(  # type: ignore[override]
            self,
            attr: _TranslatableColumn
        ) -> Column[Markup | None]:
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
        if obj.is_cached:
            mark_changed(object_session(obj))

    event.listen(instance, 'append', mark_as_changed)
    event.listen(instance, 'remove', mark_as_changed)
    event.listen(instance, 'set', mark_as_changed)
    event.listen(instance, 'init_collection', mark_as_changed)
    event.listen(instance, 'dispose_collection', mark_as_changed)


event.listen(ModelBase, 'attribute_instrument', configure_listener)


def share_session_manager(query: Query[Any]) -> None:
    session_manager = SessionManager.get_active()

    for desc in query.column_descriptions:
        desc['type'].session_manager = session_manager


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
