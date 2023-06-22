from cached_property import cached_property
from elasticsearch_dsl.function import SF
from elasticsearch_dsl.query import FunctionScore
from elasticsearch_dsl.query import Match
from elasticsearch_dsl.query import MatchPhrase
from elasticsearch_dsl.query import MultiMatch
from sqlalchemy import func

from onegov.core.collection import Pagination
from onegov.core.orm import Base
from onegov.event.models import Event
from onegov.search.utils import searchable_sqlalchemy_models


class Search(Pagination):

    results_per_page = 10
    max_query_length = 100

    def __init__(self, request, query, page):
        self.request = request
        self.query = query
        self.page = page

    @cached_property
    def available_documents(self):
        search = self.request.app.es_search_by_request(self.request)
        return search.count()

    @cached_property
    def explain(self):
        return self.request.is_manager and 'explain' in self.request.params

    @property
    def q(self):
        return self.query

    def __eq__(self, other):
        return self.page == other.page and self.query == other.query

    def subset(self):
        return self.batch

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return Search(self.request, self.query, index)

    @cached_property
    def batch(self):
        if not self.query:
            return None

        search = self.request.app.es_search_by_request(
            request=self.request,
            explain=self.explain
        )

        # queries need to be cut at some point to make sure we're not
        # pushing the elasticsearch cluster to the brink
        query = self.query[:self.max_query_length]

        if query.startswith('#'):
            search = self.hashtag_search(search, query)
        else:
            search = self.generic_search(search, query)

        return search[self.offset:self.offset + self.batch_size].execute()

    @cached_property
    def load_batch_results(self):
        """Load search results and sort events by latest occurrence.

        This methods is a wrapper around `batch.load()`, which returns the
        actual search results form the query. """

        batch = self.batch.load()
        events = []
        non_events = []
        for search_result in batch:
            if isinstance(search_result, Event):
                events.append(search_result)
            else:
                non_events.append(search_result)
        if not events:
            return batch
        sorted_events = sorted(events, key=lambda e: e.latest_occurrence.start)
        return sorted_events + non_events

    def generic_search(self, search, query):

        # make sure the title matches with a higher priority, otherwise the
        # "get lucky" functionality is not so lucky after all
        match_title = MatchPhrase(title={"query": query, "boost": 3})

        # we *could* use Match here and include '_all' fields, but that
        # yields us less exact results, probably because '_all' includes some
        # metadata fields we have no use for
        match_rest = MultiMatch(query=query, fields=[
            field for field in self.request.app.es_mappings.registered_fields
            if not field.startswith('es_')
        ], fuzziness='1', prefix_length=3)

        search = search.query(match_title | match_rest)

        # favour documents with recent changes, over documents without
        search.query = FunctionScore(query=search.query, functions=[
            SF('gauss', es_last_change={
                'offset': '7d',
                'scale': '90d',
                'decay': '0.99'
            })
        ])

        return search

    def hashtag_search(self, search, query):
        return search.query(Match(es_tags=query.lstrip('#')))

    def feeling_lucky(self):
        if self.batch:
            first_entry = self.batch[0].load()

            # XXX the default view to the event should be doing the redirect
            if first_entry.__tablename__ == 'events':
                return self.request.link(first_entry, 'latest')
            else:
                return self.request.link(first_entry)

    @cached_property
    def subset_count(self):
        return self.cached_subset and self.cached_subset.hits.total.value or 0

    def suggestions(self):
        return tuple(self.request.app.es_suggestions_by_request(
            self.request, self.query
        ))


class SearchPostgres(Pagination):
    results_per_page = 10
    max_query_length = 100

    def __init__(self, request, query, page):
        self.request = request
        self.query = query
        self.page = page  # page index
        print('*** tschupre search __init__')

    @cached_property
    def explain(self):
        # what is it used for?
        print('*** tschupre search explain')
        return self.request.is_manager and 'explain' in self.request.params

    @property
    def q(self):
        print('*** tschupre search q')
        return self.query

    def __eq__(self, other):
        print('*** tschupre search __eq__')
        return self.page == other.page and self.query == other.query

    @property
    def page_index(self):
        print('*** tschupre search page_index')
        return self.page

    def page_by_index(self, index):
        print('*** tschupre search page_by_index')
        return SearchPostgres(self.request, self.query, index)

    @cached_property
    def batch(self):
        print('*** tschupre search batch')
        if not self.query:
            return None

        # if self.query.startswith('#'):
        #     search = self.hashtag_search(search, self.query)
        # else:
        #     search = self.generic_search(search, self.query)
        #
        # return search[self.offset:self.offset + self.batch_size].execute()

        return self.postgres_search()

    # def generic_search(self, search, query):
    #     print('*** tschupre search generic_search')
    #
    #     # "get lucky" functionality is not so lucky after all
    #     match_title = MatchPhrase(title={"query": query, "boost": 3})
    #
    #     # we *could* use Match here and include '_all' fields, but that
    #     # yields us less exact results, probably because '_all' includes some
    #     # metadata fields we have no use for
    #     print('*** registered fields:')
    #     for field in self.request.app.orm_mappings.registered_fields:
    #         if not field.startswith('es_'):
    #             # print(f' * field: {field}')
    #             pass
    #     match_rest = MultiMatch(query=query, fields=[
    #         field for field in self.request.app.orm_mappings.
    #         registered_fields
    #         if not field.startswith('es_')
    #     ], fuzziness='1', prefix_length=3)
    #
    #     search = search.query(match_title | match_rest)
    #
    #     # favour documents with recent changes, over documents without
    #     search.query = FunctionScore(query=search.query, functions=[
    #         SF('gauss', es_last_change={
    #             'offset': '7d',
    #             'scale': '90d',
    #             'decay': '0.99'
    #         })
    #     ])
    #
    #     return search

    # def hashtag_search(self, search, query):
    #     print('*** tschupre search hastag_search')
    #     return search.query(Match(es_tags=query.lstrip('#')))

    @cached_property
    def load_batch_results(self):
        """Load search results and sort events by latest occurrence.

        This methods is a wrapper around `batch.load()`, which returns the
        actual search results form the query. """

        batch = self.batch.load()
        events = []
        non_events = []
        for search_result in batch:
            if isinstance(search_result, Event):
                events.append(search_result)
            else:
                non_events.append(search_result)
        if not events:
            return batch
        sorted_events = sorted(events, key=lambda e: e.latest_occurrence.start)
        return sorted_events + non_events

    def feeling_lucky(self):
        print('*** tschupre search feeling_lucky')
        if self.batch:
            first_entry = self.batch[0].load()

            # XXX the default view to the event should be doing the redirect
            if first_entry.__tablename__ == 'events':
                return self.request.link(first_entry, 'latest')
            else:
                return self.request.link(first_entry)

    @cached_property
    def subset_count(self):
        print('*** tschupre search subset_count')
        return 1
        return self.cached_subset and self.cached_subset.hits.total.value or 0

    def suggestions(self):
        print(f'*** tschupre search suggestions for \'{self.query}\'')
        return tuple()
        # self.query is the search term e.g. 'test'

        # session = self.request.session
        # tsquery = func.websearch_to_tsquery(self.query)
        # q = session.query(User)
        # q = q.filter(User.username.match(self.query))  # work but no results
        # q = q.filter(User.__tsvector__.match(self.query))  # works but no
        # results
        # q = q.filter(User.fts_idx_users_username_col.match(self.query))  #
        # q = q.filter(User.__tsvector__.like(self.query))  # not working
        # q = q.filter(User.fts_idx_users_username_col.like(self.query))  #
        # not working
        # works but no results
        # q = q.filter(User.username == self.query)  # works but no results
        # q = q.filter(User.username.like(self.query))  # works but no results
        # q = q.filter(User.username.match(self.query))  # works but no results
        # results = q.all()
        # results = q.limit(5)
        #
        # print('*** query results')
        # for result in results:
        #     print(f'result: {result}')
        #
        # # return results,
        # es_res = tuple(self.request.app.es_suggestions_by_request(
        #     self.request, self.query
        # ))
        #
        # print(es_res)
        # return tuple(self.request.app.es_suggestions_by_request(
        #     self.request, self.query
        # ))

    def postgres_search(self):
        results = []
        print('*** tschupre postgresql_search')

        # TODO:language from application setting?

        for model in searchable_sqlalchemy_models(Base):
            if model.es_public or self.request.is_logged_in:
                print(f'*** model to search: {model}')
                query = self.request.session.query(model)
                query = query.filter(
                    model.fts_idx.op('@@')
                    (func.websearch_to_tsquery('german', self.query))
                )
                results += query.all()

        print(f'*** psql res count: {len(results)}')
        for result in results:
            print(f'*** psql res: {result}')

        return results
