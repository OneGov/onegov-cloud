from datetime import date
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import Vote
from pytest import fixture
from tests.onegov.election_day.common import DummyApp
from tests.onegov.election_day.common import DummyRequest


@fixture(scope='function')
def searchable_archive(session):
    archive = SearchableArchivedResultCollection(DummyApp(session))

    # Create 12 entries
    for year in (2009, 2011, 2014):
        session.add(
            Election(
                title="Election {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )
    for year in (2008, 2012, 2016):
        session.add(
            ElectionCompound(
                title="Elections {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )
    for year in (2011, 2015, 2016):
        session.add(
            Vote(
                title="Vote {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )
    for domain in ('canton', 'region', 'district', 'none', 'municipality'):
        session.add(
            Election(
                title="Election {}".format(domain),
                domain=domain,
                date=date(2019, 1, 1),
            )
        )

    session.flush()
    archive.update_all(DummyRequest())
    return archive


def test_searchable_archive(session, searchable_archive):
    # Test to_date is always filled in and is type date
    archive = SearchableArchivedResultCollection(DummyApp(session))
    assert archive.to_date
    assert archive.from_date is None
    assert isinstance(archive.to_date, date)

    # Test initial query without params
    assert archive.query().count() == 14

    # Test with values like you would when going to search form first time
    archive = SearchableArchivedResultCollection(DummyApp(session))
    archive.domains = ['federation', 'canton', 'region', 'municipality']
    archive.answers = ['accepted', 'rejected', 'counter_proposal']
    archive.term = ''
    assert not archive.item_type
    assert archive.query().count() == 14

    # Test to_date is neglected if from_date is not given
    archive = SearchableArchivedResultCollection(DummyApp(session))
    assert not archive.from_date
    assert 'WHERE archived_results.date' \
           not in str(archive.query())

    # Test query and results with a value of to_date and from_date
    archive = SearchableArchivedResultCollection(DummyApp(session))
    archive.from_date = date(2009, 1, 1)
    assert 'WHERE archived_results.date' \
           in str(archive.query())
    assert archive.query().count() == 13

    # Test getting et the 2009 election
    archive = SearchableArchivedResultCollection(DummyApp(session))
    archive.from_date = date(2008, 1, 1)
    archive.to_date = date(2008, 1, 2)
    assert archive.query().count() == 1

    # Test by item type
    archive = SearchableArchivedResultCollection(DummyApp(session))
    archive.item_type = 'vote'
    assert archive.query().count() == 3

    archive.reset_query_params()
    archive.item_type = 'election'
    assert archive.query().count() == 11

    # Test domains
    archive = SearchableArchivedResultCollection(DummyApp(session))
    archive.domains = ['federation']
    assert archive.query().count() == 9

    archive.domains = ['canton']
    assert archive.query().count() == 1

    archive.domains = ['region']
    assert archive.query().count() == 3

    archive.domains = ['district']
    assert archive.query().count() == 1

    archive.domains = ['none']
    assert archive.query().count() == 1

    archive.domains = ['municipality']
    assert archive.query().count() == 1

    # Test voting result
    results = session.query(ArchivedResult).filter_by(type='vote').all()
    for item in results:
        item.answer = 'accepted'

    archive = SearchableArchivedResultCollection(DummyApp(session))
    archive.item_type = 'vote'
    archive.answers = ['accepted']
    assert archive.query().count() == 3

    # Test term
    # want to find the 2008 election
    archive = SearchableArchivedResultCollection(DummyApp(session))
    archive.term = 'election 2009'
    assert archive.query().count() == 1

    # Test combination of parameters
    archive = SearchableArchivedResultCollection(DummyApp(session))
    archive.domains = ['federation']   # filter to 10
    archive.item_type = 'election'     # filters to 6
    archive.answers = ['accepted', 'rejected', 'counter_proposal']
    archive.from_date = date(2009, 1, 1)
    archive.to_date = date(2009, 1, 2)
    archive.term = 'Election 2009'
    assert archive.locale == 'de_CH'
    assert archive.query().count() == 1

    sql_query = str(archive.query())
    assert 'archived_results.domain IN' in sql_query
    assert 'archived_results.date >=' in sql_query
    assert 'archived_results.type IN' in sql_query
    assert 'archived_results.date >=' in sql_query
    assert 'archived_results.date <=' in sql_query
    assert "archived_results.title_translations -> 'de_CH'" in sql_query
    assert "archived_results.shortcode) @@ to_tsquery" in sql_query

    # Test pagination
    archive = SearchableArchivedResultCollection(DummyApp(session))
    assert archive.batch_size == 10
    assert len(archive.batch) == 10
    assert archive.subset_count == 14
    assert archive.page_index == 0
    assert archive.pages_count == 2
    next_ = archive.next
    assert next_.page_index != archive.page_index
    by_index = archive.page_by_index(2)
    for key in archive.__dict__:
        if key in ('page', 'cached_subset', 'batch'):
            continue
        assert getattr(archive, key) == getattr(by_index, key)

    # Test ordered by date descending
    archive = SearchableArchivedResultCollection(DummyApp(session))
    items = archive.query().all()
    assert items[0].date == date(2019, 1, 1)
    assert items[-1].date == date(2008, 1, 1)

    # Test ordered by date of subset with different domains
    archive = SearchableArchivedResultCollection(DummyApp(session))
    archive.from_date = date(2019, 1, 1)
    archive.to_date = date(2019, 1, 1)
    assert [item.domain for item in archive.query()] == [
        'canton', 'region', 'district', 'none', 'municipality'
    ]

    archive.app.principal.domain = 'municipality'
    assert [item.domain for item in archive.query()] == [
        'municipality', 'canton', 'region', 'district', 'none'
    ]


def test_searchable_archive_exclude_elections(searchable_archive):
    searchable_archive.item_type = 'election'
    assert searchable_archive.query().count() == 11

    session = searchable_archive.session
    election_compound = session.query(ElectionCompound).first()
    election_compound.elections = session.query(Election).all()
    searchable_archive.update_all(DummyRequest())
    assert searchable_archive.query().count() == 3


def test_searchable_archive_query_term_only_on_locale(election_day_app_zg):

    session = election_day_app_zg.session_manager.session()
    vote = Vote(title="Vote {}".format(2012), domain='federation',
                date=date(2012, 1, 1))
    vote.title_translations['de_CH'] = 'Election (de)'
    vote.title_translations['fr_CH'] = 'Election (fr)'
    vote.title_translations['it_CH'] = 'Election (it)'
    vote.title_translations['rm_CH'] = 'Election (rm)'
    session.add(vote)
    session.flush()

    archive = SearchableArchivedResultCollection(DummyApp(session))
    request = DummyRequest(
        locale='de_CH',
        app=election_day_app_zg,
        session=session)

    archive.update_all(request)
    item = archive.query().first()
    assert item.title == 'Election (de)'
