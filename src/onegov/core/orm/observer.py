from __future__ import annotations

import sqlalchemy_utils.observer
from dectate.tool import resolve_dotted_name
from functools import wraps
from sqlalchemy.event import contains, listen, remove


from typing import Any, ClassVar, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.framework import Framework
    from sqlalchemy.orm import Mapper

    _F = TypeVar('_F', bound=Callable[..., Any])


MISSING = object()


class ScopedPropertyObserver(sqlalchemy_utils.observer.PropertyObserver):
    """
    This subclass of `PropertyObserver` doesn't register itself globally.

    Having all observers listen for each application is both wasteful and
    can lead to bugs if some tables only exist for some applications.

    We should never use the base class, since that will always cause all
    observers to trigger regardless of whether we used the scoped observer
    or not.
    """

    _global_observer: ClassVar[ScopedPropertyObserver]
    _scoped_observers: ClassVar[dict[str, ScopedPropertyObserver]] = {}

    def __new__(cls, dotted_name: str | None) -> ScopedPropertyObserver:  # noqa: PYI034

        # special case global scope
        if dotted_name is None:
            if not hasattr(cls, '_global_observer'):
                cls._global_observer = super().__new__(cls)
            return cls._global_observer

        if dotted_name not in cls._scoped_observers:
            cls._scoped_observers[dotted_name] = super().__new__(cls)
        return cls._scoped_observers[dotted_name]

    def __init__(self, dotted_name: str | None) -> None:
        """
        In order to get ourselves out of circular dependency hell we
        accept a dotted_name in place of the application class that
        defines the scope of the observer.

        The dotted_name will be resolved once enter_scope is called.
        """
        super().__init__()
        self.dotted_name = dotted_name
        if dotted_name is None:
            # global scope is always active
            self.activate()

    @property
    def scope(self) -> type[object]:
        assert self.dotted_name is not None
        application_cls = resolve_dotted_name(self.dotted_name)
        assert isinstance(application_cls, type)

        # reify this so we only look the scope up once
        self.__dict__['scope'] = application_cls
        return application_cls

    def register_listeners(self) -> None:
        for cls, event, func in self.listener_args:
            # don't register before_flush
            if event == 'before_flush':
                continue

            if not contains(cls, event, func):
                listen(cls, event, func)

    def activate(self) -> None:
        for cls, event, func in self.listener_args:
            # only register before_flush
            if event != 'before_flush':
                continue

            if not contains(cls, event, func):
                listen(cls, event, func)

    def deactivate(self) -> None:
        for cls, event, func in self.listener_args:
            # only deregister before_flush
            if event != 'before_flush':
                continue

            if contains(cls, event, func):
                remove(cls, event, func)

    def update_generator_registry(
        self,
        mapper: Mapper[Any],
        class_: type[Any]
    ) -> None:

        for generator in class_.__dict__.values():
            if getattr(
                generator,
                '__observes_scope__',
                MISSING
            ) == self.dotted_name:

                self.generator_registry[class_].append(
                    generator
                )

    @classmethod
    def enter_scope(cls, application: Framework) -> None:
        for observer in cls._scoped_observers.values():
            if isinstance(application, observer.scope):
                observer.activate()
            else:
                observer.deactivate()

    @classmethod
    def enter_class_scope(cls, application_cls: type[Framework]) -> None:
        for observer in cls._scoped_observers.values():
            if issubclass(application_cls, observer.scope):
                observer.activate()
            else:
                observer.deactivate()

    def __repr__(self) -> str:
        return '<ScopedPropertyObserver>'


def observes(
    *paths: str,
    scope: str | None = None
) -> Callable[[_F], _F]:

    observer = ScopedPropertyObserver(scope)
    observer.register_listeners()

    def decorator(func: _F) -> _F:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            return func(self, *args, **kwargs)

        wrapper.__observes__ = paths  # type:ignore[attr-defined]
        wrapper.__observes_scope__ = scope  # type:ignore[attr-defined]
        return wrapper  # type:ignore[return-value]
    return decorator


if hasattr(sqlalchemy_utils.observer, 'observer'):
    # make sure this observer doesn't mess with us
    # remove_listeners doesn't check if the listeners are there
    # so we call register_listeners to make sure we can remove them
    sqlalchemy_utils.observer.observer.register_listeners()
    sqlalchemy_utils.observer.observer.remove_listeners()
    delattr(sqlalchemy_utils.observer, 'observer')
