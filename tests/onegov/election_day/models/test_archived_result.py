from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timezone
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import DummyRequest


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_archived_result(session: Session) -> None:
    result = ArchivedResult()
    result.date = date(2007, 1, 1)
    result.last_modified = datetime(2007, 1, 2, 0, 0, tzinfo=timezone.utc)
    result.last_result_change = datetime(2007, 1, 1, 0, 0, tzinfo=timezone.utc)
    result.schema = 'schema'
    result.external_id = 'id'
    result.url = 'url'
    result.title = 'title'
    result.title_translations['en'] = 'title'  # type: ignore[index]
    result.domain = 'canton'
    result.type = 'vote'
    result.name = 'name'
    result.shortcode = 'shortcode'
    result.elected_candidates = [('Joe', 'Quimby')]
    result.elections = ['https://localhost/1', 'https://localhost/1']
    result.answer = 'rejected'
    result.nays_percentage = 20.5
    result.yeas_percentage = 79.5
    result.counted = True
    result.completed = True
    result.turnout = 50

    session.add(result)
    session.flush()
    result = session.query(ArchivedResult).one()

    assert result.id
    assert result.date == date(2007, 1, 1)
    assert result.last_modified == datetime(
        2007, 1, 2, 0, 0, tzinfo=timezone.utc
    )
    assert result.last_result_change == datetime(
        2007, 1, 1, 0, 0, tzinfo=timezone.utc
    )
    assert result.schema == 'schema'
    assert result.external_id == 'id'
    assert result.url == 'url'
    assert result.title == 'title'
    assert result.title_translations == {'en': 'title', 'de_CH': 'title'}
    assert result.domain == 'canton'
    assert result.type == 'vote'
    assert result.name == 'name'
    assert result.shortcode == 'shortcode'
    assert result.elected_candidates == [('Joe', 'Quimby')]
    assert result.elections == ['https://localhost/1', 'https://localhost/1']
    assert result.answer == 'rejected'
    assert result.nays_percentage == 20.5
    assert result.yeas_percentage == 79.5
    assert result.local_answer == ''
    assert result.local_nays_percentage == 100.0
    assert result.local_yeas_percentage == 0.0
    assert result.counted is True
    assert result.completed is True
    assert result.meta == {
        'answer': 'rejected',
        'nays_percentage': 20.5,
        'yeas_percentage': 79.5,
        'counted': True,
        'completed': True,
        'elected_candidates': [('Joe', 'Quimby')],
        'elections': ['https://localhost/1', 'https://localhost/1'],
        'id': 'id',
        'turnout': 50
    }
    assert result.type_class == Vote

    # Test progress
    assert result.progress == (0, 0)
    result.total_entities = 10
    assert result.progress == (0, 10)
    result.counted_entities = 5
    assert result.progress == (5, 10)

    # Test display functions
    request: Any = DummyRequest()
    assert result.display_answer(request) == 'rejected'
    assert result.display_nays_percentage(request) == 20.5
    assert result.display_yeas_percentage(request) == 79.5

    request.app.principal.domain = 'municipality'
    assert result.display_answer(request) == ''
    assert result.display_nays_percentage(request) == 100.0
    assert result.display_yeas_percentage(request) == 0.0

    # Test title prefix
    assert result.title_prefix(request) == ''

    result.domain = 'municipality'
    assert result.title_prefix(request) == result.name

    # Test fetched and adjusted URL
    assert result.is_fetched(request) is True
    assert result.adjusted_url(request) == 'url'
    request.app.schema = 'schema'
    assert result.is_fetched(request) is False
    assert result.adjusted_url(request) == "Vote//{'id': 'id'}"

    # Test copy from
    copied = ArchivedResult()
    copied.copy_from(result)

    assert copied.date == date(2007, 1, 1)
    assert copied.last_modified == datetime(
        2007, 1, 2, 0, 0, tzinfo=timezone.utc
    )
    assert copied.last_result_change == datetime(
        2007, 1, 1, 0, 0, tzinfo=timezone.utc
    )
    assert copied.schema == 'schema'
    assert copied.external_id == 'id'
    assert copied.url == 'url'
    assert copied.title == 'title'
    assert copied.title_translations == {'en': 'title', 'de_CH': 'title'}
    assert copied.domain == 'municipality'
    assert copied.type == 'vote'
    assert copied.name == 'name'
    assert copied.shortcode == 'shortcode'
    assert copied.elected_candidates == [('Joe', 'Quimby')]
    assert copied.elections == ['https://localhost/1', 'https://localhost/1']
    assert copied.total_entities == 10
    assert copied.counted_entities == 5
    assert copied.progress == (5, 10)
    assert copied.answer == 'rejected'
    assert copied.nays_percentage == 20.5
    assert copied.yeas_percentage == 79.5
    assert copied.counted is True
    assert copied.completed is True
    assert copied.meta == {
        'answer': 'rejected',
        'nays_percentage': 20.5,
        'yeas_percentage': 79.5,
        'counted': True,
        'completed': True,
        'elected_candidates': [('Joe', 'Quimby')],
        'elections': ['https://localhost/1', 'https://localhost/1'],
        'id': 'id',
        'turnout': 50
    }
    assert copied.shortcode == 'shortcode'


def test_archived_result_local_results(session: Session) -> None:
    result = ArchivedResult()

    assert result.answer == ''
    assert result.nays_percentage == 100.0
    assert result.yeas_percentage == 0.0

    assert result.local_answer == ''
    assert result.local_nays_percentage == 100.0
    assert result.local_yeas_percentage == 0.0

    request: Any = DummyRequest()
    assert result.display_answer(request) == ''
    assert result.display_nays_percentage(request) == 100.0
    assert result.display_yeas_percentage(request) == 0.0

    request.app.principal.domain = 'municipality'
    assert result.display_answer(request) == ''
    assert result.display_nays_percentage(request) == 100.0
    assert result.display_yeas_percentage(request) == 0.0

    result.answer = 'accepted'
    result.yeas_percentage = 79.5
    result.nays_percentage = 20.5

    assert result.meta == {
        'answer': 'accepted',
        'nays_percentage': 20.5,
        'yeas_percentage': 79.5
    }

    assert result.answer == 'accepted'
    assert result.nays_percentage == 20.5
    assert result.yeas_percentage == 79.5

    assert result.local_answer == ''
    assert result.local_nays_percentage == 100.0
    assert result.local_yeas_percentage == 0.0

    request = DummyRequest()
    assert result.display_answer(request) == 'accepted'
    assert result.display_nays_percentage(request) == 20.5
    assert result.display_yeas_percentage(request) == 79.5

    request.app.principal.domain = 'municipality'
    assert result.display_answer(request) == ''
    assert result.display_nays_percentage(request) == 100.0
    assert result.display_yeas_percentage(request) == 0.0

    result.local_answer = 'rejected'
    result.local_yeas_percentage = 40.0
    result.local_nays_percentage = 60.0

    assert result.meta == {
        'answer': 'accepted',
        'yeas_percentage': 79.5,
        'nays_percentage': 20.5,
        'local': {
            'answer': 'rejected',
            'yeas_percentage': 40.0,
            'nays_percentage': 60.0,
        }
    }

    assert result.answer == 'accepted'
    assert result.nays_percentage == 20.5
    assert result.yeas_percentage == 79.5

    assert result.local_answer == 'rejected'
    assert result.local_nays_percentage == 60.0
    assert result.local_yeas_percentage == 40.0

    request = DummyRequest()
    assert result.display_answer(request) == 'accepted'
    assert result.display_nays_percentage(request) == 20.5
    assert result.display_yeas_percentage(request) == 79.5

    request.app.principal.domain = 'municipality'
    assert result.display_answer(request) == 'rejected'
    assert result.display_nays_percentage(request) == 60.0
    assert result.display_yeas_percentage(request) == 40.0
