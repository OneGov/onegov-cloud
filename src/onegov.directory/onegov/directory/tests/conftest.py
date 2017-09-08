import pytest

from depot.manager import DepotManager


@pytest.yield_fixture(scope='function', autouse=True)
def depot():
    DepotManager.configure('default', {
        'depot.backend': 'depot.io.memory.MemoryFileStorage'
    })

    yield DepotManager.get()

    DepotManager._clear()
