from __future__ import annotations

from elasticsearch_dsl.function import SF  # type:ignore
from elasticsearch_dsl.query import FunctionScore  # type:ignore
from elasticsearch_dsl.query import Match
from elasticsearch_dsl.query import MatchPhrase
from elasticsearch_dsl.query import MultiMatch
from functools import cached_property
from libres.db.models import ORMBase
from onegov.core.collection import Pagination, _M
from onegov.core.orm import Base
from onegov.event.models import Event
from onegov.search.search_index import SearchIndex
from sedate import utcnow
from sqlalchemy import func, cast, or_, Text, case
from sqlalchemy.dialects.postgresql import UUID


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from onegov.search import Searchable
    from onegov.search.dsl import Hit, Response, Search as ESSearch


class Search(Pagination[_M]):
    results_per_page = 10
    max_query_length = 100

    def __init__(self, request: OrgRequest, query: str, page: int) -> None:
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
        def cached_subset(self) -> Response | None: ...  # type:ignore

    def subset(self) -> Response | None:  # type:ignore[override]
        return self.batch

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Search[_M]:
        return Search(self.request, self.query, index)

    @cached_property
    def batch(self) -> Response | None:  # type:ignore[override]
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
    def load_batch_results(self) -> list[Hit]:
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
        search: ESSearch,
        query: str
    ) -> ESSearch:

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

    def hashtag_search(self, search: ESSearch, query: str) -> ESSearch:
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


def locale_mapping(locale: str) -> str:
    mapping = {'de_CH': 'german', 'fr_CH': 'french', 'it_CH': 'italian',
               'rm_CH': 'english'}
    return mapping.get(locale, 'simple')


class SearchPostgres(Pagination[_M]):
    """
    Implements searching in postgres db based on the gin index
    """
    results_per_page = 10
    max_query_length = 100

    def __init__(self, request: OrgRequest, query: str, page: int):
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

    def subset(self) -> list[Searchable] | None:  # type:ignore[override]
        return self.batch

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> SearchPostgres[_M]:
        return SearchPostgres(self.request, self.query, index)

    @cached_property
    def batch(self) -> list[Searchable]:  # type:ignore[override]
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
        actual search results from the query.

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

    def filter_user_level(self, query: Any) -> Any:
        """ Filters search content according to user level """

        role = getattr(self.request.identity, 'role', 'anonymous')
        available_accesses = {
            'admin': (),  # can see everything
            'editor': (),  # can see everything
            'member': ('member', 'mtan', 'public')
        }.get(role, ('mtan', 'public'))
        if available_accesses:
            query = query.filter(or_(
                SearchIndex.public == 'true',
                SearchIndex.access.in_(available_accesses)
            ))

        return query

    @staticmethod
    def get_model_by_class_name(class_name: str) -> type[Any] | None:
        cls = Base._decl_class_registry.get(class_name)  # type: ignore[attr-defined]
        if cls is None:
            cls = ORMBase._decl_class_registry.get(class_name)  # type: ignore[attr-defined]
        return cls

    def generic_search(self) -> list[Searchable]:
        language = locale_mapping(self.request.locale or 'de_CH')
        ts_query = func.websearch_to_tsquery(
            # FIXME: I think we should use unidecode here, like we do
            #        when generating the TSVECTOR, otherwise we will run
            #        into issues where the two functions don't generate
            #        the same output
            language, func.unaccent(self.query))
        now = utcnow()
        results = []

        self.number_of_docs = self.filter_user_level(
            self.request.session.query(func.count(SearchIndex.id))
        ).scalar()

        query = self.request.session.query(
            SearchIndex,
            # FIXME: Make this the order_by, so we don't have to do the
            #        ordering in Python
            (
                func.ts_rank_cd(SearchIndex.fts_idx, ts_query, 0) *
                func.least(
                    func.greatest(
                        func.exp(-func.extract(
                            'epoch', now - SearchIndex.last_change)),
                        1e-10
                    ),
                    1.0
                ) / (30 * 24 * 3600)  # 30 days decay period
            ).label('rank')
        ).filter(SearchIndex.fts_idx.op('@@')(ts_query))
        query = self.filter_user_level(query)

        # Dynamically join with the appropriate model table based on owner_type
        subquery = query.subquery()
        # FIXME: Figure out which distinct model classes there actually are in
        #        the result set and only emit subqueries for them, we also
        #        should emit a select in, rather than a subquery join, we did
        #        the expensive query and we know all the object ids, we don't
        #        want to duplicate that work load for every model type
        for model_class in Base._decl_class_registry.values():  # type: ignore[attr-defined]
            if (hasattr(model_class, '__tablename__') and
                    hasattr(model_class, 'id')):
                model_query = (
                    self.request.session.query(
                        model_class, subquery.c.rank.label('rank'))
                    .join(
                        subquery,
                        # FIXME: Determine which column to using introspection
                        #        on the model_class, then we also don't need to
                        #        perform any casts
                        cast(model_class.id, Text) == case(
                            [
                                (
                                    subquery.c.owner_id_int.isnot(None),
                                    cast(subquery.c.owner_id_int, Text),
                                ),
                                (
                                    subquery.c.owner_id_uuid.isnot(None),
                                    cast(subquery.c.owner_id_uuid, Text),
                                ),
                                (
                                    subquery.c.owner_id_str.isnot(None),
                                    subquery.c.owner_id_str,
                                ),
                            ]
                        ),
                    )
                    .filter(subquery.c.owner_type == model_class.__name__)
                )

                results.extend(model_query)

        self.number_of_results = len(results)

        # sort and return only the model instances from the results
        results.sort(key=lambda x: x.rank, reverse=True)
        return [r[0] for r in results]

    def hashtag_search(self) -> list[Searchable]:
        results: list[Any] = []
        q = self.query.lstrip('#')

        self.number_of_docs = self.filter_user_level(
            self.request.session.query(func.count(SearchIndex.id))
        ).scalar()

        query = self.request.session.query(SearchIndex)
        query = self.filter_user_level(query)
        query = query.filter(SearchIndex._tags.has_key(q))  # type: ignore[attr-defined]

        # FIXME: refactor this result loading into a common utility function
        #        since both search function need to do this and they're
        #        currently not doing the same thing.
        for index_entry in query:
            model = self.get_model_by_class_name(index_entry.owner_type)

            if model:
                owner_id: str | int | UUID | None = None

                if index_entry.owner_id_int is not None:
                    owner_id = index_entry.owner_id_int
                elif index_entry.owner_id_uuid is not None:
                    owner_id = index_entry.owner_id_uuid
                else:
                    owner_id = index_entry.owner_id_str

                result = (self.request.session.query(model).
                          filter(model.id == owner_id).first())

                if result:
                    results.append(result)

        self.number_of_results = len(results)
        return results

    def feeling_lucky(self) -> str | None:
        # FIXME: make this actually return a random result
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

    @cached_property
    def get_all_hashtags(self) -> list[str]:
        """
        Returns all hashtags from the database in alphabetical order
        filtered by user level.

        """

        query = self.filter_user_level(
            self.request.session.query(func.skeys(SearchIndex._tags))
        ).distinct()

        # mark tags as hashtags; it also helps ot remain with the hashtag
        # search (url) when clicking on a suggestion
        return sorted({f'#{tag}' for tag, in query})

    def suggestions(self) -> tuple[str, ...]:
        suggestions = []
        number_of_suggestions = 15

        if self.query.startswith('#'):  # hashtag search
            q = self.query.lstrip('#').lower()
            tags = self.get_all_hashtags

            if len(q) == 0:
                return tuple(tags[:number_of_suggestions])

            suggestions = [tag for tag in tags if q in tag]

        else:
            # FIXME: This is really inefficient we first generate all the
            #        suggestions and then remove the ones we don't need
            #        We also may not want to rely on the generic search
            #        for this, we could try to do something using similarity
            #        search on a separate table that contains all the
            #        suggestions and return the most similar suggestions.
            for element in self.generic_search():
                # FIXME: Why are we special casing files? Too much noise?
                #        then maybe we shouldn't provide suggestions for
                #        files...
                if element.es_type_name == 'files':
                    continue
                suggest = getattr(element, 'es_suggestion', '')
                if isinstance(suggest, tuple):
                    # FIXME: Return the first suggestion that contains
                    #        our search term
                    suggest = suggest[0]
                suggestions.append(suggest)

        return tuple(suggestions[:number_of_suggestions])
