from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from uuid import uuid4


def test_data_source_item_collection(session):
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


def test_data_source_item_collection_pagination(session):
    id_ = uuid4()
    DataSourceCollection(session).add(
        DataSource(type='vote', name='ds', id=id_)
    )
    collection = DataSourceItemCollection(session, id=id_)

    for number in range(100):
        collection.add(DataSourceItem(number='{:02}'.format(number)))
    assert collection.query().count() == 100

    assert DataSourceItemCollection(session, id=id_, page=0).batch[0].number \
        == '00'
    assert DataSourceItemCollection(session, id=id_, page=4).batch[4].number \
        == '44'
    assert DataSourceItemCollection(session, id=id_, page=5).batch[5].number \
        == '55'
    assert DataSourceItemCollection(session, id=id_, page=9).batch[9].number \
        == '99'

    assert len(DataSourceItemCollection(session, page=10).batch) == 0
