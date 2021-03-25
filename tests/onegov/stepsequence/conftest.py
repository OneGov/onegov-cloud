import pytest
import onegov.stepsequence


@pytest.fixture(scope='function')
def sequences():
    yield onegov.stepsequence.step_sequences
    onegov.stepsequence.step_sequences.registry = {}
