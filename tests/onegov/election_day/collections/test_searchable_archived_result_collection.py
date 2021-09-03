from datetime import date
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.models import ArchivedResult
from pytest import fixture
from tests.onegov.election_day.common import DummyRequest


@fixture(scope='function')
def searchable_archive(session):
    archive = SearchableArchivedResultCollection(session)

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
    for domain in ('canton', 'region', 'municipality'):
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


def test_searchable_archive_initial_config(searchable_archive):
    # Test to_date is always filled in and is type date
    assert searchable_archive.to_date
    assert searchable_archive.from_date is None
    assert isinstance(searchable_archive.to_date, date)


def test_searchable_archive_initial_query(searchable_archive):
    # Test initial query without params
    assert searchable_archive.query().count() == 12


def test_searchable_archive_default_values_of_form(searchable_archive):
    # Set values like you would when going to search form first time
    archive = searchable_archive
    archive.domains = [d[0] for d in ArchivedResult.types_of_domains]
    archive.answers = ['accepted', 'rejected', 'counter_proposal']
    archive.term = ''

    assert not searchable_archive.item_type
    assert searchable_archive.query().count() == 12


def test_searchable_archive_from_date_to_date(searchable_archive):
    archive = searchable_archive
    # Test to_date is neglected if from_date is not given
    assert not archive.from_date
    assert 'WHERE archived_results.date' \
           not in str(archive.query())

    # Test query and results with a value of to_date and from_date
    archive.from_date = date(2009, 1, 1)
    assert 'WHERE archived_results.date' \
           in str(archive.query())
    assert archive.query().count() == 11

    # get the 2009 election
    archive.reset_query_params()
    archive.from_date = date(2008, 1, 1)
    archive.to_date = date(2008, 1, 2)
    assert archive.query().count() == 1


def test_searchable_archive_query_item_type(searchable_archive):
    searchable_archive.item_type = 'vote'
    assert searchable_archive.query().count() == 3

    searchable_archive.reset_query_params()
    searchable_archive.item_type = 'election'
    assert searchable_archive.query().count() == 9


def test_searchable_archive_query_with_domains(searchable_archive):
    archive = searchable_archive
    archive.domains = ['federation']
    assert archive.query().count() == 9

    archive.domains = ['canton']
    assert archive.query().count() == 1

    archive.domains = ['region']
    assert archive.query().count() == 1

    archive.domains = ['municipality']
    assert archive.query().count() == 1


def test_searchable_archive_query_with_voting_result(
    session, searchable_archive
):
    results = session.query(ArchivedResult).all()
    archive = searchable_archive
    for item in results:
        assert not item.answer
        item.answer = 'accepted'
        item.type = 'vote'
    for item in session.query(ArchivedResult).all():
        assert item.answer == 'accepted'

    archive.item_type = 'vote'
    archive.answers = ['accepted']
    assert archive.query().count() == len(results)


def test_searchable_archive_with_term(searchable_archive):
    # want to find the 2008 election
    archive = searchable_archive
    searchable_archive.term = 'election 2009'
    assert archive.query().count() == 1


def test_searchable_archive_with_all_params_non_default(searchable_archive):
    # Want to receive 2009 election
    archive = searchable_archive
    assert not archive.item_type
    all_items = archive.query().all()
    # set the answers
    for item in all_items:
        item.answer = 'rejected'

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


def test_searchable_archive_query_term_only_on_locale(election_day_app):

    session = election_day_app.session_manager.session()
    vote = Vote(title="Vote {}".format(2012), domain='federation',
                date=date(2012, 1, 1))
    vote.title_translations['de_CH'] = 'Election (de)'
    vote.title_translations['fr_CH'] = 'Election (fr)'
    vote.title_translations['it_CH'] = 'Election (it)'
    vote.title_translations['rm_CH'] = 'Election (rm)'
    session.add(vote)
    session.flush()

    archive = SearchableArchivedResultCollection(session)
    request = DummyRequest(
        locale='de_CH',
        app=election_day_app,
        session=session)

    archive.update_all(request)
    item = archive.query().first()
    assert item.title == 'Election (de)'


def test_searchable_archive_pagination(searchable_archive):
    # Tests methods that have to be implemented for pagination parent class
    assert searchable_archive.batch_size == 10
    assert len(searchable_archive.batch) == 10
    assert searchable_archive.subset_count == 12
    assert searchable_archive.page_index == 0
    assert searchable_archive.pages_count == 2
    next_ = searchable_archive.next
    assert next_.page_index != searchable_archive.page_index
    by_index = searchable_archive.page_by_index(2)

    for key in searchable_archive.__dict__:
        if key in ('page', 'cached_subset', 'batch'):
            continue
        assert getattr(searchable_archive, key) == getattr(by_index, key)


def test_searchable_archive_query_ordering(searchable_archive):

    items = searchable_archive.query().all()
    # test ordered by date descending
    assert items[0].date == date(2019, 1, 1)
    assert items[-1].date == date(2008, 1, 1)

    # subset with different domains
    searchable_archive.from_date = date(2019, 1, 1)
    searchable_archive.to_date = date(2019, 1, 1)
    items_one_date = searchable_archive.query().all()
    assert items_one_date[0].domain == 'canton'
    assert items_one_date[1].domain == 'region'
    assert items_one_date[2].domain == 'municipality'

    # Test for municipality
    searchable_archive.app_principal_domain = 'municipality'
    items_one_date = searchable_archive.query().all()
    assert items_one_date[0].domain == 'municipality'
    assert items_one_date[1].domain == 'canton'
    assert items_one_date[2].domain == 'region'


def test_searchable_archive_exclude_elections(searchable_archive):
    searchable_archive.item_type = 'election'
    assert searchable_archive.query().count() == 9

    session = searchable_archive.session
    election_compound = session.query(ElectionCompound).first()
    election_compound.elections = session.query(Election).all()
    searchable_archive.update_all(DummyRequest())
    assert searchable_archive.query().count() == 3
