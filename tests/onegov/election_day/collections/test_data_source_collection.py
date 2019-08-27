from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.models import DataSource


def test_data_source_collection(session):
    collection = DataSourceCollection(session)

    collection.add(DataSource(type='vote', name='ds_vote'))
    data_source = collection.query().one()
    assert data_source.type == 'vote'
    assert data_source.name == 'ds_vote'
    assert collection.by_id(data_source.id) == data_source

    collection.delete(data_source)
    assert collection.query().count() == 0


def test_data_source_collection_pagination(session):
    collection = DataSourceCollection(session)

    for number in range(100):
        collection.add(DataSource(type='vote', name='{:02}'.format(number)))
    assert collection.query().count() == 100

    assert DataSourceCollection(session, page=0).batch[0].name == '00'
    assert DataSourceCollection(session, page=4).batch[4].name == '44'
    assert DataSourceCollection(session, page=5).batch[5].name == '55'
    assert DataSourceCollection(session, page=9).batch[9].name == '99'

    assert len(DataSourceCollection(session, page=10).batch) == 0
