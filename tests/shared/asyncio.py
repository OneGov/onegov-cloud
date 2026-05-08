from __future__ import annotations

from asyncio import run
from functools import wraps
from threading import Thread


from typing import overload, Any, ParamSpec, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    _P = ParamSpec('_P')

@overload
def run_in_separate_thread(*, timeout: float) -> Callable[
    [Callable[_P, Coroutine[None, Any, Any]]],
    Callable[_P, None]
]: ...

@overload
def run_in_separate_thread[**P](
    coro: Callable[P, Coroutine[None, Any, Any]],
    *,
    timeout: float = 30
) -> Callable[P, None]: ...


def run_in_separate_thread[**P](
    coro: Callable[P, Coroutine[None, Any, Any]] | None = None,
    *,
    timeout: float = 30
) -> Any:
    """
    This decorator lets us run async tests in a separate thread.

    Which is required as soon as playwright's synchronous test runner
    messes with the asyncio loop in the main thread.

    Longer running tests will require a longer timeout in order to
    not get too flaky.
    """

    def decorator(
        coro: Callable[P, Coroutine[None, Any, Any]]
    ) -> Callable[P, None]:
        @wraps(coro)
        def run_test(*args: P.args, **kwargs: P.kwargs) -> None:
            errors: list[BaseException] = []

            def run_in_thread() -> None:
                try:
                    run(coro(*args, **kwargs))
                except BaseException as exc:
                    errors.append(exc)

            t = Thread(target=run_in_thread, daemon=True)
            t.start()
            t.join(timeout=timeout)
            if errors:
                raise errors[0]
        return run_test

    return decorator if coro is None else decorator(coro)
