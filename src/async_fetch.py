from typing import Union, Callable, Tuple, List, Any, Sequence, NamedTuple

import aiohttp
import asyncio

ErrFunc = Callable[[str], Any]
HandleExceptionType = Union[Tuple[ErrFunc], List[ErrFunc], ErrFunc]
UrlType = Union[str, object]


def raise_by_default(url, exception):
    raise exception


async def fetch(
        url: UrlType,
        session,
        response_attr: str = 'json',
        handle_exceptions: HandleExceptionType = raise_by_default
):
    """
    Asynchronous get request. Pass handle_exceptions in order to get your
    desired error handling.

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
                return response_called
            else:
                # eg. status
                return attr
    except Exception as e:
        if not handle_exceptions:
            raise e
        return handle_exceptions(url, e)


async def fetch_many(
        loop,
        urls: Sequence[UrlType],
        response_attr: str = 'json',
        fetch_func: Callable = fetch,
        handle_exceptions: HandleExceptionType = raise_by_default
):
    """ Registers a task per url using the coroutine fetch_func with correct
        signature. """
    async with aiohttp.ClientSession() as session:

        def exception_handler(ix):
            if callable(handle_exceptions):
                return handle_exceptions
            return handle_exceptions[urls.index(ix)]

        return await asyncio.gather(*(
            loop.create_task(
                fetch_func(url, session, response_attr, exception_handler(ix))
            )
            for ix, url in enumerate(urls)))


def async_aiohttp_get_all(
        urls: Sequence[UrlType],
        response_attr: str = 'json',
        handle_exceptions: HandleExceptionType = raise_by_default
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
            handle_exceptions=handle_exceptions
        )
    )
