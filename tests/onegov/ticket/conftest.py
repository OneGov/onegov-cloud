import pytest
import onegov.ticket


@pytest.yield_fixture
def handlers():
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = {}
