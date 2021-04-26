from typing import Union, Callable, Tuple, List, Any, Sequence, Optional

import aiohttp
import asyncio

from aiohttp import ClientTimeout

UrlType = Union[str, object]
UrlsType = Union[Sequence[UrlType]]
ErrFunc = Callable[[UrlType, Any], Any]
HandleExceptionType = Union[ErrFunc, Tuple[ErrFunc], List[ErrFunc]]
FetchCallback = Callable[[UrlType, Any], Any]


def raise_by_default(url, exception):
    raise exception


def default_callback(url, response):
    return url, response


async def fetch(
        url: UrlType,
        session,
        response_attr: str = 'json',
        callback: FetchCallback = default_callback,
        handle_exceptions: HandleExceptionType = raise_by_default
):
    """
    Asynchronous get request. Pass handle_exceptions in order to get your
    desired error handling.

    :param callback: callback to handle the response.
    :param url: object that has an attribute url or a string
    :param session: instance of aiohttp.ClientSession()
    :param response_attr: valid, (awaitable) attribute for response object
    :param handle_exceptions: list of callables of same length than urls
    :return: response_attr or handled exception return for each url
    """
    try:
        url_ = url if isinstance(url, str) else getattr(url, 'url')
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
            raise e
        return handle_exceptions(url, e)


async def fetch_many(
        loop,
        urls: UrlsType,
        response_attr: str = 'json',
        fetch_func: Callable = fetch,
        callback: FetchCallback = default_callback,
        handle_exceptions: HandleExceptionType = raise_by_default,
        timeout: Optional[ClientTimeout] = None
):
    """ Registers a task per url using the coroutine fetch_func with correct
        signature. """
    async with aiohttp.ClientSession(timeout=timeout) as session:

        def exception_handler(ix):
            if callable(handle_exceptions):
                return handle_exceptions
            return handle_exceptions[ix]

        return await asyncio.gather(*(
            loop.create_task(
                fetch_func(
                    url,
                    session,
                    response_attr,
                    callback,
                    exception_handler(ix)
                )
            )
            for ix, url in enumerate(urls)))


def async_aiohttp_get_all(
        urls: UrlsType,
        response_attr: str = 'json',
        callback: FetchCallback = default_callback,
        handle_exceptions: HandleExceptionType = raise_by_default,
        timeout: Optional[ClientTimeout] = None
):
    """ Performs asynchronous get requests.

    Example only checking the status without awaiting content:
        result = async_aiohttp_get_all(test_urls, response_attr='status')

    Other valid response attributes are 'json' and 'text', which are awaited.

    If the callable of the exception handler function returns, it will be
    part of the returned results. """

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        fetch_many(
            loop, urls,
            response_attr=response_attr,
            callback=callback,
            handle_exceptions=handle_exceptions,
            timeout=timeout or ClientTimeout()
        )
    )
