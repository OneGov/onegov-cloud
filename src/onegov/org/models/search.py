from __future__ import annotations

from elasticsearch_dsl.function import SF  # type:ignore
from elasticsearch_dsl.query import FunctionScore  # type:ignore
from elasticsearch_dsl.query import Match
from elasticsearch_dsl.query import MatchPhrase
from elasticsearch_dsl.query import MultiMatch
from functools import cached_property
from onegov.core.collection import Pagination, _M
from onegov.event.models import Event
from onegov.search.search_index import SearchIndex
from onegov.search.utils import language_from_locale
from sedate import utcnow
from sqlalchemy import func, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import escape_like
from unidecode import unidecode


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from onegov.search import Searchable
    from onegov.search.dsl import Hit, Response, Search as ESSearch
    from sqlalchemy.orm import Query


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
        actual search results from the query. """

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
        events.sort(key=get_sort_key)
        return events + non_events

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


class SearchPostgres(Pagination[_M]):
    """
    Implements searching in postgres db based on the gin index
    """
    results_per_page = 10

    def __init__(self, request: OrgRequest, query: str, page: int):
        self.request = request
        self.query = query
        self.page = page  # page index

        self.number_of_results: int | None = None

    @cached_property
    def available_documents(self) -> int:
        return self.filter_user_level(
            self.request.session.query(func.count(SearchIndex.id))
        ).scalar()

    @cached_property
    def available_results(self) -> int:
        if self.number_of_results is None:
            _ = self.batch
            assert self.number_of_results is not None
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
        if not self.query.lstrip('#'):
            self.number_of_results = 0
            return []

        if self.query.startswith('#'):
            query = self.hashtag_search()
        else:
            query = self.generic_search()

        # compute the number of results for this query
        self.number_of_results = (
            query
            # remove order for speed
            .order_by(None)
            .with_entities(func.count(SearchIndex.id))
            .scalar()
        )
        return self.load_batch(query)

    @cached_property
    def load_batch_results(self) -> list[Any]:
        """
        Load search results and sort upcoming events by occurrence start date.
        """
        batch = self.batch

        # FIXME: This is highly questionable, we probably should add a time
        #        decayed portion to the result ranking instead (we already
        #        had one, but it's too agressive compared to ElasticSearch,
        #        we should apply the same Gaussian decay we did before but
        #        make sure we only do that for records where the time portion
        #        actually is an indicator for relevancy, some documents will
        #        never or rarely change and remain eternally relevant)
        future_events: list[Event] = []
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

        future_events.sort(
            key=lambda e: e.latest_occurrence.start,  # type:ignore[union-attr]
            reverse=True
        )
        return future_events + other

    def filter_user_level(self, query: Any) -> Any:
        """ Filters search content according to user level """

        # FIXME: This doesn't handle elevated/downgaraded permissions properly
        #        yet like access to tickets by user group. We could add a new
        #        column `groupids` to the search index if a particular result
        #        should bypass regular access checks for non-admins and check
        #        if at least one of the groups match instead.
        role = getattr(self.request.identity, 'role', 'anonymous')
        available_accesses = {
            'admin': (),  # can see everything
            'editor': (),  # can see everything
            # FIXME: For mtan access to work properly we probably need to
            #        split public and private content, so you can still find
            #        an object by it's public name, but not via data that
            #        should only be visible once authenticated.
            'supporter': ('member', 'public'),  # TODO: 'mtan'
            'member': ('member', 'public')  # TODO: 'mtan'
        }.get(role, ('public',))  # TODO: 'mtan'
        if available_accesses:
            query = query.filter(SearchIndex.access.in_(available_accesses))
            query = query.filter(SearchIndex.published)

        # FIXME: We may need to redesign this a little, for starters we
        #        probably want to flip this boolean from public to private
        #        in order to make it less confusing and make sure that
        #        the boolean is only set for models we want to be affected
        #        by the outcome of this method.
        if not self.request.app.es_may_use_private_search(self.request):
            query = query.filter(SearchIndex.public)

        return query

    def generic_search(self) -> Query[SearchIndex]:
        language = language_from_locale(self.request.locale)
        ts_query = func.websearch_to_tsquery(
            language, unidecode(self.query))

        query = self.request.session.query(
            SearchIndex,
            # FIXME: Make this the order_by, so we don't have to do the
            #        ordering in Python
            (
                func.ts_rank_cd(SearchIndex.fts_idx, ts_query, 0)
                # FIXME: Wheter or not we apply a time decay should depend
                #        on the type of content, there's content that remains
                #        relevant no matter how old it is, e.g. people, but
                #        there's also content that does get less relevant
                #        with time e.g. news. For now we apply no time decay.
                # * func.least(
                #     func.greatest(
                #         # TODO: This is quite a dramatic decay, we
                #         #       may want something more gradual, so
                #         #       the ts_rank_cd still plays enough of
                #         #       a role, compared to the time factor
                #         func.exp(
                #             func.extract(
                #                 'epoch',
                #                 SearchIndex.last_change - utcnow()
                #             ) / (30 * 24 * 3600)  # 30 days decay period
                #         ),
                #         1e-6
                #     ),
                #     1.0
                # )
            ).label('rank')
        ).filter(
            SearchIndex.fts_idx.op('@@')(ts_query)
        ).order_by(
            (
                func.ts_rank_cd(SearchIndex.fts_idx, ts_query, 0)
                # FIXME: Wheter or not we apply a time decay should depend
                #        on the type of content, there's content that remains
                #        relevant no matter how old it is, e.g. people, but
                #        there's also content that does get less relevant
                #        with time e.g. news. For now we apply no time decay.
                # * func.least(
                #     func.greatest(
                #         # TODO: This is quite a dramatic decay, we
                #         #       may want something more gradual, so
                #         #       the ts_rank_cd still plays enough of
                #         #       a role, compared to the time factor
                #         func.exp(
                #             func.extract(
                #                 'epoch',
                #                 SearchIndex.last_change - utcnow()
                #             ) / (30 * 24 * 3600)  # 30 days decay period
                #         ),
                #         1e-6
                #     ),
                #     1.0
                # )
            ).desc().label('rank')
        )
        return self.filter_user_level(query)

    def hashtag_search(self) -> Query[SearchIndex]:
        tag = self.query.lstrip('#')
        query = self.request.session.query(SearchIndex)
        query = query.filter(SearchIndex._tags.has_key(tag))  # type: ignore[attr-defined]
        # TODO: Do we want to order results in some way?
        return self.filter_user_level(query)

    def load_batch(self, query: Query[SearchIndex]) -> list[Searchable]:
        batch: list[tuple[str, UUID | int | str]]
        batch = [
            (
                tablename,
                id_uuid if id_uuid is not None else (
                id_int if id_int is not None else
                id_str)
            )
            for tablename, id_uuid, id_int, id_str in query.with_entities(
                SearchIndex.owner_tablename,
                SearchIndex.owner_id_uuid,
                SearchIndex.owner_id_int,
                SearchIndex.owner_id_str
            ).offset(self.offset).limit(self.results_per_page)
        ]
        if not batch:
            return []

        table_batches: dict[str, set[UUID | int | str]] = {}
        for tablename, owner_id in batch:
            table_batches.setdefault(tablename, set()).add(owner_id)

        indexable_base_models = {
            model.__tablename__: model
            for model in self.request.app.indexable_base_models()
        }

        results_by_id: dict[UUID | int | str, Searchable] = {}
        for tablename, table_batch in table_batches.items():
            base_model = indexable_base_models.get(tablename)
            if base_model is None:
                # NOTE: We might want to log this, although this should
                #       only ever happen if the search index is out of
                #       date and contains entries for tables that have
                #       since been removed.
                continue

            primary_key, = inspect(base_model).primary_key

            results_by_id.update(
                self.request.session.query(primary_key, base_model)
                .filter(primary_key.in_(table_batch))
            )

        return [
            result
            for __, owner_id in batch
            if (result := results_by_id.get(owner_id)) is not None
        ]

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

    def all_hashtags_query(self) -> Query[tuple[str]]:
        """
        Returns all hashtags from the database in alphabetical order
        filtered by user level.

        """

        return self.filter_user_level(
            self.request.session.query(
                func.skeys(SearchIndex._tags).distinct().label('tag')
            ).order_by(func.skeys(SearchIndex._tags).asc())
        )

    def suggestions(self) -> tuple[str, ...]:
        if not self.query:
            return ()

        number_of_suggestions = 15

        if self.query.startswith('#'):  # hashtag search
            q = self.query.lstrip('#').lower()
            query = self.filter_user_level(
                self.request.session.query(
                    func.skeys(SearchIndex._tags).distinct().label('tag')
                ).order_by(func.skeys(SearchIndex._tags).asc())
            )
            if len(q) >= 0:
                subquery = query.subquery()
                query = self.request.session.query(subquery.c.tag).filter(
                    subquery.c.tag.ilike(f'{escape_like(q)}%', '*')
                )
            return tuple(
                f'#{tag}'
                for tag, in query.limit(number_of_suggestions)
            )
        else:
            subquery = self.filter_user_level(
                self.request.session.query(
                    func.unnest(
                        SearchIndex.suggestion
                    ).distinct().label('suggestion')
                )
            ).subquery()
            # FIXME: This could be a lot faster if suggestions were
            #        their own table, we also don't handle normalization
            #        of accents/umlauts yet for auto-complete
            return tuple(
                suggestion
                for suggestion, in self.request.session
                .query(subquery.c.suggestion)
                .filter(subquery.c.suggestion.ilike(
                    f'{escape_like(self.query)}%',
                    '*'
                ))
                .order_by(subquery.c.suggestion.asc())
                .limit(number_of_suggestions)
            )
