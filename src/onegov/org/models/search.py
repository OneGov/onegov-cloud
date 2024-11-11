from elasticsearch_dsl.function import SF  # type:ignore
from elasticsearch_dsl.query import FunctionScore  # type:ignore
from elasticsearch_dsl.query import Match
from elasticsearch_dsl.query import MatchPhrase
from elasticsearch_dsl.query import MultiMatch
from functools import cached_property
from sedate import utcnow
from sqlalchemy import func
from typing import TYPE_CHECKING, Any

from onegov.core.collection import Pagination, _M
from onegov.core.orm import Base
from onegov.event.models import Event
from onegov.search.utils import searchable_sqlalchemy_models

if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from onegov.search import Searchable
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
        future_events = []
        others = []

        for search_result in batch:
            if isinstance(search_result, Event):
                future_events.append(search_result)
            else:
                others.append(search_result)

        if not future_events:
            return batch

        sorted_events = sorted(
            future_events,
            key=get_sort_key
        )
        return sorted_events + others

    def generic_search(
        self,
        search: 'ESSearch',
        query: str
    ) -> 'ESSearch':

        # make sure the title matches with a higher priority, otherwise the
        # "get lucky" functionality is not so lucky after all
        match_title = MatchPhrase(title={'query': query, 'boost': 3})

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
            if first_entry.es_type_name == 'events':
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


def locale_mapping(locale: str) -> str:
    mapping = {'de_CH': 'german', 'fr_CH': 'french', 'it_CH': 'italian',
               'rm_CH': 'english'}
    return mapping.get(locale, 'english')


class SearchPostgres(Pagination[_M]):
    """
    Implements searching in postgres db based on the gin index
    """
    results_per_page = 10
    max_query_length = 100

    def __init__(self, request: 'OrgRequest', query: str, page: int):
        self.request = request
        self.query = query
        self.page = page  # page index

        self.number_of_docs = 0
        self.number_of_results = 0

    @cached_property
    def available_documents(self) -> int:
        if not self.number_of_docs:
            _ = self.load_batch_results
        return self.number_of_docs

    @cached_property
    def available_results(self) -> int:
        if not self.number_of_results:
            _ = self.load_batch_results
        return self.number_of_results

    @property
    def q(self) -> str:
        """
        Returns the user's query term from the search field of the UI

        """
        return self.query

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SearchPostgres):
            return NotImplemented
        return self.page == other.page and self.query == other.query

    def subset(self) -> 'list[Searchable] | None':  # type:ignore[override]
        return self.batch

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> 'SearchPostgres[_M]':
        return SearchPostgres(self.request, self.query, index)

    @cached_property
    def batch(self) -> 'list[Searchable]':  # type:ignore[override]
        if not self.query:
            return []

        if self.query.startswith('#'):
            results = self.hashtag_search()
        else:
            results = self.generic_search()

        return results[self.offset:self.offset + self.batch_size]

    @cached_property
    def load_batch_results(self) -> list[Any]:
        """
        Load search results and sort upcoming events by occurrence start date.
        This methods is a wrapper around `batch.load()`, which returns the
        actual search results form the query.

        """
        batch: list[Searchable] = self.batch
        future_events: list[Searchable] = []
        other: list[Searchable] = []

        for search_result in batch:
            if (isinstance(search_result, Event)
                    and search_result.latest_occurrence
                    and search_result.latest_occurrence.start > utcnow()):
                future_events.append(search_result)
            else:
                other.append(search_result)

        if not future_events:
            return batch

        sorted_events = sorted(
            future_events, key=lambda e:
            e.latest_occurrence.start,  # type:ignore[attr-defined]
            reverse=True)

        return sorted_events + other

    def _create_weighted_vector(
        self,
        model: Any,
        language: str = 'simple'
    ) -> Any:
        # for now weight the first field with 'A', the rest with 'B'
        weighted_vectors = [
            func.setweight(
                func.to_tsvector(
                    language,
                    getattr(model.fts_idx_data, field, '')),
                weight
            )
            for field, weight in zip(model.es_properties.keys(), 'ABBBBBBBBBB')
            if not field.startswith('es_')  # TODO: rename to fts_
        ]

        # combine all weighted vectors
        if weighted_vectors:
            combined_vector = weighted_vectors[0]
            for vector in weighted_vectors[1:]:
                combined_vector = combined_vector.op('||')(vector)
        else:
            combined_vector = func.to_tsvector(language, '')

        return combined_vector

    def generic_search(self) -> list['Searchable']:
        doc_count = 0
        results: list[Any] = []
        language = locale_mapping(self.request.locale or 'de_CH')
        ts_query = func.websearch_to_tsquery(language,
                                             func.unaccent(self.query))
        session = self.request.session

        for base in self.request.app.session_manager.bases:
            for model in searchable_sqlalchemy_models(base):
                query = session.query(model)

                if not self.request.is_logged_in:
                    query = query.filter(
                        model.fts_idx_data['es_public'].astext == 'True')

                # as a member we only want to see public and member content
                if self.request.is_member and hasattr(model, 'meta'):
                    query = query.filter(
                        model.meta['access'].astext.in_(('public', 'member')))

                # as non-manager we only want to see public content
                elif not self.request.is_manager:
                    query = query.filter(
                        model.fts_idx_data['es_public'].astext == 'True')

                if session.query(query.exists()).scalar():
                    weighted = (
                        self._create_weighted_vector(model, language))
                    rank_expression = func.coalesce(
                        func.ts_rank(
                            weighted,
                            ts_query,
                            0  # normalization, ignore document length
                        ), 0).label('rank')
                    query = (query.filter(model.fts_idx.op('@@')(ts_query))
                             .add_columns(rank_expression))
                    res = list(query.all())
                    doc_count += len(res)
                    results.extend(res)

        # remove duplicates, sort by rank
        results = list(set(results))
        results.sort(key=lambda x: x[1], reverse=True)

        self.number_of_docs = doc_count
        self.number_of_results = len(results)

        # remove rank column from results and return
        return [r[0] for r in results]

    def hashtag_search(self) -> list['Searchable']:
        q = self.query.lstrip('#')

        # Skip certain tables for hashtag search for better performance
        results = [
            doc for model in searchable_sqlalchemy_models(Base)
            if model.es_type_name not in
               ['attendees', 'files', 'people', 'tickets', 'users']
            if model.es_public or self.request.is_logged_in  # type:ignore
            for doc in self.request.session.query(model).all()
            if doc.es_tags and q in doc.es_tags
        ]

        # remove duplicates
        results = list(set(results))

        self.number_of_results = len(results)
        return results

    def feeling_lucky(self) -> str | None:
        if self.batch:
            first_entry = self.batch[0]

            # XXX the default view to the event should be doing the redirect
            if isinstance(first_entry, Event):
                return self.request.link(first_entry, 'latest')
            else:
                return self.request.link(first_entry)
        return None

    @cached_property
    def subset_count(self) -> int:
        return self.available_results

    def suggestions(self) -> tuple[str, ...]:
        suggestions = []

        for element in self.generic_search():
            if element.es_type_name == 'files':
                continue
            suggest = getattr(element, 'es_suggestion', '')
            if isinstance(suggest, tuple):
                suggest = suggest[0]
            suggestions.append(suggest)

        return tuple(suggestions[:15])
