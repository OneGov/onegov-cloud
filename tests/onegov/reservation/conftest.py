import pytest

from libres.context.registry import create_default_registry
from onegov.reservation import LibresIntegration
from uuid import uuid4


@pytest.fixture(scope="function")
def libres_context(session_manager):

    session_manager.set_current_schema('test_' + uuid4().hex)

    registry = create_default_registry()

    yield LibresIntegration.libres_context_from_session_manager(
        registry, session_manager
    )
