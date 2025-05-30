from __future__ import annotations

import asyncio
from aiohttp import ClientSession, ClientTimeout


from typing import overload, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence
    from typing import Protocol, TypeVar, TypeAlias

    class HasUrl(Protocol):
        url: str

    _T = TypeVar('_T')
    UrlType: TypeAlias = str | HasUrl
    _UrlTypeT = TypeVar('_UrlTypeT', bound=UrlType)
    ErrFunc: TypeAlias = Callable[[_UrlTypeT, Exception], Any]
    HandleExceptionType: TypeAlias = (
        ErrFunc[_UrlTypeT] | Sequence[ErrFunc[_UrlTypeT]])
    FetchCallback: TypeAlias = Callable[[_UrlTypeT, Any], _T]
    FetchFunc: TypeAlias = Callable[[
        UrlType,
        ClientSession,
        str,
        FetchCallback[_UrlTypeT, _T],
        ErrFunc[_UrlTypeT] | None
    ], Awaitable[_T]]


def raise_by_default(url: Any, exception: Exception) -> None:
    raise exception


def default_callback(url: UrlType, response: Any) -> tuple[UrlType, Any]:
    return url, response


@overload
async def fetch(
    url: UrlType,
    session: ClientSession,
    response_attr: str = 'json',
    callback: FetchCallback[UrlType, tuple[UrlType, Any]] = default_callback,
    handle_exceptions: ErrFunc[UrlType] | None = raise_by_default
) -> tuple[UrlType, Any]: ...


@overload
async def fetch(
    url: UrlType,
    session: ClientSession,
    response_attr: str,
    callback: FetchCallback[_UrlTypeT, _T],
    handle_exceptions: ErrFunc[_UrlTypeT] | None = raise_by_default
) -> _T: ...


@overload
async def fetch(
    url: UrlType,
    session: ClientSession,
    response_attr: str = 'json',
    *,
    callback: FetchCallback[_UrlTypeT, _T],
    handle_exceptions: ErrFunc[_UrlTypeT] | None = raise_by_default
) -> _T: ...


async def fetch(
    url: UrlType,
    session: ClientSession,
    response_attr: str = 'json',
    callback: FetchCallback[Any, Any] = default_callback,
    handle_exceptions: ErrFunc[Any] | None = raise_by_default
) -> Any:
    """
    Asynchronous get request. Pass handle_exceptions in order to get your
    desired error handling.

    :param callback: callback to handle the response.
    :param url: object that has an attribute url or a string
    :param session: instance of aiohttp.ClientSession()
    :param response_attr: valid, (awaitable) attribute for response object
    :param handle_exceptions: optional callback for handling exceptions
    :return: response_attr or handled exception return for each url
    """
    try:
        url_ = url if isinstance(url, str) else url.url
        async with session.get(url_) as response:
            response_attr = response_attr or 'json'
            attr = getattr(response, response_attr)
            if callable(attr):
                response_called = await attr()
                return callback(url, response_called)
            else:
                # eg. status
                return callback(url, attr)
    except Exception as e:
        if not handle_exceptions:
            raise
        return handle_exceptions(url, e)


@overload
async def fetch_many(
    urls: Sequence[UrlType],
    response_attr: str = 'json',
    fetch_func: FetchFunc[UrlType, tuple[UrlType, Any]] = fetch,
    callback: FetchCallback[UrlType, tuple[UrlType, Any]] = default_callback,
    handle_exceptions: HandleExceptionType[UrlType] = raise_by_default,
    timeout: ClientTimeout | None = None  # noqa: ASYNC109
) -> list[tuple[UrlType, Any]]: ...


@overload
async def fetch_many(
    urls: Sequence[UrlType],
    response_attr: str,
    fetch_func: FetchFunc[_UrlTypeT, _T],
    callback: FetchCallback[_UrlTypeT, _T],
    handle_exceptions: HandleExceptionType[_UrlTypeT] = raise_by_default,
    timeout: ClientTimeout | None = None  # noqa: ASYNC109
) -> list[_T]: ...


@overload
async def fetch_many(
    urls: Sequence[UrlType],
    response_attr: str = 'json',
    fetch_func: FetchFunc[_UrlTypeT, _T] = fetch,
    *,
    callback: FetchCallback[_UrlTypeT, _T],
    handle_exceptions: HandleExceptionType[_UrlTypeT] = raise_by_default,
    timeout: ClientTimeout | None = None  # noqa: ASYNC109
) -> list[_T]: ...


async def fetch_many(
    urls: Sequence[UrlType],
    response_attr: str = 'json',
    fetch_func: FetchFunc[Any, Any] = fetch,
    callback: FetchCallback[Any, Any] = default_callback,
    handle_exceptions: HandleExceptionType[Any] = raise_by_default,
    timeout: ClientTimeout | None = None  # noqa: ASYNC109
) -> list[Any]:
    """ Registers a task per url using the coroutine fetch_func with correct
    signature. """
    timeout = timeout or ClientTimeout()
    async with ClientSession(timeout=timeout) as session:

        def exception_handler(ix: int) -> Any:
            if callable(handle_exceptions):
                return handle_exceptions
            return handle_exceptions[ix]

        return await asyncio.gather(*(
            fetch_func(
                url,
                session,
                response_attr,
                callback,
                exception_handler(ix)
            )
            for ix, url in enumerate(urls)))


@overload
def async_aiohttp_get_all(
    urls: Sequence[UrlType],
    response_attr: str = 'json',
    callback: FetchCallback[UrlType, tuple[UrlType, Any]] = default_callback,
    handle_exceptions: HandleExceptionType[UrlType] = raise_by_default,
    timeout: ClientTimeout | None = None
) -> list[tuple[UrlType, Any]]: ...


@overload
def async_aiohttp_get_all(
    urls: Sequence[UrlType],
    response_attr: str,
    callback: FetchCallback[_UrlTypeT, _T],
    handle_exceptions: HandleExceptionType[_UrlTypeT] = raise_by_default,
    timeout: ClientTimeout | None = None
) -> list[_T]: ...


@overload
def async_aiohttp_get_all(
    urls: Sequence[UrlType],
    response_attr: str = 'json',
    *,
    callback: FetchCallback[_UrlTypeT, _T],
    handle_exceptions: HandleExceptionType[_UrlTypeT] = raise_by_default,
    timeout: ClientTimeout | None = None
) -> list[_T]: ...


def async_aiohttp_get_all(
    urls: Sequence[_UrlTypeT],
    response_attr: str = 'json',
    callback: FetchCallback[Any, Any] = default_callback,
    handle_exceptions: HandleExceptionType[Any] = raise_by_default,
    timeout: ClientTimeout | None = None
) -> list[Any]:
    """ Performs asynchronous get requests.

    Example only checking the status without awaiting content:
        result = async_aiohttp_get_all(test_urls, response_attr='status')

    Other valid response attributes are 'json' and 'text', which are awaited.

    If the callable of the exception handler function returns, it will be
    part of the returned results. """

    return asyncio.run(
        fetch_many(
            urls,
            response_attr=response_attr,
            callback=callback,
            handle_exceptions=handle_exceptions,
            timeout=timeout or ClientTimeout()
        )
    )
