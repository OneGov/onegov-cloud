from datetime import date

from onegov.ballot import Vote
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.models import ArchivedResult
from tests.onegov.election_day.common import DummyRequest


class TestSearchableCollection:

    available_types = [t[0] for t in ArchivedResult.types_of_results]
    available_domains = [d[0] for d in ArchivedResult.types_of_domains]
    available_answers = ['accepted', 'rejected', 'counter_proposal']

    def test_initial_config(self, searchable_archive):
        # Test to_date is always filled in and is type date
        assert searchable_archive.to_date
        assert searchable_archive.from_date is None
        assert isinstance(searchable_archive.to_date, date)

    def test_initial_query(self, searchable_archive):
        # Test initial query without params
        assert searchable_archive.query().count() == 12

    def test_default_values_of_form(self, searchable_archive):
        # Set values like you would when going to search form first time

        archive = searchable_archive
        archive.domains = self.available_domains
        archive.types = self.available_types
        archive.answers = self.available_answers
        archive.term = ''
        assert not searchable_archive.item_type
        sql_query = str(archive.query(sort=False))
        assert 'archived_results.domains IN' not in sql_query
        assert 'archived_results.date >=' not in sql_query
        assert 'archived_results.type IN' not in sql_query
        assert 'archived_results.date >= %(date_1)s AND' \
               ' archived_results.date <= %(date_2)s' not in sql_query
        # test for the term that looks in title_translations
        assert "archived_results.title_translations -> 'de_CH'"\
               not in sql_query
        assert "archived_results.shortcode) @@ to_tsquery" not in sql_query

    def test_from_date_to_date(self, searchable_archive):
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

    def test_ignore_types_with_item_type(self, searchable_archive):
        # Test if types is ignored when item_type is set
        searchable_archive.item_type = 'election'
        searchable_archive.types = ['vote']
        assert searchable_archive.query().count() != 3

    def test_query_with_types_and_type(self, searchable_archive):
        # Check if types is queried correctly
        assert searchable_archive.item_type is None
        searchable_archive.types = ['vote']
        assert searchable_archive.query().count() == 3
        searchable_archive.reset_query_params()
        searchable_archive.item_type = 'vote'
        assert searchable_archive.query().count() == 3

        searchable_archive.reset_query_params()

        searchable_archive.types = ['election']
        assert searchable_archive.query().count() == 6
        searchable_archive.reset_query_params()
        # When used with item_type, compound elections are also returned
        searchable_archive.item_type = 'election'
        assert searchable_archive.query().count() == 9
        searchable_archive.item_type = 'election_compound'
        assert searchable_archive.query().count() == 9

        searchable_archive.reset_query_params()
        searchable_archive.types = ['vote', 'election', 'election_compound']
        assert searchable_archive.query().count() == 12

    def test_query_with_domains(self, searchable_archive):
        archive = searchable_archive
        archive.domains = ['federation']
        assert archive.query().count() == 9

        archive.domains = ['canton']
        assert archive.query().count() == 1

        archive.domains = ['region']
        assert archive.query().count() == 1

        archive.domains = ['municipality']
        assert archive.query().count() == 1

    def test_query_with_voting_result(self, session, searchable_archive):
        results = session.query(ArchivedResult).all()
        archive = searchable_archive
        for item in results:
            assert not item.answer
            item.answer = 'accepted'
            item.type = 'vote'
            # assert item.answer is None      # fails since it has also ''
        for item in session.query(ArchivedResult).all():
            assert item.answer == 'accepted'

        archive.types = ['vote', 'election']
        archive.answers = ['accepted']
        assert archive.query().count() == len(results)

    def test_with_term(self, searchable_archive):
        # want to find the 2008 election
        archive = searchable_archive
        searchable_archive.term = 'election 2009'
        assert archive.query().count() == 1

    def test_with_all_params_non_default(self, searchable_archive):
        # Want to receive 2009 election
        archive = searchable_archive
        assert not archive.item_type
        all_items = archive.query().all()
        # set the answers
        for item in all_items:
            item.answer = 'rejected'

        archive.domains = ['federation']   # filter to 10
        archive.types = ['election']       # filters to 6
        archive.answers = self.available_answers     # no filter
        archive.from_date = date(2009, 1, 1)
        archive.to_date = date(2009, 1, 2)
        archive.term = 'Election 2009'
        assert archive.locale == 'de_CH'
        assert archive.query().count() == 1

        sql_query = str(archive.query())
        print(sql_query)
        assert 'archived_results.domain IN' in sql_query
        assert 'archived_results.date >=' in sql_query
        assert 'archived_results.type IN' in sql_query
        assert 'archived_results.date >= %(date_1)s AND' \
               ' archived_results.date <= %(date_2)s' in sql_query
        # test for the term that looks in title_tranTslations
        assert "archived_results.title_translations -> 'de_CH'" in sql_query
        assert "archived_results.shortcode) @@ to_tsquery" in sql_query

    def test_query_term_only_on_locale(
            self, election_day_app):

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

        # test for different locales

        # for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        #     archive.locale = locale
        #     election_day_app.session_manager.current_locale = locale
        #     archive.term = locale[0:2]
        #     sql_query = str(archive.query())
        #     print(sql_query)
        #     assert archive.query().count() == 1
        #     assert f"archived_results.title_translations -> '{locale}'" \
        #            in sql_query

    def test_group_items_for_archive(
            self, searchable_archive):
        items = searchable_archive.query().all()
        request = DummyRequest()
        assert request.app.principal.domain, 'DummyRequest should have domain'
        g_items = searchable_archive.group_items(items, request)
        votes = g_items.get('votes')
        elections = g_items.get('elections')
        assert len(items) == len(votes) + len(elections)

    def test_pagination(self, searchable_archive):
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

    def test_query_ordering(self, searchable_archive):

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

    def test_check_from_date_to_date(self, searchable_archive):
        # check_from_date_to_date is triggered in the query function

        archive = searchable_archive

        assert archive.to_date == date.today()
        # both are not set
        archive.check_from_date_to_date()
        assert archive.from_date is None, 'Should not modify anything'
        assert archive.to_date == date.today()

        # from_date bigger than to_date
        archive.from_date = date(2019, 1, 1)
        archive.to_date = date(2018, 1, 1)
        assert archive.from_date
        assert archive.to_date

        archive.check_from_date_to_date()
        assert archive.from_date
        assert archive.to_date

        assert archive.from_date == archive.to_date

        archive.to_date = date(2300, 1, 1)
        archive.check_from_date_to_date()
        assert archive.to_date == date.today()
