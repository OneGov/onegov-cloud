from __future__ import annotations

from datetime import date
from datetime import datetime
from decimal import Decimal
from freezegun import freeze_time
from onegov.swissvotes.collections import SwissVoteCollection
from pytz import utc


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestApp


def test_app(swissvotes_app: TestApp) -> None:
    assert swissvotes_app.principal
    assert swissvotes_app.static_content_pages == {
        'home', 'disclaimer', 'imprint', 'data-protection'
    }


def test_app_dataset_caches(swissvotes_app: TestApp) -> None:
    votes = SwissVoteCollection(swissvotes_app)

    csv = [swissvotes_app.get_cached_dataset('csv')]
    xlsx = [swissvotes_app.get_cached_dataset('xlsx')]

    with freeze_time(datetime(2019, 1, 1, 10, tzinfo=utc)):
        votes.add(
            id=1,
            bfs_number=Decimal('100.1'),
            date=date(1990, 6, 2),
            title_de="Vote",
            title_fr="Vote",
            short_title_de="Vote",
            short_title_fr="Vote",
            _legal_form=1
        )

    csv.append(swissvotes_app.get_cached_dataset('csv'))
    xlsx.append(swissvotes_app.get_cached_dataset('xlsx'))

    with freeze_time(datetime(2019, 7, 9, 12, tzinfo=utc)):
        votes.add(
            id=2,
            bfs_number=Decimal('100.2'),
            date=date(1990, 6, 2),
            title_de="Vote",
            title_fr="Vote",
            short_title_de="Vote",
            short_title_fr="Vote",
            _legal_form=1
        )

    csv.append(swissvotes_app.get_cached_dataset('csv'))
    xlsx.append(swissvotes_app.get_cached_dataset('xlsx'))

    assert len(csv) == len(set(csv))
    assert len(xlsx) == len(set(xlsx))
    assert swissvotes_app.filestorage is not None
    assert set(swissvotes_app.filestorage.listdir('.')) == {
        'dataset-.csv',
        'dataset-.xlsx',
        'dataset-1546336800.0.csv',
        'dataset-1546336800.0.xlsx',
        'dataset-1562673600.0.csv',
        'dataset-1562673600.0.xlsx',
    }
