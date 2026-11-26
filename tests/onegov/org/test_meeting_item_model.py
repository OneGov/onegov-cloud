from __future__ import annotations

from datetime import datetime
from onegov.org.models.meeting import Meeting
from onegov.org.models.meeting_item import MeetingItem, MeetingItemCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_meeting_item_properties() -> None:
    item = MeetingItem(title='Budget', number='1')
    assert item.fts_suggestion == 'Budget'
    assert item.display_name == '1 Budget'
    assert '1' in repr(item)
    assert 'Budget' in repr(item)

    # without a number the display name is just the title
    assert MeetingItem(title='Budget').display_name == 'Budget'


def test_meeting_item_fts_last_change() -> None:
    # no meeting -> no change date
    assert MeetingItem(title='Budget').fts_last_change is None

    item = MeetingItem(title='Budget')
    item.meeting = Meeting(
        title='Session', start_datetime=datetime(2020, 5, 1, 10))
    assert item.fts_last_change == datetime(2020, 5, 1, 10)


def test_meeting_item_collection(session: Session) -> None:
    items = MeetingItemCollection(session)
    assert items.model_class is MeetingItem
    assert items.query().count() == 0
