from datetime import date
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem


def test_data_source(session):
    session.add(DataSource(name='ds_vote', type='vote'))
    session.add(DataSource(name='ds_majorz', type='majorz'))
    session.add(DataSource(name='ds_proporz', type='proporz'))
    session.flush()

    ds_vote = session.query(DataSource).filter_by(type='vote').one()
    assert ds_vote.name == 'ds_vote'
    assert ds_vote.label == 'Vote'
    assert ds_vote.token

    ds_majorz = session.query(DataSource).filter_by(type='majorz').one()
    assert ds_majorz.name == 'ds_majorz'
    assert ds_majorz.label == 'Election based on the simple majority system'
    assert ds_majorz.token

    ds_proporz = session.query(DataSource).filter_by(type='proporz').one()
    assert ds_proporz.name == 'ds_proporz'
    assert ds_proporz.label == 'Election based on proportional representation'
    assert ds_proporz.token

    dt = date(2015, 6, 14)
    session.add(Vote(title='v', domain='canton', date=dt))
    session.add(Election(title='m', type='majorz', domain='canton', date=dt))
    session.add(Election(title='p', type='proporz', domain='canton', date=dt))
    session.flush()

    vote = session.query(Vote).one()
    majorz = session.query(Election).filter_by(type='majorz').one()
    proporz = session.query(Election).filter_by(type='proporz').one()

    assert ds_vote.query_candidates().one() == vote
    assert ds_majorz.query_candidates().one() == majorz
    assert ds_proporz.query_candidates().one() == proporz

    ds_vote.items.append(
        DataSourceItem(district='1', number='11', vote_id=vote.id)
    )
    ds_majorz.items.append(
        DataSourceItem(district='2', number='22', election_id=majorz.id)
    )
    ds_proporz.items.append(
        DataSourceItem(district='3', number='33', election_id=proporz.id)
    )
    session.flush()

    item = ds_vote.items.one()
    assert item.item == vote
    assert item.name == 'v'
    assert item.district == '1'
    assert item.number == '11'

    item = ds_majorz.items.one()
    assert item.item == majorz
    assert item.name == 'm'
    assert item.district == '2'
    assert item.number == '22'

    item = ds_proporz.items.one()
    assert item.item == proporz
    assert item.name == 'p'
    assert item.district == '3'
    assert item.number == '33'
