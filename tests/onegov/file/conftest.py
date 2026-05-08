from __future__ import annotations

import pytest

from depot.manager import DepotManager


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from depot.io.interfaces import FileStorage


@pytest.fixture(scope='function', autouse=True)
def depot(temporary_directory: str) -> Iterator[FileStorage | None]:
    DepotManager.configure('default', {
        'depot.backend': 'depot.io.local.LocalFileStorage',
        'depot.storage_path': temporary_directory
    })

    yield DepotManager.get()

    DepotManager._clear()  # type: ignore[attr-defined]
