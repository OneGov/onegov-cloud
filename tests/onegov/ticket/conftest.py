import pytest
import onegov.ticket


@pytest.fixture
def handlers():
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = {}
