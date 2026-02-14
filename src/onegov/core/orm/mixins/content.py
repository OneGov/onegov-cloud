from __future__ import annotations

from markupsafe import escape, Markup
from onegov.core.orm.types import MarkupText
from sqlalchemy import type_coerce
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, Mapped


from typing import overload, Any, Protocol, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from sqlalchemy.ext.hybrid import _HybridClassLevelAccessor
    from sqlalchemy.sql.elements import ColumnElement, SQLCoreOperations
    from typing import Self

    class HasHTML(Protocol):
        def __html__(self, /) -> str: ...

    class _dict_property_factory(Protocol):  # noqa: N801

        @overload
        def __call__(
            self,
            key: str | None = None,
            default: None = None,
            value_type: None = None
        ) -> dict_property[Any | None]: ...

        @overload
        def __call__(
            self,
            key: str | None,
            default: _T | Callable[[], _T],
            value_type: None = None
        ) -> dict_property[_T]: ...

        @overload
        def __call__(
            self,
            key: str | None = None,
            *,
            default: _T | Callable[[], _T],
            value_type: None = None
        ) -> dict_property[_T]: ...

        @overload
        def __call__(
            self,
            key: str | None,
            default: None,
            *,
            value_type: type[_T]
        ) -> dict_property[_T]: ...

        @overload
        def __call__(
            self,
            key: str | None = None,
            default: None = None,
            *,
            value_type: type[_T]
        ) -> dict_property[_T]: ...

        @overload
        def __call__(
            self,
            key: str | None,
            default: _T | Callable[[], _T],
            value_type: type[_T]
        ) -> dict_property[_T]: ...

        @overload
        def __call__(
            self,
            key: str | None = None,
            *,
            default: _T | Callable[[], _T],
            value_type: type[_T]
        ) -> dict_property[_T]: ...


_T = TypeVar('_T')
_MarkupT = TypeVar('_MarkupT', Markup, Markup | None)


IMMUTABLE_TYPES = (int, float, complex, str, tuple, frozenset, bytes)


class ContentMixin:
    """ Mixin providing a meta/content JSON pair. Meta is a JSON column loaded
    with each request, content is a JSON column loaded deferred (to be shown
    only in the detail view).

    """

    #: metadata associated with the object, for storing small amounts of data
    meta: Mapped[dict[str, Any]] = mapped_column(default=dict)

    #: content associated with the object, for storing things like long texts
    content: Mapped[dict[str, Any]] = mapped_column(
        default=dict,
        deferred=True
    )


def is_valid_default(default: object | None) -> bool:
    if default is None:
        return True

    if callable(default):
        return True

    if isinstance(default, IMMUTABLE_TYPES):
        return True

    return False


class dict_property(hybrid_property[_T]):  # noqa: N801
    """ Enables access of dictionaries through properties.

    Usage::

        class Model(ContentMixin):
            access_times = dict_property('meta')

    This creates a property that accesses the meta directory with the key
    'access_times'. The key is implicitly copied from the definition.

    Another way of writing this out would be::

        class Model(ContentMixin):
            access_times = dict_property('meta', 'access_times')

    As is apparent, the 'access_times' key is duplicated in this case. Usually
    you do not need to provide the name. The exception being if you want
    the property name and the dictionary key to differ::

        class Model(ContentMixin):
            access_times = dict_property('meta', 'access')

    Here, the key in the dictionary is 'access', while the property is
    'access_times'.

    Since we often use the same kind of dictionaries we can use the builtin
    properties that are scoped to a specific dictionary::

        class Model(ContentMixin):
            access_times = meta_property()

    This is equivalent to the initial example.

    We can also create our own scoped properties as follows:

        foo_property = dict_property_factory('foo')

        class Model:

            foo = {}

            bar = foo_property()

    Here, model.bar would read model.foo['bar'].

    Dict properties are compatible with typical python properties, so the
    usual getter/setter/deleter methods are also available::

        class Model(ContentMixin):
            content = meta_property()

            @content.setter
            def set_content(self, value):
                self.meta['content'] = value
                self.meta['content_html'] = to_html_ul(value)

            @content.deleter
            def del_content(self):
                del self.meta['content']
                del self.meta['content_html']

    This also behaves like a hybrid_property in that you can use
    these properties inside select and filter statements, if you
    provider a custom getter you will also need to provide a custom
    expression, otherwise we will return an expression which retrieves
    the value from the JSON column::

        class Model(ContentMixin):
            names = meta_property(default=list)

        session.query(Model).filter(Model.names.contains('foo'))

    By default that will mean that the RHS of a comparison will also
    expect a JSONB object, but if you explicitly pass in a value_type
    or a default that is not None, then we will try to first convert
    to that type, so type coercion is a bit more flexible::

        class Model(ContentMixin):
            name = meta_property(value_type=str)

        session.query(Model.name)

    """

    is_attribute = True

    custom_getter: Callable[[Any], _T] | None
    custom_expression: Callable[[type[Any]], ColumnElement[_T]] | None
    custom_setter: Callable[[Any, _T], None] | None
    custom_deleter: Callable[[Any], None] | None

    @overload
    def __init__(
        # TODO: We probably want to change this to `dict_property[_T | None]`
        #       eventually so mypy complains about the missing LHS annotation
        self: dict_property[Any | None],
        attribute: str,
        key: str | None = None,
        default: None = None,
        value_type: None = None
    ): ...

    @overload
    def __init__(
        self: dict_property[_T],
        attribute: str,
        key: str | None,
        default: _T | Callable[[], _T],
        value_type: None = None
    ): ...

    @overload
    def __init__(
        self: dict_property[_T],
        attribute: str,
        key: str | None = None,
        *,
        default: _T | Callable[[], _T],
        value_type: None = None
    ): ...

    @overload
    def __init__(
        self: dict_property[_T],
        attribute: str,
        key: str | None,
        default: None,
        *,
        value_type: type[_T]
    ): ...

    @overload
    def __init__(
        self: dict_property[_T],
        attribute: str,
        key: str | None = None,
        default: None = None,
        *,
        value_type: type[_T]
    ): ...

    @overload
    def __init__(
        self: dict_property[_T],
        attribute: str,
        key: str | None,
        default: _T | Callable[[], _T],
        value_type: type[_T]
    ): ...

    @overload
    def __init__(
        self: dict_property[_T],
        attribute: str,
        key: str | None = None,
        *,
        default: _T | Callable[[], _T],
        value_type: type[_T]
    ): ...

    def __init__(
        self,
        attribute: str,
        key: str | None = None,
        default: Any | None = None,
        # this is for coercing the result of the json access to
        # the appropriate type, otherwise the rhs of the comparison
        # needs to be casted to
        value_type: type[Any] | None = None
    ):
        assert is_valid_default(default)
        self.attribute = attribute
        self.key = key
        self.default = default

        if value_type is None and default is not None:
            if callable(default):
                value_type = type(default())
            else:
                value_type = type(default)

        self.value_type = value_type

        super().__init__(
            fget=self._default_getter,
            fset=self._default_setter,
            fdel=self._default_deleter,
            expr=self._default_expr,
        )

    def _default_getter(self, instance: object) -> _T:
        # get the value in the dictionary
        data = getattr(instance, self.attribute, None)

        if data is not None and self.key in data:
            return data[self.key]

        # fallback to the default
        return self.default() if callable(self.default) else self.default  # type: ignore[return-value]

    def _default_setter(self, instance: object, value: _T) -> None:
        getattr(instance, self.attribute)[self.key] = value

    def _default_deleter(self, instance: object) -> None:
        del getattr(instance, self.attribute)[self.key]

    def _default_expr(self, owner: type[Any]) -> ColumnElement[_T]:
        column: ColumnElement[dict[str, Any]] = getattr(owner, self.attribute)
        expr = column[self.key]
        if self.value_type is None:
            pass
        elif issubclass(self.value_type, str):
            expr = expr.as_string()
        elif issubclass(self.value_type, bool):
            expr = expr.as_boolean()
        elif issubclass(self.value_type, float):
            expr = expr.as_float()
        elif issubclass(self.value_type, int):
            expr = expr.as_integer()
        return expr

    def __set_name__(self, owner: type[object], name: str) -> None:
        """ Sets the dictionary key, if none is provided. """

        if self.key is None:
            self.key = name

        if not hasattr(self, '__name__'):
            self.__name__ = name

    def __set__(
        self,
        instance: object,
        value: SQLCoreOperations[_T] | _T
    ) -> None:

        # create the dictionary if it does not exist yet
        if getattr(instance, self.attribute) is None:
            setattr(instance, self.attribute, {})

        super().__set__(instance, value)


class dict_markup_property(dict_property[_MarkupT]):  # noqa: N801

    @overload
    def __init__(
        self: dict_markup_property[Markup | None],
        attribute: str,
        key: str | None = None,
        default: None = None,
    ): ...

    @overload
    def __init__(
        self: dict_markup_property[Markup],
        attribute: str,
        key: str | None,
        default: Markup,
    ): ...

    @overload
    def __init__(
        self: dict_markup_property[Markup],
        attribute: str,
        key: str | None = None,
        *,
        default: Markup,
    ): ...

    def __init__(
        self,
        attribute: str,
        key: str | None = None,
        default: Markup | None = None,
    ):
        super().__init__(
            attribute,
            key,
            default,  # type:ignore[arg-type]
            Markup  # type:ignore[arg-type]
        )

    def _default_expr(self, owner: type[Any]) -> ColumnElement[_MarkupT]:
        return type_coerce(
            getattr(owner, self.attribute)[self.key].as_string(),
            MarkupText()  # type: ignore[arg-type]
        )

    @overload
    def __get__(self, instance: Any, owner: None) -> Self: ...

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object]
    ) -> _HybridClassLevelAccessor[_MarkupT]: ...

    @overload
    def __get__(self, instance: object, owner: type[object]) -> _MarkupT: ...

    def __get__(
        self,
        instance: object | None,
        owner: type[object] | None
    ) -> Self | _HybridClassLevelAccessor[_MarkupT] | _MarkupT:

        value = super().__get__(instance, owner)
        if owner is None or instance is None or value is None:
            return value  # type: ignore[return-value]

        # NOTE: It would be safer to sanitize the text, in case someone
        #       bypassed this property to insert raw unsanitized markup
        #       However, this would also add a ton of static overhead.
        #       If we decide we want the additional safety, we should
        #       use an approach like OCQMS' lazy Sanitized text type.
        return Markup(value)  # nosec: B704

    def __set__(
        self,
        instance: object,
        value: SQLCoreOperations[_MarkupT] | _MarkupT | str | HasHTML
    ) -> None:
        super().__set__(
            instance,
            # escape when setting the value
            None if value is None else escape(value)  # type:ignore[arg-type]
        )


def dict_property_factory(attribute: str) -> _dict_property_factory:
    def factory(
        key: str | None = None,
        default: Any | None = None,
        value_type: type[Any] | None = None
    ) -> dict_property[Any]:
        return dict_property(
            attribute,
            key=key,
            default=default,
            value_type=value_type
        )

    return factory


content_property = dict_property_factory('content')
data_property = dict_property_factory('data')
meta_property = dict_property_factory('meta')

# for backwards compatibility, might be removed in the future
dictionary_based_property_factory = dict_property_factory
