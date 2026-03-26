from __future__ import annotations

import asyncio
from aiohttp import ClientSession, ClientTimeout


from typing import overload, Any, Never, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence
    from typing import Protocol

    class HasUrl(Protocol):
        url: str

    type UrlType = str | HasUrl
    type UrlAndResult = tuple[UrlType, Any]
    type ErrFunc[
        UrlTypeT: UrlType = UrlType,
        RT = UrlAndResult
    ] = Callable[[UrlTypeT, Exception], RT]
    type HandleExceptionType[
        UrlTypeT: UrlType = UrlType,
        RT = UrlAndResult
    ] = ErrFunc[UrlTypeT, RT] | Sequence[ErrFunc[UrlTypeT, RT]]
    type FetchCallback[
        UrlTypeT: UrlType = UrlType,
        RT = UrlAndResult
    ] = Callable[[UrlTypeT, Any], RT]
    type FetchFunc[
        UrlTypeT: UrlType = UrlType,
        RT = UrlAndResult
    ] = Callable[[
        UrlType,
        ClientSession,
        str,
        FetchCallback[UrlTypeT, RT],
        ErrFunc[UrlTypeT, RT] | None
    ], Awaitable[RT]]


def raise_by_default(url: Any, exception: Exception) -> Never:
    raise exception


def default_callback(url: UrlType, response: Any) -> tuple[UrlType, Any]:
    return url, response


@overload
async def fetch(
    url: UrlType,
    session: ClientSession,
    response_attr: str = 'json',
    callback: FetchCallback = default_callback,
    handle_exceptions: ErrFunc | None = raise_by_default
) -> UrlAndResult: ...


@overload
async def fetch[T, UrlTypeT: UrlType = UrlType](
    url: UrlType,
    session: ClientSession,
    response_attr: str,
    callback: FetchCallback[UrlTypeT, T],
    handle_exceptions: ErrFunc[UrlTypeT, T] | None = raise_by_default
) -> T: ...


@overload
async def fetch[T, UrlTypeT: UrlType = UrlType](
    url: UrlType,
    session: ClientSession,
    response_attr: str = 'json',
    *,
    callback: FetchCallback[UrlTypeT, T],
    handle_exceptions: ErrFunc[UrlTypeT, T] | None = raise_by_default
) -> T: ...


async def fetch(
    url: UrlType,
    session: ClientSession,
    response_attr: str = 'json',
    callback: FetchCallback[Any, Any] = default_callback,
    handle_exceptions: ErrFunc[Any, Any] | None = raise_by_default
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
    fetch_func: FetchFunc = fetch,
    callback: FetchCallback = default_callback,
    handle_exceptions: HandleExceptionType = raise_by_default,
    timeout: ClientTimeout | None = None  # noqa: ASYNC109
) -> list[UrlAndResult]: ...


@overload
async def fetch_many[T, UrlTypeT: UrlType = UrlType](
    urls: Sequence[UrlType],
    response_attr: str,
    fetch_func: FetchFunc[UrlTypeT, T],
    callback: FetchCallback[UrlTypeT, T],
    handle_exceptions: HandleExceptionType[UrlTypeT, T] = raise_by_default,
    timeout: ClientTimeout | None = None  # noqa: ASYNC109
) -> list[T]: ...


@overload
async def fetch_many[T, UrlTypeT: UrlType = UrlType](
    urls: Sequence[UrlType],
    response_attr: str = 'json',
    fetch_func: FetchFunc[UrlTypeT, T] = fetch,
    *,
    callback: FetchCallback[UrlTypeT, T],
    handle_exceptions: HandleExceptionType[UrlTypeT, T] = raise_by_default,
    timeout: ClientTimeout | None = None  # noqa: ASYNC109
) -> list[T]: ...


async def fetch_many(
    urls: Sequence[UrlType],
    response_attr: str = 'json',
    fetch_func: FetchFunc[Any, Any] = fetch,
    callback: FetchCallback[Any, Any] = default_callback,
    handle_exceptions: HandleExceptionType[Any, Any] = raise_by_default,
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
    callback: FetchCallback = default_callback,
    handle_exceptions: HandleExceptionType = raise_by_default,
    timeout: ClientTimeout | None = None
) -> list[UrlAndResult]: ...


@overload
def async_aiohttp_get_all[T, UrlTypeT: UrlType = UrlType](
    urls: Sequence[UrlType],
    response_attr: str,
    callback: FetchCallback[UrlTypeT, T],
    handle_exceptions: HandleExceptionType[UrlTypeT, T] = raise_by_default,
    timeout: ClientTimeout | None = None
) -> list[T]: ...


@overload
def async_aiohttp_get_all[T, UrlTypeT: UrlType = UrlType](
    urls: Sequence[UrlType],
    response_attr: str = 'json',
    *,
    callback: FetchCallback[UrlTypeT, T],
    handle_exceptions: HandleExceptionType[UrlTypeT, T] = raise_by_default,
    timeout: ClientTimeout | None = None
) -> list[T]: ...


def async_aiohttp_get_all[UrlTypeT: UrlType = UrlType](
    urls: Sequence[UrlTypeT],
    response_attr: str = 'json',
    callback: FetchCallback[Any, Any] = default_callback,
    handle_exceptions: HandleExceptionType[Any, Any] = raise_by_default,
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
