import pytest
from depot.manager import DepotManager

from onegov.core.utils import module_path


@pytest.fixture(scope='function', autouse=True)
def depot(temporary_directory):
    DepotManager.configure('default', {
        'depot.backend': 'depot.io.local.LocalFileStorage',
        'depot.storage_path': temporary_directory
    })

    yield DepotManager.get()

    DepotManager._clear()


@pytest.fixture(scope='function')
def malicious_pdf():
    name = 'fixtures/malicious.pdf'
    with open(module_path('tests.onegov.file', name), 'rb') as f:
        yield f.read()


@pytest.fixture(scope='function')
def pdf_example():
    name = 'fixtures/example.pdf'
    with open(module_path('tests.onegov.file', name), 'rb') as f:
        yield f.read()
