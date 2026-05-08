from __future__ import annotations

import pytest
import onegov.ticket


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.ticket.handler import HandlerRegistry


@pytest.fixture(scope='function')
def handlers() -> Iterator[HandlerRegistry]:
    before = onegov.ticket.handlers.registry
    onegov.ticket.handlers.registry = {}
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = before
