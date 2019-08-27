import pytest

from onegov.ticket import Handler
from onegov.ticket.errors import DuplicateHandlerError


def test_invalid_handler_code(handlers):

    # it's possible for the registry to not be empty due to other tests
    count = len(handlers.registry)

    with pytest.raises(AssertionError):
        handlers.register('abc', Handler)

    with pytest.raises(AssertionError):
        handlers.register('AB', Handler)

    assert len(handlers.registry) == count


def test_register_handler(handlers):

    class FooHandler(Handler):
        pass

    class BarHandler(Handler):
        pass

    handlers.register('FOO', FooHandler)
    handlers.register('BAR', BarHandler)

    assert handlers.get('FOO') == FooHandler
    assert handlers.get('BAR') == BarHandler

    with pytest.raises(DuplicateHandlerError):
        handlers.register('FOO', BarHandler)
