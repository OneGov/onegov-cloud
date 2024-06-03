from operator import attrgetter

from elasticsearch_dsl.function import SF
from elasticsearch_dsl.query import FunctionScore
from elasticsearch_dsl.query import Match
from elasticsearch_dsl.query import MatchPhrase
from elasticsearch_dsl.query import MultiMatch
from functools import cached_property

from sqlalchemy import func

from onegov.core.collection import Pagination, _M
from onegov.core.orm import Base
from onegov.event.models import Event


from typing import TYPE_CHECKING

from onegov.search.utils import searchable_sqlalchemy_models

if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from onegov.search.dsl import Hit, Response, Search as ESSearch


class Search(Pagination[_M]):

    results_per_page = 10
    max_query_length = 100

    def __init__(self, request: 'OrgRequest', query: str, page: int) -> None:
        super().__init__(page)
        self.request = request
        self.query = query

    @cached_property
    def available_documents(self) -> int:
        search = self.request.app.es_search_by_request(self.request)
        return search.count()

    @cached_property
    def explain(self) -> bool:
        return self.request.is_manager and 'explain' in self.request.params

    @property
    def q(self) -> str:
        return self.query

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
            and self.query == other.query
        )

    if TYPE_CHECKING:
        @property
        def cached_subset(self) -> 'Response | None': ...  # type:ignore

    def subset(self) -> 'Response | None':  # type:ignore[override]
        return self.batch

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> 'Search[_M]':
        return Search(self.request, self.query, index)

    @cached_property
    def batch(self) -> 'Response | None':  # type:ignore[override]
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
    def load_batch_results(self) -> list['Hit']:
        """Load search results and sort events by latest occurrence.

        This methods is a wrapper around `batch.load()`, which returns the
        actual search results form the query. """

        def get_sort_key(event: Event) -> float:
            if event.latest_occurrence:
                return event.latest_occurrence.start.timestamp()
            return float('-inf')

        assert self.batch is not None
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
        sorted_events = sorted(
            events,
            key=get_sort_key
        )
        return sorted_events + non_events

    def generic_search(
        self,
        search: 'ESSearch',
        query: str
    ) -> 'ESSearch':

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

    def hashtag_search(self, search: 'ESSearch', query: str) -> 'ESSearch':
        return search.query(Match(es_tags=query.lstrip('#')))

    def feeling_lucky(self) -> str | None:
        if self.batch:
            first_entry = self.batch[0].load()

            # XXX the default view to the event should be doing the redirect
            if first_entry.__tablename__ == 'events':
                return self.request.link(first_entry, 'latest')
            else:
                return self.request.link(first_entry)
        return None

    @cached_property
    def subset_count(self) -> int:
        return self.cached_subset and self.cached_subset.hits.total.value or 0

    def suggestions(self) -> tuple[str, ...]:
        return tuple(self.request.app.es_suggestions_by_request(
            self.request, self.query
        ))


def locale_mapping(locale):
    mapping = {'de_CH': 'german', 'fr_CH': 'french', 'it_CH': 'italian',
               'rm_CH': 'english'}
    return mapping.get(locale, 'english')


class SearchPostgres(Pagination):
    """
    Implements searching in postgres db based on the gin index
    """
    results_per_page = 10
    max_query_length = 100

    def __init__(self, request, query, page):
        self.request = request
        self.query = query
        self.page = page  # page index

        self.nbr_of_docs = 0
        self.nbr_of_results = 0

    @cached_property
    def available_documents(self):
        if not self.nbr_of_docs:
            self.load_batch_results
        return self.nbr_of_docs

    @cached_property
    def available_results(self):
        if not self.nbr_of_results:
            self.load_batch_results
        return self.nbr_of_results

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
        return SearchPostgres(self.request, self.query, index)

    @cached_property
    def batch(self):
        if not self.query:
            return None

        if self.query.startswith('#'):
            results = self.hashtag_search()
        else:
            results = self.generic_search()

        return results[self.offset:self.offset + self.batch_size]

    @cached_property
    def load_batch_results(self):
        """Load search results and sort events by latest occurrence.
        This methods is a wrapper around `batch.load()`, which returns the
        actual search results form the query. """

        batch = self.batch
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

    def generic_search(self):
        doc_count = 0
        results = []

        language = locale_mapping(self.request.locale)
        for model in searchable_sqlalchemy_models(Base):
            if model.es_public or self.request.is_logged_in:
                query = self.request.session.query(model)
                doc_count += query.count()
                query = query.filter(
                    model.fts_idx.op('@@')(func.websearch_to_tsquery(
                        language, self.query))
                )
                query = query.order_by(func.ts_rank_cd(
                    model.fts_idx, func.websearch_to_tsquery(language,
                                                             self.query)))
                results.extend(query.all())

        self.nbr_of_docs = doc_count
        self.nbr_of_results = len(results)
        results.sort(key=attrgetter('search_score'), reverse=False)
        return results

    def hashtag_search(self):
        q = self.query.lstrip('#')
        results = []

        for model in searchable_sqlalchemy_models(Base):
            # skip certain tables for hashtag search for better performance
            if model.__tablename__ not in ['attendees', 'files', 'people',
                                           'tickets', 'users']:
                if model.es_public or self.request.is_logged_in:
                    for doc in self.request.session.query(model).all():
                        if doc.es_tags and q in doc.es_tags:
                            results.append(doc)

        self.nbr_of_results = len(results)
        results.sort(key=attrgetter('search_score'), reverse=False)
        return results

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
        return self.available_results

    def suggestions(self):
        suggestions = list()

        for element in self.generic_search():
            suggest = getattr(element, 'es_suggestion', [])
            suggestions.append(suggest)

        return tuple(suggestions[:15])
