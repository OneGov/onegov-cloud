from typing import Union, Callable, Tuple, List, Any

import aiohttp
import asyncio

ErrFunc = Callable[[str], Any]
HandleExceptionType = Union[Tuple[ErrFunc], List[ErrFunc], ErrFunc]


def raise_by_default(exception):
    raise exception


async def fetch(
        url: str,
        session,
        response_attr: str = 'json',
        handle_exceptions: HandleExceptionType = raise_by_default
):
    """
    Asynchronous get request. Pass handle_exceptions in order to get your
    desired error handling.
    """
    try:
        async with session.get(url) as response:
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
        urls: Union[list, tuple],
        response_attr: str = 'json',
        fetch_func: Callable = fetch,
        handle_exceptions: HandleExceptionType = raise_by_default
):
    """ Registers a task per url using the coroutine fetch_func with correct
    signature.



     """
    async with aiohttp.ClientSession() as session:

        def exception_handler(url):
            if callable(handle_exceptions):
                return handle_exceptions
            return handle_exceptions[urls.index(url)]

        return await asyncio.gather(*(
            loop.create_task(
                fetch_func(url, session, response_attr, exception_handler(url))
            )
            for url in urls))


def async_aiohttp_get_all(
        urls: Union[list, tuple],
        response_attr: str = 'json',
        handle_exceptions: HandleExceptionType = raise_by_default
):
    """
    Performs asynchronous get requests.

    Example only checking the status without awaiting content:
        result = async_aiohttp_get_all(test_urls, response_attr='status')

    Other valid response attributes are 'json' and 'text', which are awaited.

    If the callable of the exception handler function returns, it will be
    part of the returned results.

    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        fetch_many(
            loop, urls,
            response_attr=response_attr,
            handle_exceptions=handle_exceptions
        )
    )
