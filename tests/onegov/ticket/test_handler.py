from __future__ import annotations

import pytest
from onegov.ticket import Handler
from onegov.ticket.errors import DuplicateHandlerError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ticket.handler import HandlerRegistry


def test_invalid_handler_code(handlers: HandlerRegistry) -> None:

    # it's possible for the registry to not be empty due to other tests
    count = len(handlers.registry)

    with pytest.raises(AssertionError):
        handlers.register('abc', Handler)

    with pytest.raises(AssertionError):
        handlers.register('AB', Handler)

    assert len(handlers.registry) == count


def test_register_handler(handlers: HandlerRegistry) -> None:

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
