from datetime import date
from datetime import datetime
from decimal import Decimal
from freezegun import freeze_time
from onegov.swissvotes.collections import SwissVoteCollection
from psycopg2.extras import NumericRange
from pytz import utc


def test_app(swissvotes_app):
    assert swissvotes_app.principal
    assert swissvotes_app.static_content_pages == {
        'home', 'disclaimer', 'imprint', 'data-protection'
    }


def test_app_dataset_caches(swissvotes_app):
    votes = SwissVoteCollection(swissvotes_app)

    csv = [swissvotes_app.get_cached_dataset('csv')]
    xlsx = [swissvotes_app.get_cached_dataset('xlsx')]

    with freeze_time(datetime(2019, 1, 1, 10, tzinfo=utc)):
        votes.add(
            id=1,
            bfs_number=Decimal('100.1'),
            date=date(1990, 6, 2),
            legislation_number=4,
            legislation_decade=NumericRange(1990, 1994),
            title_de="Vote",
            title_fr="Vote",
            short_title_de="Vote",
            short_title_fr="Vote",
            votes_on_same_day=2,
            _legal_form=1
        )

    csv.append(swissvotes_app.get_cached_dataset('csv'))
    xlsx.append(swissvotes_app.get_cached_dataset('xlsx'))

    with freeze_time(datetime(2019, 7, 9, 12, tzinfo=utc)):
        votes.add(
            id=2,
            bfs_number=Decimal('100.2'),
            date=date(1990, 6, 2),
            legislation_number=4,
            legislation_decade=NumericRange(1990, 1994),
            title_de="Vote",
            title_fr="Vote",
            short_title_de="Vote",
            short_title_fr="Vote",
            votes_on_same_day=2,
            _legal_form=1
        )

    csv.append(swissvotes_app.get_cached_dataset('csv'))
    xlsx.append(swissvotes_app.get_cached_dataset('xlsx'))

    assert len(csv) == len(set(csv))
    assert len(xlsx) == len(set(xlsx))
    assert set(swissvotes_app.filestorage.listdir('.')) == {
        'dataset-.csv',
        'dataset-.xlsx',
        'dataset-1546336800.0.csv',
        'dataset-1546336800.0.xlsx',
        'dataset-1562673600.0.csv',
        'dataset-1562673600.0.xlsx',
    }
