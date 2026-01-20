from __future__ import annotations

from markupsafe import escape, Markup
from onegov.core.orm.types import JSON, MarkupText
from sqlalchemy import type_coerce
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import ExprComparator
from sqlalchemy.orm import deferred
from sqlalchemy.orm.attributes import create_proxied_attribute
from sqlalchemy.orm.interfaces import InspectionAttrInfo
from sqlalchemy.schema import Column


from typing import overload, Any, Generic, Protocol, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from sqlalchemy.orm.attributes import QueryableAttribute
    from sqlalchemy.sql import ColumnElement
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

    if TYPE_CHECKING:
        meta: Column[dict[str, Any]]
        content: Column[dict[str, Any]]

    #: metadata associated with the form, for storing small amounts of data
    @declared_attr  # type:ignore[no-redef]
    def meta(cls) -> Column[dict[str, Any]]:
        return Column(JSON, nullable=False, default=dict)

    #: content associated with the form, for storing things like long texts
    @declared_attr  # type:ignore[no-redef]
    def content(cls) -> Column[dict[str, Any]]:
        return deferred(Column(JSON, nullable=False, default=dict))


def is_valid_default(default: object | None) -> bool:
    if default is None:
        return True

    if callable(default):
        return True

    if isinstance(default, IMMUTABLE_TYPES):
        return True

    return False


class dict_property(InspectionAttrInfo, Generic[_T]):  # noqa: N801
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
        self.custom_getter = None
        self.custom_expression = None
        self.custom_setter = None
        self.custom_deleter = None
        # compatibility with ExprComparator
        self.update_expr = None

    def __set_name__(self, owner: type[object], name: str) -> None:
        """ Sets the dictionary key, if none is provided. """

        if self.key is None:
            self.key = name

    @property
    def getter(self) -> Callable[[Callable[[Any], _T]], Self]:
        def wrapper(fn: Callable[[Any], _T]) -> Any:
            self.custom_getter = fn
            return self

        return wrapper

    @property
    def setter(self) -> Callable[[Callable[[Any, _T], None]], Self]:
        def wrapper(fn: Callable[[Any, _T], None]) -> Any:
            self.custom_setter = fn
            return self

        return wrapper

    @property
    def deleter(self) -> Callable[[Callable[[Any], None]], Self]:
        def wrapper(fn: Callable[[Any], None]) -> Any:
            self.custom_deleter = fn
            return self

        return wrapper

    @property
    def expression(
        self
    ) -> Callable[[Callable[[Any], ColumnElement[_T]]], Self]:
        def wrapper(fn: Callable[[Any], ColumnElement[_T]]) -> Any:
            self.custom_expression = fn
            return self

        return wrapper

    def _expr(self, owner: type[Any]) -> QueryableAttribute | None:
        # FIXME: We should be able to remove this Any in SQlAlchemy 2.0
        expr: Any
        if self.custom_expression is not None:
            expr = self.custom_expression(owner)
        elif self.custom_getter is None:
            column: Column[dict[str, Any]] = getattr(owner, self.attribute)
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
        else:
            return None

        # FIXME: This will need to change for SQLAlchemy 1.4/2.0
        comparator = ExprComparator(owner, expr, self)  # type:ignore[call-arg]
        proxy_attr = create_proxied_attribute(self)
        return proxy_attr(
            owner,
            self.attribute,
            self,
            comparator,
            doc=comparator.__doc__ or self.__doc__
        )

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object]
    ) -> QueryableAttribute | None: ...

    @overload
    def __get__(
        self,
        instance: object,
        owner: type[object]
    ) -> _T: ...

    def __get__(
        self,
        instance: object | None,
        owner: type[object]
    ) -> _T | QueryableAttribute | None:

        if instance is None:
            return self._expr(owner)

        # pass control wholly to the custom getter if available
        if self.custom_getter:
            return self.custom_getter(instance)

        # get the value in the dictionary
        data = getattr(instance, self.attribute, None)

        if data is not None and self.key in data:
            return data[self.key]

        # fallback to the default
        return self.default() if callable(self.default) else self.default

    def __set__(self, instance: object, value: _T) -> None:

        # create the dictionary if it does not exist yet
        if getattr(instance, self.attribute) is None:
            setattr(instance, self.attribute, {})

        # pass control to the custom setter if available
        if self.custom_setter:
            return self.custom_setter(instance, value)

        # fallback to just setting the value
        getattr(instance, self.attribute)[self.key] = value

    def __delete__(self, instance: object) -> None:

        # pass control to the custom deleter if available
        if self.custom_deleter:
            return self.custom_deleter(instance)

        # fallback to just removing the value
        del getattr(instance, self.attribute)[self.key]


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
        # FIXME: This isn't super robust, we should instead
        #        override _expr to perform the type coercion
        #        but for that we should probably refactor
        #        the entire thing a bit to make it more easily
        #        extensible
        self.custom_expression = lambda owner: type_coerce(
            getattr(owner, self.attribute)[self.key].as_string(),
            MarkupText()
        )

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object]
    ) -> QueryableAttribute | None: ...

    @overload
    def __get__(
        self,
        instance: object,
        owner: type[object]
    ) -> _MarkupT: ...

    def __get__(
        self,
        instance: object | None,
        owner: type[object]
    ) -> _MarkupT | QueryableAttribute | None:

        if instance is None:
            return self._expr(owner)

        # pass control wholly to the custom getter if available
        if self.custom_getter:
            # NOTE: It would be safer to sanitize the text, in case someone
            #       bypassed this property to insert raw unsanitized markup
            #       However, this would also add a ton of static overhead.
            #       If we decide we want the additional safety, we should
            #       use an approach like OCQMS' lazy Sanitized text type.
            return Markup(self.custom_getter(instance))  # nosec: B704

        # get the value in the dictionary
        data = getattr(instance, self.attribute, None)

        if data is not None and self.key in data:
            value = data[self.key]
            # NOTE: It would be safer to sanitize the text, in case someone
            #       bypassed this property to insert raw unsanitized markup
            #       However, this would also add a ton of static overhead.
            #       If we decide we want the additional safety, we should
            #       use an approach like OCQMS' lazy Sanitized text type.
            return None if value is None else Markup(value)  # nosec: B704

        # fallback to the default
        return self.default() if callable(self.default) else self.default

    def __set__(
        self,
        instance: object,
        value: _MarkupT | str | HasHTML
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
