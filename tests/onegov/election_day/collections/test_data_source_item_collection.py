from __future__ import annotations

import pytest

from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_data_source_item_collection(session: Session) -> None:
    DataSourceCollection(session).add(DataSource(type='vote', name='ds'))
    data_source = session.query(DataSource).one()

    collection = DataSourceItemCollection(session, id=data_source.id)
    assert collection.source is data_source

    collection.add(DataSourceItem(number='1', district='2'))
    item = collection.query().one()
    assert item.number == '1'
    assert item.district == '2'
    assert collection.by_id(item.id) == item

    collection.delete(item)
    assert collection.query().count() == 0


def test_data_source_item_collection_pagination(session: Session) -> None:
    id_ = uuid4()
    DataSourceCollection(session).add(
        DataSource(type='vote', name='ds', id=id_)
    )
    collection = DataSourceItemCollection(session, id=id_)

    for number in range(100):
        collection.add(DataSourceItem(number='{:02}'.format(number)))
    assert collection.query().count() == 100

    assert DataSourceItemCollection(
        session, id=id_, page=0).batch[0].number == '00'
    assert DataSourceItemCollection(
        session, id=id_, page=4).batch[4].number == '44'
    assert DataSourceItemCollection(
        session, id=id_, page=5).batch[5].number == '55'
    assert DataSourceItemCollection(
        session, id=id_, page=9).batch[9].number == '99'

    assert len(DataSourceItemCollection(session, page=10).batch) == 0


def test_data_source_item_pagination_negative_page_index(
    session: Session
) -> None:
    collection = DataSourceItemCollection(session, page=-13)
    assert collection.page == 0
    assert collection.page_index == 0
    assert collection.page_by_index(-2).page == 0
    assert collection.page_by_index(-3).page_index == 0

    with pytest.raises(AssertionError):
        DataSourceItemCollection(session, page=None)  # type: ignore[arg-type]
