from __future__ import annotations

import pytest

from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.models import DataSource


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_data_source_collection(session: Session) -> None:
    collection = DataSourceCollection(session)

    collection.add(DataSource(type='vote', name='ds_vote'))
    data_source = collection.query().one()
    assert data_source.type == 'vote'
    assert data_source.name == 'ds_vote'
    assert collection.by_id(data_source.id) == data_source

    collection.delete(data_source)
    assert collection.query().count() == 0


def test_data_source_collection_pagination(session: Session) -> None:
    collection = DataSourceCollection(session)

    for number in range(100):
        collection.add(DataSource(type='vote', name='{:02}'.format(number)))
    assert collection.query().count() == 100

    assert DataSourceCollection(session, page=0).batch[0].name == '99'
    assert DataSourceCollection(session, page=4).batch[4].name == '55'
    assert DataSourceCollection(session, page=5).batch[5].name == '44'
    assert DataSourceCollection(session, page=9).batch[9].name == '00'

    assert len(DataSourceCollection(session, page=10).batch) == 0


def test_data_source_pagination_negative_page_index(session: Session) -> None:
    collection = DataSourceCollection(session, page=-15)
    assert collection.page == 0
    assert collection.page_index == 0
    assert collection.page_by_index(-2).page == 0
    assert collection.page_by_index(-3).page_index == 0

    with pytest.raises(AssertionError):
        DataSourceCollection(session, page=None)  # type: ignore[arg-type]
