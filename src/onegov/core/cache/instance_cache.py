from __future__ import annotations

from functools import cached_property
from functools import lru_cache
from functools import partial
from functools import update_wrapper


from typing import overload, Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable

    _F = TypeVar('_F', bound=Callable[..., Any])


@overload
def instance_lru_cache(*, maxsize: int | None = ...) -> Callable[[_F], _F]:
    ...


@overload
def instance_lru_cache(method: _F, *, maxsize: int | None = ...) -> _F: ...


def instance_lru_cache(
    method: _F | None = None,
    *,
    maxsize: int | None = 128
) -> _F | Callable[[_F], _F]:
    """ Least-recently-used cache decorator for class methods.

    The cache follows the lifetime of an object (it is stored on the object,
    not on the class) and can be used on unhashable objects.

    This is a wrapper around functools.lru_cache which prevents memory leaks
    when using LRU cache within classes.

    https://stackoverflow.com/a/71663059

    """

    def decorator(wrapped: _F) -> _F:
        def wrapper(self: Any) -> Any:
            return lru_cache(maxsize=maxsize)(
                update_wrapper(partial(wrapped, self), wrapped)
            )

        # NOTE: we are doing some oddball stuff here that the type
        #       checker will have trouble to understand, so we just
        #       pretend we returned a regular decorator, rather than
        #       a cached_property that contains a decorator
        return cached_property(wrapper)  # type:ignore[return-value]

    return decorator if method is None else decorator(method)
