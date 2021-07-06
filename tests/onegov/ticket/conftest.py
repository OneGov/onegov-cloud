import pytest
import onegov.ticket


@pytest.fixture(scope='function')
def handlers():
    before = onegov.ticket.handlers.registry
    onegov.ticket.handlers.registry = {}
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = before
