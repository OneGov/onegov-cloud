import pytest

from depot.manager import DepotManager


@pytest.yield_fixture(scope='function', autouse=True)
def depot(temporary_directory):
    DepotManager.configure('default', {
        'depot.backend': 'depot.io.local.LocalFileStorage',
        'depot.storage_path': temporary_directory
    })

    yield DepotManager.get()

    DepotManager._clear()
